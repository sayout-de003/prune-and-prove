from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from engine.repository.project_detector import ProjectSummary
from engine.repository.scanner import RepositoryScan


_PYTHON_MAIN_RE = re.compile(r'if\s+__name__\s*==\s*["\']__main__["\']\s*:')
_PYTHON_APP_RE = re.compile(r"\b(FastAPI|Flask|Starlette|Celery)\s*\(")
_JS_LISTEN_RE = re.compile(r"\.(listen|createServer)\s*\(")
_GO_MAIN_RE = re.compile(r"\bfunc\s+main\s*\(\s*\)")
_DART_MAIN_RE = re.compile(r"\bvoid\s+main\s*\(")

_KNOWN_ENTRYPOINT_FILENAMES = {
    "manage.py": "django_cli",
    "wsgi.py": "python_wsgi",
    "asgi.py": "python_asgi",
    "artisan": "laravel_cli",
}


@dataclass
class Entrypoint:
    path: str
    kind: str
    evidence: str
    language: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EntrypointDetector:
    """Detects application, HTTP server, and CLI entrypoints with explicit evidence."""

    def detect(
        self,
        scan: RepositoryScan,
        project_summary: ProjectSummary,
    ) -> list[Entrypoint]:
        root_path = Path(scan.root)
        entrypoints: list[Entrypoint] = []
        seen: set[tuple[str, str]] = set()

        def add(path: str, kind: str, evidence: str, language: str | None = None) -> None:
            key = (path, kind)
            if key not in seen:
                seen.add(key)
                entrypoints.append(
                    Entrypoint(path=path, kind=kind, evidence=evidence, language=language)
                )

        # 1. Manifest-declared scripts / CLI entrypoints
        for manifest in project_summary.manifests:
            scripts = manifest.get("scripts", {})
            for script_name, command in scripts.items():
                if script_name in {"start", "dev", "serve", "build"} or manifest["ecosystem"] == "python":
                    add(
                        manifest["path"],
                        f"manifest_script:{script_name}",
                        f"{script_name} -> {command}",
                        manifest["ecosystem"],
                    )

        # 2. Source-file entrypoints (skip test/generated files)
        for entry in scan.files:
            if entry.get("status") != "analyze":
                continue
            categories = set(entry.get("categories", []))
            if "test" in categories or "generated" in categories:
                continue

            rel_path = entry["path"]
            lang = entry.get("language")
            filename = Path(rel_path).name

            if filename in _KNOWN_ENTRYPOINT_FILENAMES:
                add(rel_path, _KNOWN_ENTRYPOINT_FILENAMES[filename], f"known entrypoint filename: {filename}", lang)

            if lang not in {"python", "javascript", "typescript", "javascript_react", "typescript_react", "go", "dart"}:
                continue

            try:
                text = (root_path / rel_path).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            if lang == "python":
                if _PYTHON_MAIN_RE.search(text):
                    add(rel_path, "python_main", 'if __name__ == "__main__":', lang)
                app_match = _PYTHON_APP_RE.search(text)
                if app_match:
                    add(rel_path, "python_app_instance", f"{app_match.group(1)}(...) instantiation", lang)
            elif lang in {"javascript", "typescript", "javascript_react", "typescript_react"}:
                listen_match = _JS_LISTEN_RE.search(text)
                if listen_match:
                    add(rel_path, "node_server", f".{listen_match.group(1)}(...) server start", lang)
            elif lang == "go" and _GO_MAIN_RE.search(text):
                add(rel_path, "go_main", "func main()", lang)
            elif lang == "dart" and _DART_MAIN_RE.search(text):
                add(rel_path, "dart_main", "void main()", lang)

        entrypoints.sort(key=lambda e: (e.path, e.kind))
        return entrypoints
