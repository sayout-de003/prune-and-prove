from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from engine.graph.dependency_graph import DependencyGraph


VALID_PROVENANCES = {"static_ast", "static_structural", "static_heuristic", "runtime_observed"}


@dataclass
class GraphValidationReport:
    valid: bool
    node_count: int
    edge_count: int
    dangling_edges: list[dict[str, str]] = field(default_factory=list)
    invalid_provenance_edges: list[dict[str, str]] = field(default_factory=list)
    import_cycles: list[list[str]] = field(default_factory=list)
    provenance_counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GraphValidator:
    """Validates DependencyGraph integrity, edge provenance, and detects module import cycles."""

    def validate(self, graph: DependencyGraph) -> GraphValidationReport:
        dangling: list[dict[str, str]] = []
        invalid_prov: list[dict[str, str]] = []
        prov_counts: dict[str, int] = {}

        for edge in graph.edges:
            if edge.source not in graph.nodes or edge.target not in graph.nodes:
                dangling.append(
                    {
                        "source": edge.source,
                        "target": edge.target,
                        "relation": edge.relation,
                    }
                )
            if edge.provenance not in VALID_PROVENANCES:
                invalid_prov.append(
                    {
                        "source": edge.source,
                        "target": edge.target,
                        "provenance": edge.provenance,
                    }
                )
            prov_counts[edge.provenance] = prov_counts.get(edge.provenance, 0) + 1

        cycles = self._find_import_cycles(graph)

        return GraphValidationReport(
            valid=(len(dangling) == 0 and len(invalid_prov) == 0),
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
            dangling_edges=dangling,
            invalid_provenance_edges=invalid_prov,
            import_cycles=cycles,
            provenance_counts=prov_counts,
        )

    @staticmethod
    def _find_import_cycles(graph: DependencyGraph) -> list[list[str]]:
        adj: dict[str, list[str]] = {}
        for edge in graph.edges:
            if edge.relation == "IMPORTS" and edge.target.startswith("file:"):
                adj.setdefault(edge.source, []).append(edge.target)

        state: dict[str, int] = {}  # 0=unvisited, 1=visiting, 2=done
        stack: list[str] = []
        cycles: list[list[str]] = []
        seen_cycles: set[tuple[str, ...]] = set()

        def dfs(node: str) -> None:
            state[node] = 1
            stack.append(node)
            for nxt in sorted(adj.get(node, [])):
                st = state.get(nxt, 0)
                if st == 1:
                    idx = stack.index(nxt)
                    cycle = stack[idx:]
                    canon = tuple(sorted(cycle))
                    if canon not in seen_cycles:
                        seen_cycles.add(canon)
                        cycles.append([n.removeprefix("file:") for n in cycle])
                elif st == 0:
                    dfs(nxt)
            stack.pop()
            state[node] = 2

        for node in sorted(adj.keys()):
            if state.get(node, 0) == 0:
                dfs(node)

        return cycles
