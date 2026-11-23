from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from engine.config_loader import load_toolkit_configs
from engine.graph.call_graph import CallGraph
from engine.graph.dependency_graph import DependencyGraph, GraphEdge, GraphNode
from engine.graph.import_graph import ImportGraph
from engine.graph.symbol_index import SymbolIndex, symbol_id
from engine.parsers.parser_registry import ParseResult, ParserRegistry
from engine.repository.file_classifier import FileClassifier
from engine.repository.scanner import RepositoryScan, RepositoryScanner


class GraphBuilder:
    """Orchestrates parsing and builds the unified DependencyGraph for a repository."""

    def __init__(
        self,
        configs: dict[str, dict[str, Any]] | None = None,
        registry: ParserRegistry | None = None,
    ) -> None:
        self.configs = configs if configs is not None else load_toolkit_configs()
        self.registry = registry if registry is not None else ParserRegistry()

    def build_from_path(self, root: str | Path) -> tuple[DependencyGraph, RepositoryScan]:
        classifier = FileClassifier(
            self.configs.get("languages", {}),
            self.configs.get("exclusions", {}),
        )
        scanner = RepositoryScanner(classifier)
        scan = scanner.scan(root)
        graph = self.build_from_scan(scan)
        return graph, scan

    def build_from_scan(self, scan: RepositoryScan) -> DependencyGraph:
        graph = DependencyGraph(root=scan.root)
        analyzable = [f for f in scan.files if f.get("status") == "analyze"]
        known_files = [f["path"] for f in scan.files]
        file_categories = {f["path"]: list(f.get("categories", [])) for f in scan.files}

        parse_results: list[ParseResult] = []
        for entry in analyzable:
            rel_path = entry["path"]
            lang = entry.get("language")
            cats = file_categories.get(rel_path, [])
            is_test = "test" in cats

            graph.add_node(
                GraphNode(
                    id=f"file:{rel_path}",
                    kind="test" if is_test else "file",
                    label=rel_path,
                    file_path=rel_path,
                    metadata={"language": lang, "categories": cats},
                )
            )

            res = self.registry.parse_file(scan.root, rel_path, lang)
            parse_results.append(res)

            for sig in res.dynamic_signals:
                graph.dynamic_signals.append(asdict(sig))
            if res.limitations or res.errors:
                graph.parse_limitations.append(
                    {
                        "file_path": rel_path,
                        "parser": res.parser_name,
                        "errors": res.errors,
                        "limitations": res.limitations,
                    }
                )

        # 1. Index all symbols and add symbol + DEFINES + INHERITS edges
        symbol_index = SymbolIndex()
        symbol_index.add_parse_results(parse_results)

        for entry in symbol_index.all_symbols():
            sym = entry.info
            cats = file_categories.get(sym.file_path, [])
            graph.add_node(
                GraphNode(
                    id=entry.id,
                    kind=sym.kind,
                    label=sym.qualified_name,
                    file_path=sym.file_path,
                    metadata={
                        "start_line": sym.start_line,
                        "end_line": sym.end_line,
                        "parameters": sym.parameters,
                        "decorators": sym.decorators,
                        "categories": cats,
                    },
                )
            )
            graph.add_edge(
                GraphEdge(
                    source=f"file:{sym.file_path}",
                    target=entry.id,
                    relation="DEFINES",
                    provenance="static_ast" if sym.file_path.endswith(".py") else "static_structural",
                )
            )
            for base_name in sym.bases:
                base_tail = base_name.split(".")[-1]
                base_matches = symbol_index.find_by_name(base_tail)
                if len(base_matches) == 1:
                    graph.add_edge(
                        GraphEdge(
                            source=entry.id,
                            target=base_matches[0].id,
                            relation="INHERITS",
                            provenance="static_ast" if sym.file_path.endswith(".py") else "static_structural",
                        )
                    )

        # 2. Build ImportGraph
        import_graph = ImportGraph(known_files)
        resolved_imports = import_graph.build(parse_results)
        for imp in resolved_imports:
            source_id = f"file:{imp.source_file}"
            is_test_source = "test" in file_categories.get(imp.source_file, [])
            if imp.target_file:
                target_id = f"file:{imp.target_file}"
                if target_id not in graph.nodes:
                    graph.add_node(
                        GraphNode(
                            id=target_id,
                            kind="file",
                            label=imp.target_file,
                            file_path=imp.target_file,
                        )
                    )
                graph.add_edge(
                    GraphEdge(
                        source=source_id,
                        target=target_id,
                        relation="TESTS" if is_test_source else "IMPORTS",
                        provenance=imp.provenance,
                        metadata={"module": imp.module, "line": imp.line},
                    )
                )
                if is_test_source:
                    graph.add_edge(
                        GraphEdge(
                            source=source_id,
                            target=target_id,
                            relation="IMPORTS",
                            provenance=imp.provenance,
                            metadata={"module": imp.module, "line": imp.line},
                        )
                    )
            else:
                ext_id = f"external:{imp.module}"
                if ext_id not in graph.nodes:
                    graph.add_node(
                        GraphNode(
                            id=ext_id,
                            kind="external",
                            label=imp.module,
                        )
                    )
                graph.add_edge(
                    GraphEdge(
                        source=source_id,
                        target=ext_id,
                        relation="IMPORTS",
                        provenance=imp.provenance,
                        metadata={"line": imp.line, "external": True},
                    )
                )

        # 3. Build CallGraph
        call_graph = CallGraph(symbol_index, import_graph)
        resolved_calls = call_graph.build(parse_results)
        for call in resolved_calls:
            if not call.callee_id:
                continue
            if call.caller_id in graph.nodes and call.callee_id in graph.nodes:
                graph.add_edge(
                    GraphEdge(
                        source=call.caller_id,
                        target=call.callee_id,
                        relation="CALLS",
                        provenance=call.provenance,
                        metadata={"line": call.line, "raw_callee": call.raw_callee},
                    )
                )

        # 4. Add Route nodes and ROUTES_TO edges
        for res in parse_results:
            for route in res.routes:
                route_id = f"route:{route.method} {route.path}"
                graph.add_node(
                    GraphNode(
                        id=route_id,
                        kind="route",
                        label=f"{route.method} {route.path}",
                        file_path=route.file_path,
                        metadata={"method": route.method, "path": route.path, "line": route.line},
                    )
                )
                handler_sym = symbol_index.resolve_in_file(route.file_path, route.handler)
                if not handler_sym:
                    matches = symbol_index.find_by_name(route.handler.split(".")[-1])
                    handler_sym = matches[0] if len(matches) == 1 else None
                target_id = handler_sym.id if handler_sym else f"file:{route.file_path}"
                graph.add_edge(
                    GraphEdge(
                        source=route_id,
                        target=target_id,
                        relation="ROUTES_TO",
                        provenance=res.provenance,
                        metadata={"handler": route.handler, "line": route.line},
                    )
                )

        return graph
