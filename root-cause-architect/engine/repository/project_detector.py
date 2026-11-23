from __future__ import annotations

import json
import re
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from engine.repository.scanner import RepositoryScan


MANIFEST_FILENAMES = {
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "Pipfile": "python",
    "package.json": "javascript",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "pubspec.yaml": "dart",
    "composer.json": "php",
    "pom.xml": "java",
    "build.gradle": "java",
    "build.gradle.kts": "java",
    "Gemfile": "ruby",
}

_REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)")
_GO_REQUIRE_RE = re.compile(r"^\s*(?:require\s+)?([a-zA-Z0-9._\-/]+)\s+v\d+")
_CARGO_DEP_RE = re.compile(r"^\s*([A-Za-z0-9_\-]+)\s*=")


@dataclass
class DetectedManifest:
    path: str
    ecosystem: str
    dependencies: list[str] = field(default_factory=list)
    scripts: dict[str, str] = field(default_factory=dict)
    parse_error: str | None = None


@dataclass
class ProjectSummary:
    root: str
    languages: dict[str, int] = field(default_factory=dict)
    categories: dict[str, int] = field(default_factory=dict)
    manifests: list[dict[str, Any]] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    test_files: list[str] = field(default_factory=list)
    migration_files: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProjectDetector:
    """Extracts project ecosystems, manifests, and declared dependencies from a RepositoryScan."""

    def detect(self, scan: RepositoryScan) -> ProjectSummary:
        root_path = Path(scan.root)
        summary = ProjectSummary(root=scan.root)

        all_deps: dict[str, set[str]] = {}

        for entry in scan.files:
            rel_path = entry["path"]
            lang = entry.get("language")
            categories = entry.get("categories", [])

            if lang:
                summary.languages[lang] = summary.languages.get(lang, 0) + 1

            for cat in categories:
                summary.categories[cat] = summary.categories.get(cat, 0) + 1

            if "test" in categories:
                summary.test_files.append(rel_path)
            if "migration" in categories:
                summary.migration_files.append(rel_path)
            if "configuration" in categories:
                summary.config_files.append(rel_path)

            if entry.get("status") != "analyze":
                continue

            filename = Path(rel_path).name
            if filename in MANIFEST_FILENAMES:
                ecosystem = MANIFEST_FILENAMES[filename]
                manifest = self._parse_manifest(root_path / rel_path, rel_path, ecosystem)
                summary.manifests.append(asdict(manifest))
                if manifest.dependencies:
                    all_deps.setdefault(ecosystem, set()).update(manifest.dependencies)

        summary.dependencies = {
            eco: sorted(deps) for eco, deps in sorted(all_deps.items())
        }
        return summary

    def _parse_manifest(
        self,
        full_path: Path,
        rel_path: str,
        ecosystem: str,
    ) -> DetectedManifest:
        manifest = DetectedManifest(path=rel_path, ecosystem=ecosystem)
        try:
            text = full_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            manifest.parse_error = str(exc)
            return manifest

        filename = full_path.name
        try:
            if filename == "package.json":
                data = json.loads(text)
                deps: set[str] = set()
                for key in ("dependencies", "devDependencies", "peerDependencies"):
                    section = data.get(key)
                    if isinstance(section, dict):
                        deps.update(section.keys())
                manifest.dependencies = sorted(deps)
                if isinstance(data.get("scripts"), dict):
                    manifest.scripts = {
                        str(k): str(v) for k, v in data["scripts"].items()
                    }
            elif filename == "pyproject.toml":
                data = tomllib.loads(text)
                deps = set()
                project = data.get("project", {})
                for item in project.get("dependencies", []):
                    match = _REQ_NAME_RE.match(str(item))
                    if match:
                        deps.add(match.group(1))
                for group_deps in project.get("optional-dependencies", {}).values():
                    for item in group_deps:
                        match = _REQ_NAME_RE.match(str(item))
                        if match:
                            deps.add(match.group(1))
                poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
                if isinstance(poetry_deps, dict):
                    deps.update(k for k in poetry_deps if k.lower() != "python")
                manifest.dependencies = sorted(deps)
                scripts = project.get("scripts", {})
                if isinstance(scripts, dict):
                    manifest.scripts = {str(k): str(v) for k, v in scripts.items()}
            elif filename == "requirements.txt":
                deps = set()
                for line in text.splitlines():
                    stripped = line.strip()
                    if not stripped or stripped.startswith(("#", "-")):
                        continue
                    match = _REQ_NAME_RE.match(stripped)
                    if match:
                        deps.add(match.group(1))
                manifest.dependencies = sorted(deps)
            elif filename == "composer.json":
                data = json.loads(text)
                deps = set()
                for key in ("require", "require-dev"):
                    if isinstance(data.get(key), dict):
                        deps.update(data[key].keys())
                manifest.dependencies = sorted(deps)
            elif filename == "go.mod":
                deps = set()
                for line in text.splitlines():
                    match = _GO_REQUIRE_RE.match(line)
                    if match:
                        deps.add(match.group(1))
                manifest.dependencies = sorted(deps)
            elif filename == "Cargo.toml":
                data = tomllib.loads(text)
                deps = set()
                for key in ("dependencies", "dev-dependencies"):
                    if isinstance(data.get(key), dict):
                        deps.update(data[key].keys())
                manifest.dependencies = sorted(deps)
            elif filename == "pubspec.yaml":
                in_deps = False
                deps = set()
                for line in text.splitlines():
                    if re.match(r"^(dependencies|dev_dependencies)\s*:", line):
                        in_deps = True
                        continue
                    if in_deps and line and not line[0].isspace():
                        in_deps = False
                    if in_deps:
                        m = re.match(r"^\s{2}([A-Za-z0-9_]+)\s*:", line)
                        if m:
                            deps.add(m.group(1))
                manifest.dependencies = sorted(deps)
        except Exception as exc:
            manifest.parse_error = f"{type(exc).__name__}: {exc}"

        return manifest
