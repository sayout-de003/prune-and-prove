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

    def trace_pipeline(self, start_query: str, max_depth: int = 8) -> dict[str, Any]:
        """Trace an ordered step-by-step execution pipeline from a route, function, or file."""
        seeds = self.resolve_target(start_query)
        if not seeds:
            return {
                "id": start_query,
                "label": start_query,
                "kind": "unknown",
                "file_path": None,
                "total_steps": 0,
                "total_nodes": 0,
                "total_edges": 0,
                "steps": [],
            }

        primary = seeds[0]
        primary_node = self.nodes[primary]

        # If starting from a file node, seed Step 0 with its defined callables that have outgoing calls
        frontier: list[str] = []
        if primary_node.kind in {"file", "test"}:
            defined = [
                e.target
                for e in self.outgoing(primary, {"DEFINES"})
                if e.target in self.nodes and self.outgoing(e.target, {"CALLS", "ROUTES_TO"})
            ]
            frontier = sorted(set(defined)) if defined else [primary]
        else:
            frontier = sorted(set(seeds))

        visited: set[str] = set(frontier)
        steps: list[dict[str, Any]] = [
            {
                "step": 0,
                "nodes": list(frontier),
                "edges": [],
            }
        ]
        total_edges = 0

        for step_idx in range(1, max_depth + 1):
            next_nodes: set[str] = set()
            step_edges: list[dict[str, Any]] = []
            seen_step_edges: set[tuple[str, str, str]] = set()

            for src_id in frontier:
                src_node = self.nodes.get(src_id)
                out_edges = self.outgoing(src_id, {"ROUTES_TO", "CALLS"})
                # If a file node has no direct CALLS, fall back to IMPORTS for file-level pipeline hops
                if not out_edges and src_node and src_node.kind == "file":
                    out_edges = [
                        e
                        for e in self.outgoing(src_id, {"IMPORTS"})
                        if e.target in self.nodes and self.nodes[e.target].kind != "external"
                    ]

                for edge in sorted(out_edges, key=lambda e: (e.metadata.get("line", 0), e.target)):
                    tgt_node = self.nodes.get(edge.target)
                    if not tgt_node or tgt_node.kind == "external":
                        continue
                    if edge.target in visited and edge.target not in next_nodes:
                        continue
                    ekey = (edge.source, edge.target, edge.relation)
                    if ekey in seen_step_edges:
                        continue
                    seen_step_edges.add(ekey)
                    next_nodes.add(edge.target)
                    src_file = src_node.file_path if src_node else None
                    tgt_file = tgt_node.file_path
                    step_edges.append(
                        {
                            "source": edge.source,
                            "target": edge.target,
                            "source_file": src_file,
                            "target_file": tgt_file,
                            "cross_file": bool(src_file and tgt_file and src_file != tgt_file),
                            "relation": edge.relation,
                            "provenance": edge.provenance,
                            "line": edge.metadata.get("line"),
                            "raw_callee": edge.metadata.get("raw_callee"),
                        }
                    )

            if not next_nodes:
                break

            visited.update(next_nodes)
            frontier = sorted(next_nodes)
            total_edges += len(step_edges)
            steps.append(
                {
                    "step": step_idx,
                    "nodes": frontier,
                    "edges": step_edges,
                }
            )

        return {
            "id": primary,
            "label": primary_node.label,
            "kind": primary_node.kind,
            "file_path": primary_node.file_path,
            "total_steps": len(steps),
            "total_nodes": len(visited),
            "total_edges": total_edges,
            "steps": steps,
        }

    def discover_pipelines(self, max_pipelines: int = 30, max_depth: int = 8) -> list[dict[str, Any]]:
        """Auto-discover top execution pipelines starting from routes and entrypoint functions."""
        routes = sorted(nid for nid, n in self.nodes.items() if n.kind == "route")

        entry_hints = ("main", "run", "cli", "app", "execute", "handle", "start", "dispatch", "process")
        entry_candidates: list[tuple[int, int, str]] = []
        for nid, node in self.nodes.items():
            if node.kind not in {"function", "method"}:
                continue
            if "test" in node.metadata.get("categories", []):
                continue
            if self.incoming(nid, {"CALLS", "ROUTES_TO"}):
                continue
            out_calls = self.outgoing(nid, {"CALLS"})
            if not out_calls:
                continue
            lower_lbl = node.label.lower().split(".")[-1]
            hint_priority = 0 if any(lower_lbl.startswith(h) for h in entry_hints) else 1
            entry_candidates.append((hint_priority, -len(out_calls), nid))

        entry_candidates.sort()
        ordered_seeds = routes + [nid for _, _, nid in entry_candidates[: max_pipelines * 2]]

        discovered: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for seed in ordered_seeds:
            if seed in seen_ids:
                continue
            seen_ids.add(seed)
            pipe = self.trace_pipeline(seed, max_depth=max_depth)
            if pipe["total_steps"] >= 2:
                discovered.append(pipe)
            if len(discovered) >= max_pipelines:
                break

        discovered.sort(
            key=lambda p: (
                0 if p["kind"] == "route" else 1,
                -p["total_steps"],
                -p["total_nodes"],
                p["id"],
            )
        )
        return discovered[:max_pipelines]

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
