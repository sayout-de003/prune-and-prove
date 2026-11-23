from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from engine.graph.import_graph import ImportGraph
from engine.graph.symbol_index import SymbolIndex, symbol_id
from engine.parsers.parser_registry import ParseResult


@dataclass(frozen=True)
class ResolvedCall:
    caller_id: str
    callee_id: str | None
    raw_callee: str
    file_path: str
    line: int
    provenance: str  # "static_ast" | "static_structural" | "static_heuristic" | "unresolved"


class CallGraph:
    """
    Resolves call sites to indexed symbols with explicit provenance.
    Never upgrades an inferred static edge to a runtime-verified call.
    """

    def __init__(self, symbol_index: SymbolIndex, import_graph: ImportGraph) -> None:
        self.symbol_index = symbol_index
        self.import_graph = import_graph
        self.edges: list[ResolvedCall] = []

    def build(self, results: Iterable[ParseResult]) -> list[ResolvedCall]:
        for res in results:
            imported_files = [
                imp.target_file
                for imp in self.import_graph.imports_of(res.file_path)
                if imp.target_file
            ]
            for call in res.calls:
                caller_id = (
                    f"file:{res.file_path}"
                    if call.caller == "<module>"
                    else symbol_id(res.file_path, call.caller)
                )
                callee_id, provenance = self._resolve_callee(
                    res.file_path,
                    call.caller,
                    call.callee,
                    imported_files,
                    call.provenance,
                )
                self.edges.append(
                    ResolvedCall(
                        caller_id=caller_id,
                        callee_id=callee_id,
                        raw_callee=call.callee,
                        file_path=res.file_path,
                        line=call.line,
                        provenance=provenance,
                    )
                )
        return self.edges

    def _resolve_callee(
        self,
        file_path: str,
        caller: str,
        raw_callee: str,
        imported_files: list[str],
        base_provenance: str,
    ) -> tuple[str | None, str]:
        # 1. self.method() inside a class method
        if raw_callee.startswith(("self.", "cls.", "this.")) and "." in caller:
            class_name = caller.split(".")[0]
            method_name = raw_callee.split(".", 1)[1]
            candidate = self.symbol_index.get(symbol_id(file_path, f"{class_name}.{method_name}"))
            if candidate:
                return candidate.id, base_provenance

        # 2. Same-file symbol (exact qualified name or short name)
        local = self.symbol_index.resolve_in_file(file_path, raw_callee)
        if local:
            return local.id, base_provenance

        tail = raw_callee.split(".")[-1]

        # 3. Symbol defined in directly imported repository files
        for imp_file in imported_files:
            found = self.symbol_index.resolve_in_file(imp_file, raw_callee) or self.symbol_index.resolve_in_file(
                imp_file, tail
            )
            if found:
                return found.id, base_provenance

        # 4. Unique repo-wide symbol match (marked as static_heuristic)
        matches = self.symbol_index.find_by_name(tail)
        if len(matches) == 1:
            return matches[0].id, "static_heuristic"

        return None, "unresolved"
