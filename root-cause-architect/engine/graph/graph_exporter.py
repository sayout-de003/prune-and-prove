from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from engine.graph.dependency_graph import DependencyGraph
from engine.graph.html_3d_exporter import Interactive3DExporter


_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9_]")


def _mermaid_id(node_id: str) -> str:
    return "n_" + _SAFE_ID_RE.sub("_", node_id)


def _mermaid_label(text: str) -> str:
    return text.replace('"', "'")


class GraphExporter:
    """Exports DependencyGraph to JSON, Mermaid diagrams, and Markdown impact reports."""

    @staticmethod
    def to_json(graph: DependencyGraph, indent: int = 2) -> str:
        return json.dumps(graph.to_dict(), indent=indent, sort_keys=False) + "\n"

    @staticmethod
    def write_json(graph: DependencyGraph, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(GraphExporter.to_json(graph), encoding="utf-8")
        return path

    @staticmethod
    def to_interactive_3d_html(
        graph: DependencyGraph,
        validation: dict[str, Any] | None = None,
        include_external: bool = False,
        pipeline_depth: int = 8,
    ) -> str:
        return Interactive3DExporter.render(
            graph,
            validation=validation,
            include_external=include_external,
            pipeline_depth=pipeline_depth,
        )

    @staticmethod
    def write_interactive_3d_html(
        graph: DependencyGraph,
        output_path: str | Path,
        validation: dict[str, Any] | None = None,
        include_external: bool = False,
        pipeline_depth: int = 8,
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            GraphExporter.to_interactive_3d_html(
                graph,
                validation=validation,
                include_external=include_external,
                pipeline_depth=pipeline_depth,
            ),
            encoding="utf-8",
        )
        return path

    @staticmethod
    def to_mermaid(
        graph: DependencyGraph,
        include_external: bool = False,
        relations: set[str] | None = None,
        max_edges: int = 120,
    ) -> str:
        allowed_relations = relations or {"IMPORTS", "ROUTES_TO", "TESTS"}
        lines = ["flowchart LR"]
        declared: set[str] = set()
        emitted_edges = 0

        for edge in sorted(graph.edges, key=lambda e: (e.source, e.relation, e.target)):
            if edge.relation not in allowed_relations:
                continue
            src = graph.nodes.get(edge.source)
            tgt = graph.nodes.get(edge.target)
            if not src or not tgt:
                continue
            if not include_external and (src.kind == "external" or tgt.kind == "external"):
                continue

            for node in (src, tgt):
                if node.id not in declared:
                    declared.add(node.id)
                    mid = _mermaid_id(node.id)
                    lbl = _mermaid_label(node.label)
                    lines.append(f'    {mid}["{lbl}"]')

            lines.append(
                f"    {_mermaid_id(src.id)} -->|{edge.relation}| {_mermaid_id(tgt.id)}"
            )
            emitted_edges += 1
            if emitted_edges >= max_edges:
                lines.append(f"    %% Truncated at {max_edges} edges")
                break

        return "\n".join(lines) + "\n"

    @staticmethod
    def format_impact_markdown(impact: dict[str, Any]) -> str:
        lines = [
            f"# Blast-Radius Impact — `{impact['query']}`",
            "",
            f"- **Matched nodes:** {len(impact['matched_nodes'])}",
            f"- **Upstream dependents:** {len(impact['upstream_dependents'])}",
            f"- **Downstream dependencies:** {len(impact['downstream_dependencies'])}",
            f"- **Covering tests:** {len(impact['covering_tests'])}",
            f"- **Dynamic registration warnings:** {len(impact['dynamic_warnings'])}",
            "",
            "## Upstream Dependents (Affected if Target Changes)",
            "",
        ]
        if impact["upstream_dependents"]:
            for item in impact["upstream_dependents"]:
                lines.append(f"- [depth {item['depth']}] `{item['id']}` ({item['kind']})")
        else:
            lines.append("- None detected statically")

        lines.extend(["", "## Downstream Dependencies", ""])
        if impact["downstream_dependencies"]:
            for item in impact["downstream_dependencies"]:
                lines.append(f"- [depth {item['depth']}] `{item['id']}` ({item['kind']})")
        else:
            lines.append("- None detected statically")

        lines.extend(["", "## Covering Tests", ""])
        if impact["covering_tests"]:
            for test_path in impact["covering_tests"]:
                lines.append(f"- `{test_path}`")
        else:
            lines.append("- None detected statically (verify manually before editing)")

        if impact["dynamic_warnings"]:
            lines.extend(["", "## Dynamic Registration / Reflection Warnings", ""])
            for warn in impact["dynamic_warnings"]:
                lines.append(
                    f"- `{warn['file_path']}:{warn['line']}` ({warn['kind']}): {warn['detail']}"
                )

        return "\n".join(lines) + "\n"
