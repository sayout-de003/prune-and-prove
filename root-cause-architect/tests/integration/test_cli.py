from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ANALYZE_SCRIPT = REPO_ROOT / "scripts" / "analyze.py"
PYTHON_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "python-project"


class CliIntegrationTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ANALYZE_SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_health_command(self) -> None:
        proc = self._run("health")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["version"], "2.0.0")

    def test_map_graph_and_impact_on_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            map_out = Path(tmp) / "repository-map.md"
            graph_out = Path(tmp) / "dependency-graph.json"
            mmd_out = Path(tmp) / "architecture.mmd"

            p_map = self._run("map", str(PYTHON_FIXTURE), "--output", str(map_out))
            self.assertEqual(p_map.returncode, 0, p_map.stderr)
            self.assertIn("fastapi", map_out.read_text(encoding="utf-8"))

            p_graph = self._run(
                "graph",
                str(PYTHON_FIXTURE),
                "--output",
                str(graph_out),
                "--mermaid",
                str(mmd_out),
            )
            self.assertEqual(p_graph.returncode, 0, p_graph.stderr)
            summary = json.loads(p_graph.stdout)
            self.assertTrue(summary["validation"]["valid"])
            self.assertTrue(graph_out.exists())
            self.assertTrue(mmd_out.exists())

            p_impact = self._run(
                "impact",
                str(PYTHON_FIXTURE),
                "app/services/payment.py",
                "--json",
            )
            self.assertEqual(p_impact.returncode, 0, p_impact.stderr)
            impact = json.loads(p_impact.stdout)
            self.assertIn("tests/test_payment.py", impact["covering_tests"])

    def test_self_analysis_on_root_cause_architect(self) -> None:
        """Dogfood the analyzer on root-cause-architect itself."""
        p_graph = self._run("graph", str(REPO_ROOT))
        self.assertEqual(p_graph.returncode, 0, p_graph.stderr)
        summary = json.loads(p_graph.stdout)
        self.assertTrue(summary["validation"]["valid"])
        self.assertGreater(summary["validation"]["node_count"], 50)
        self.assertGreater(summary["validation"]["edge_count"], 50)


if __name__ == "__main__":
    unittest.main()
