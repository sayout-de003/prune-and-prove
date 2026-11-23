from __future__ import annotations

import unittest
from pathlib import Path

from engine.config_loader import load_toolkit_configs
from engine.repository.manifest_builder import ManifestBuilder


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
PYTHON_FIXTURE = FIXTURES / "python-project"
TS_FIXTURE = FIXTURES / "typescript-project"


class DetectorsAndConfigTests(unittest.TestCase):
    def test_config_loader_loads_all_yaml_files(self) -> None:
        configs = load_toolkit_configs()
        self.assertEqual(configs["default"]["system"]["version"], "2.0.0")
        self.assertIn("python", configs["languages"]["languages"])
        self.assertIn("node_modules", configs["exclusions"]["directories"]["exact"])
        self.assertIn("fastapi", configs["frameworks"]["frameworks"])

    def test_manifest_builder_on_python_fixture(self) -> None:
        manifest, scan = ManifestBuilder().build(PYTHON_FIXTURE)
        self.assertGreaterEqual(scan.total_analyzed, 5)
        self.assertIn("python", manifest.languages)
        self.assertIn("fastapi", manifest.dependencies.get("python", []))

        fw_names = [f["name"] for f in manifest.frameworks]
        self.assertIn("fastapi", fw_names)
        fastapi = next(f for f in manifest.frameworks if f["name"] == "fastapi")
        self.assertEqual(fastapi["role"], "primary")
        self.assertGreaterEqual(len(fastapi["evidence"]), 2)

        ep_paths = {e["path"] for e in manifest.entrypoints}
        self.assertIn("app/main.py", ep_paths)
        self.assertIn("pyproject.toml", ep_paths)

        md = manifest.to_markdown()
        self.assertIn("# Repository Map", md)
        self.assertIn("fastapi", md)

    def test_manifest_builder_on_typescript_fixture(self) -> None:
        manifest, _ = ManifestBuilder().build(TS_FIXTURE)
        self.assertIn("typescript", manifest.languages)
        self.assertIn("express", manifest.dependencies.get("javascript", []))
        fw_names = [f["name"] for f in manifest.frameworks]
        self.assertIn("express", fw_names)
        ep_kinds = {e["kind"] for e in manifest.entrypoints}
        self.assertIn("node_server", ep_kinds)


if __name__ == "__main__":
    unittest.main()
