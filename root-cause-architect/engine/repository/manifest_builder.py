from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.config_loader import load_toolkit_configs
from engine.repository.entrypoint_detector import EntrypointDetector
from engine.repository.file_classifier import FileClassifier
from engine.repository.framework_detector import FrameworkDetector
from engine.repository.project_detector import ProjectDetector
from engine.repository.scanner import RepositoryScan, RepositoryScanner


@dataclass
class RepositoryManifest:
    root: str
    generated_at: str
    git_commit: str | None
    content_fingerprint: str
    totals: dict[str, int]
    languages: dict[str, int]
    categories: dict[str, int]
    manifests: list[dict[str, Any]]
    dependencies: dict[str, list[str]]
    frameworks: list[dict[str, Any]]
    entrypoints: list[dict[str, Any]]
    test_files: list[str]
    migration_files: list[str]
    config_files: list[str]
    errors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        lines = [
            f"# Repository Map — `{Path(self.root).name}`",
            "",
            f"- **Root:** `{self.root}`",
            f"- **Generated:** `{self.generated_at}`",
            f"- **Git Commit:** `{self.git_commit or 'not-a-git-repo'}`",
            f"- **Fingerprint:** `{self.content_fingerprint}`",
            f"- **Files:** {self.totals['discovered']} discovered "
            f"({self.totals['analyzed']} analyzed, {self.totals['inventory_only']} inventory-only, "
            f"{self.totals['skipped']} skipped)",
            "",
            "## Languages",
            "",
        ]
        if self.languages:
            for lang, count in sorted(self.languages.items(), key=lambda kv: (-kv[1], kv[0])):
                lines.append(f"- `{lang}`: {count} files")
        else:
            lines.append("- None detected")

        lines.extend(["", "## Detected Frameworks", ""])
        if self.frameworks:
            for fw in self.frameworks:
                ev = "; ".join(f"{e['type']}: {e['detail']}" for e in fw["evidence"])
                lines.append(
                    f"- **{fw['name']}** ({fw['role']}, confidence `{fw['confidence']}` / {fw['confidence_level']}) — {ev}"
                )
        else:
            lines.append("- None detected with sufficient evidence")

        lines.extend(["", "## Entrypoints", ""])
        if self.entrypoints:
            for ep in self.entrypoints:
                lines.append(f"- `{ep['path']}` (`{ep['kind']}`) — {ep['evidence']}")
        else:
            lines.append("- None detected")

        lines.extend(["", "## Dependency Manifests", ""])
        if self.manifests:
            for m in self.manifests:
                dep_count = len(m.get("dependencies", []))
                lines.append(f"- `{m['path']}` ({m['ecosystem']}, {dep_count} dependencies)")
        else:
            lines.append("- None detected")

        lines.extend(
            [
                "",
                "## Test & Migration Inventory",
                "",
                f"- Test files: {len(self.test_files)}",
                f"- Migration files: {len(self.migration_files)}",
                f"- Configuration files: {len(self.config_files)}",
            ]
        )
        return "\n".join(lines) + "\n"


class ManifestBuilder:
    """Orchestrates Phase 1–2 repository discovery into a fingerprinted RepositoryManifest."""

    def __init__(self, configs: dict[str, dict[str, Any]] | None = None) -> None:
        self.configs = configs if configs is not None else load_toolkit_configs()
        self.classifier = FileClassifier(
            self.configs.get("languages", {}),
            self.configs.get("exclusions", {}),
        )
        self.scanner = RepositoryScanner(self.classifier)
        self.project_detector = ProjectDetector()
        self.framework_detector = FrameworkDetector(self.configs.get("frameworks", {}))
        self.entrypoint_detector = EntrypointDetector()

    def build(self, root: str | Path) -> tuple[RepositoryManifest, RepositoryScan]:
        scan = self.scanner.scan(root)
        project = self.project_detector.detect(scan)
        frameworks = self.framework_detector.detect(scan, project)
        entrypoints = self.entrypoint_detector.detect(scan, project)

        manifest = RepositoryManifest(
            root=scan.root,
            generated_at=datetime.now(timezone.utc).isoformat(),
            git_commit=self._get_git_commit(scan.root),
            content_fingerprint=self._compute_fingerprint(scan),
            totals={
                "discovered": scan.total_discovered,
                "analyzed": scan.total_analyzed,
                "inventory_only": scan.total_inventory_only,
                "skipped": scan.total_skipped,
            },
            languages=project.languages,
            categories=project.categories,
            manifests=project.manifests,
            dependencies=project.dependencies,
            frameworks=[f.to_dict() for f in frameworks],
            entrypoints=[e.to_dict() for e in entrypoints],
            test_files=project.test_files,
            migration_files=project.migration_files,
            config_files=project.config_files,
            errors=scan.errors,
        )
        return manifest, scan

    @staticmethod
    def _get_git_commit(root: str) -> str | None:
        try:
            proc = subprocess.run(
                ["git", "-C", root, "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
        return None

    @staticmethod
    def _compute_fingerprint(scan: RepositoryScan) -> str:
        digest = hashlib.sha256()
        for entry in scan.files:
            digest.update(
                f"{entry['path']}:{entry.get('size_bytes')}:{entry.get('modified_time_ns')}\n".encode("utf-8")
            )
        return digest.hexdigest()[:16]
