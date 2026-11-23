from __future__ import annotations

import json
import unittest
from pathlib import Path

from engine.graph.dependency_graph import DependencyGraph, GraphEdge, GraphNode
from engine.graph.graph_builder import GraphBuilder
from engine.graph.graph_exporter import GraphExporter
from engine.graph.graph_validator import GraphValidator


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
PYTHON_FIXTURE = FIXTURES / "python-project"
TS_FIXTURE = FIXTURES / "typescript-project"


class KnowledgeGraphTests(unittest.TestCase):
    def test_python_graph_builds_valid_cross_file_edges_and_blast_radius(self) -> None:
        graph, _ = GraphBuilder().build_from_path(PYTHON_FIXTURE)
        validation = GraphValidator().validate(graph)

        self.assertTrue(validation.valid, f"Validation errors: {validation.to_dict()}")
        self.assertEqual(validation.dangling_edges, [])
        self.assertIn("static_ast", validation.provenance_counts)

        # Blast radius on payment_repo.py should trace upstream to payment.py, main.py, and test_payment.py
        impact = graph.blast_radius("app/repositories/payment_repo.py", max_depth=4)
        self.assertEqual(impact["matched_nodes"], ["file:app/repositories/payment_repo.py"])

        upstream_files = {item["file_path"] for item in impact["upstream_dependents"]}
        self.assertIn("app/services/payment.py", upstream_files)
        self.assertIn("app/main.py", upstream_files)
        self.assertIn("tests/test_payment.py", impact["covering_tests"])
        # Dynamic signals on payment.py must surface as warnings in blast radius
        self.assertTrue(len(impact["dynamic_warnings"]) >= 1)

        # JSON and Mermaid exports
        parsed_json = json.loads(GraphExporter.to_json(graph))
        self.assertEqual(parsed_json["stats"]["node_count"], len(graph.nodes))
        mermaid = GraphExporter.to_mermaid(graph)
        self.assertTrue(mermaid.startswith("flowchart LR"))
        self.assertIn("ROUTES_TO", mermaid)

    def test_typescript_graph_resolves_relative_imports_and_routes(self) -> None:
        graph, _ = GraphBuilder().build_from_path(TS_FIXTURE)
        validation = GraphValidator().validate(graph)
        self.assertTrue(validation.valid)

        impact = graph.blast_radius("src/routes/orders.ts", max_depth=3)
        upstream_ids = {item["id"] for item in impact["upstream_dependents"]}
        self.assertIn("file:src/server.ts", upstream_ids)
        self.assertIn("route:POST /orders", upstream_ids)

    def test_validator_detects_import_cycles(self) -> None:
        g = DependencyGraph(root="/tmp/cycle")
        g.add_node(GraphNode(id="file:a.py", kind="file", label="a.py", file_path="a.py"))
        g.add_node(GraphNode(id="file:b.py", kind="file", label="b.py", file_path="b.py"))
        g.add_edge(GraphEdge(source="file:a.py", target="file:b.py", relation="IMPORTS", provenance="static_ast"))
        g.add_edge(GraphEdge(source="file:b.py", target="file:a.py", relation="IMPORTS", provenance="static_ast"))

        report = GraphValidator().validate(g)
        self.assertTrue(report.valid)
        self.assertEqual(len(report.import_cycles), 1)
        self.assertEqual(sorted(report.import_cycles[0]), ["a.py", "b.py"])

    def test_pipeline_tracing_and_interactive_3d_html_export(self) -> None:
        graph, _ = GraphBuilder().build_from_path(PYTHON_FIXTURE)
        validation = GraphValidator().validate(graph)

        # Trace execution pipeline from FastAPI route across files and functions
        pipeline = graph.trace_pipeline("route:POST /api/payments", max_depth=6)
        self.assertEqual(pipeline["kind"], "route")
        self.assertGreaterEqual(pipeline["total_steps"], 3)
        self.assertEqual(pipeline["steps"][0]["nodes"], ["route:POST /api/payments"])
        all_step_nodes = [nid for st in pipeline["steps"] for nid in st["nodes"]]
        self.assertTrue(any("payment" in nid for nid in all_step_nodes))

        # Auto-discover pipelines prioritizes routes
        discovered = graph.discover_pipelines(max_pipelines=10, max_depth=6)
        self.assertTrue(len(discovered) >= 1)
        self.assertEqual(discovered[0]["kind"], "route")

        # Interactive 3D HTML export contains embedded deterministic JSON payload and full interaction hooks
        html = GraphExporter.to_interactive_3d_html(graph, validation=validation.to_dict())
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("3d-force-graph", html)
        self.assertNotIn("three@0.160.0/build/three.min.js", html)
        self.assertIn('controlType: "orbit"', html)
        self.assertIn(".onLinkClick(", html)
        self.assertIn(".onNodeDragEnd(", html)
        self.assertIn("openNodeConnections", html)
        self.assertIn("rca-graph-data", html)
        self.assertIn("fileCallLinks", html)
        self.assertIn("route:POST /api/payments", html)

        # Extract embedded JSON and verify structure & integrity
        marker_start = '<script id="rca-graph-data" type="application/json">'
        start_idx = html.index(marker_start) + len(marker_start)
        end_idx = html.index("</script>", start_idx)
        payload = json.loads(html[start_idx:end_idx])
        self.assertGreater(payload["stats"]["nodes"], 5)
        self.assertGreater(payload["stats"]["edges"], 5)
        self.assertGreaterEqual(len(payload["pipelines"]), 1)
        self.assertTrue(any(e["relation"] == "CALLS" for e in payload["edges"]))
        self.assertTrue(len(payload["fileCallLinks"]) >= 1)


if __name__ == "__main__":
    unittest.main()
