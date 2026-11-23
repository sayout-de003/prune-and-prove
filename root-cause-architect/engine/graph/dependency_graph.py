from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class GraphNode:
    id: str
    kind: str  # "file", "function", "method", "class", "interface", "type", "route", "test", "external"
    label: str
    file_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str  # "IMPORTS", "CALLS", "INHERITS", "ROUTES_TO", "TESTS", "DEFINES", "DEPENDS_ON"
    provenance: str  # "static_ast" | "static_structural" | "static_heuristic"
    metadata: dict[str, Any] = field(default_factory=dict)


class DependencyGraph:
    """
    Unified Architecture Knowledge Graph supporting cross-file dependency,
    call, route, inheritance, test coverage, and blast-radius queries.
    Uses stdlib adjacency indexes (zero external dependencies).
    """

    def __init__(self, root: str) -> None:
        self.root = root
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self._out: dict[str, list[GraphEdge]] = {}
        self._in: dict[str, list[GraphEdge]] = {}
        self._edge_keys: set[tuple[str, str, str]] = set()
        self.dynamic_signals: list[dict[str, Any]] = []
        self.parse_limitations: list[dict[str, Any]] = []

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        key = (edge.source, edge.target, edge.relation)
        if key in self._edge_keys:
            return
        self._edge_keys.add(key)
        self.edges.append(edge)
        self._out.setdefault(edge.source, []).append(edge)
        self._in.setdefault(edge.target, []).append(edge)

    def outgoing(self, node_id: str, relations: set[str] | None = None) -> list[GraphEdge]:
        edges = self._out.get(node_id, [])
        if relations is None:
            return list(edges)
        return [e for e in edges if e.relation in relations]

    def incoming(self, node_id: str, relations: set[str] | None = None) -> list[GraphEdge]:
        edges = self._in.get(node_id, [])
        if relations is None:
            return list(edges)
        return [e for e in edges if e.relation in relations]

    def resolve_target(self, query: str) -> list[str]:
        """Resolve a file path, node ID, or symbol name to matching graph node IDs."""
        if query in self.nodes:
            return [query]
        file_node_id = f"file:{query}"
        if file_node_id in self.nodes:
            return [file_node_id]

        matches: list[str] = []
        for nid, node in self.nodes.items():
            if node.label == query or nid.endswith(f"::{query}") or node.file_path == query:
                if node.kind == "file" and node.file_path == query:
                    return [nid]
                matches.append(nid)
        return sorted(matches)

    def callers_of(self, node_id: str) -> list[GraphEdge]:
        return self.incoming(node_id, {"CALLS", "ROUTES_TO"})

    def callees_of(self, node_id: str) -> list[GraphEdge]:
        return self.outgoing(node_id, {"CALLS"})

    def importers_of(self, file_node_id: str) -> list[GraphEdge]:
        return self.incoming(file_node_id, {"IMPORTS"})

    def imports_of(self, file_node_id: str) -> list[GraphEdge]:
        return self.outgoing(file_node_id, {"IMPORTS"})

    def blast_radius(self, query: str, max_depth: int = 3) -> dict[str, Any]:
        """Compute upstream dependents, downstream dependencies, covering tests, and dynamic warnings."""
        seeds = self.resolve_target(query)
        if not seeds:
            return {
                "query": query,
                "matched_nodes": [],
                "upstream_dependents": [],
                "downstream_dependencies": [],
                "covering_tests": [],
                "dynamic_warnings": [],
            }

        # Include symbols defined inside matched file nodes as part of the seed set
        expanded_seeds = set(seeds)
        for sid in list(seeds):
            for edge in self.outgoing(sid, {"DEFINES"}):
                expanded_seeds.add(edge.target)

        upstream: dict[str, int] = {}
        q: deque[tuple[str, int]] = deque((s, 0) for s in expanded_seeds)
        visited_up = set(expanded_seeds)
        while q:
            curr, depth = q.popleft()
            if depth >= max_depth:
                continue
            for edge in self.incoming(curr, {"IMPORTS", "CALLS", "INHERITS", "ROUTES_TO", "TESTS"}):
                if edge.source not in visited_up:
                    visited_up.add(edge.source)
                    upstream[edge.source] = depth + 1
                    q.append((edge.source, depth + 1))

        downstream: dict[str, int] = {}
        q = deque((s, 0) for s in expanded_seeds)
        visited_down = set(expanded_seeds)
        while q:
            curr, depth = q.popleft()
            if depth >= max_depth:
                continue
            for edge in self.outgoing(curr, {"IMPORTS", "CALLS", "INHERITS"}):
                if edge.target not in visited_down:
                    visited_down.add(edge.target)
                    downstream[edge.target] = depth + 1
                    q.append((edge.target, depth + 1))

        affected_files = {
            self.nodes[nid].file_path
            for nid in (expanded_seeds | set(upstream.keys()))
            if nid in self.nodes and self.nodes[nid].file_path
        }

        covering_tests = sorted(
            {
                self.nodes[nid].file_path or nid
                for nid in upstream
                if nid in self.nodes
                and (
                    self.nodes[nid].kind == "test"
                    or "test" in self.nodes[nid].metadata.get("categories", [])
                )
            }
        )

        dynamic_warnings = [
            sig for sig in self.dynamic_signals if sig.get("file_path") in affected_files
        ]

        return {
            "query": query,
            "matched_nodes": sorted(seeds),
            "upstream_dependents": [
                {
                    "id": nid,
                    "kind": self.nodes[nid].kind,
                    "file_path": self.nodes[nid].file_path,
                    "depth": depth,
                }
                for nid, depth in sorted(upstream.items(), key=lambda kv: (kv[1], kv[0]))
                if nid in self.nodes
            ],
            "downstream_dependencies": [
                {
                    "id": nid,
                    "kind": self.nodes[nid].kind,
                    "file_path": self.nodes[nid].file_path,
                    "depth": depth,
                }
                for nid, depth in sorted(downstream.items(), key=lambda kv: (kv[1], kv[0]))
                if nid in self.nodes
            ],
            "covering_tests": covering_tests,
            "dynamic_warnings": dynamic_warnings,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "stats": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "dynamic_signal_count": len(self.dynamic_signals),
            },
            "nodes": [asdict(n) for n in sorted(self.nodes.values(), key=lambda n: n.id)],
            "edges": [
                asdict(e)
                for e in sorted(self.edges, key=lambda e: (e.source, e.relation, e.target))
            ],
            "dynamic_signals": self.dynamic_signals,
            "parse_limitations": self.parse_limitations,
        }
