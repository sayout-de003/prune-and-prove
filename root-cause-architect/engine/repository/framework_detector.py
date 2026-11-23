from __future__ import annotations

import fnmatch
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from engine.repository.project_detector import ProjectSummary
from engine.repository.scanner import RepositoryScan

_GENERIC_MANIFESTS = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "cargo.toml",
    "go.mod",
    "composer.json",
    "pubspec.yaml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
}


def _glob_match(path: str, pattern: str) -> bool:
    if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(f"/{path}", f"*/{pattern}"):
        return True
    if "**/" in pattern:
        collapsed = pattern.replace("**/", "")
        if fnmatch.fnmatch(path, collapsed) or fnmatch.fnmatch(f"/{path}", f"*/{collapsed}"):
            return True
    return False


@dataclass
class FrameworkDetection:
    name: str
    language: str
    confidence: float
    confidence_level: str
    role: str  # "primary" or "secondary"
    evidence: list[dict[str, str]] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FrameworkDetector:
    """
    Evidence-based framework detector governed by config/frameworks.yaml.
    Never infers a framework from directory names alone; requires dependency or config evidence.
    """

    def __init__(self, frameworks_config: dict[str, Any]) -> None:
        self.config = frameworks_config

    def detect(
        self,
        scan: RepositoryScan,
        project_summary: ProjectSummary,
    ) -> list[FrameworkDetection]:
        policy = self.config.get("detection_policy", {})
        min_evidence = int(policy.get("minimum_evidence", 2))
        require_dep_or_cfg = bool(policy.get("require_dependency_or_config_evidence", True))
        levels = policy.get("confidence_levels", {"high": 0.85, "medium": 0.65, "low": 0.40})

        all_paths = [f["path"] for f in scan.files]
        filenames_to_paths: dict[str, list[str]] = {}
        for p in all_paths:
            filenames_to_paths.setdefault(Path(p).name.lower(), []).append(p)

        declared_deps: dict[str, str] = {}
        for manifest in project_summary.manifests:
            for dep in manifest.get("dependencies", []):
                declared_deps[dep.lower()] = manifest["path"]

        detections: list[FrameworkDetection] = []
        frameworks = self.config.get("frameworks", {})

        for name, spec in frameworks.items():
            evidence: list[dict[str, str]] = []
            missing: list[str] = []
            has_dep_or_cfg = False

            # 1. Dependency evidence
            matched_dep = False
            for dep in spec.get("dependencies", []):
                if dep.lower() in declared_deps:
                    evidence.append(
                        {
                            "type": "dependency",
                            "detail": f"{dep} in {declared_deps[dep.lower()]}",
                        }
                    )
                    matched_dep = True
                    has_dep_or_cfg = True
            if spec.get("dependencies") and not matched_dep:
                missing.append(f"dependency ({', '.join(spec['dependencies'])})")

            # 2. Config file evidence
            matched_cfg = False
            for cfg in spec.get("config_files", []):
                cfg_lower = cfg.lower()
                if "/" in cfg_lower:
                    matches = [p for p in all_paths if p.lower().endswith(cfg_lower)]
                else:
                    matches = filenames_to_paths.get(cfg_lower, [])
                if matches:
                    evidence.append(
                        {"type": "config_file", "detail": matches[0]}
                    )
                    matched_cfg = True
                    # Generic ecosystem manifests (e.g., package.json) do not prove a specific framework on their own
                    if cfg_lower not in _GENERIC_MANIFESTS:
                        has_dep_or_cfg = True
            if spec.get("config_files") and not matched_cfg:
                missing.append(f"config file ({', '.join(spec['config_files'][:3])})")

            # 3. Structural file pattern evidence
            matched_patterns: list[str] = []
            for pattern in spec.get("patterns", []):
                for p in all_paths:
                    if _glob_match(p, pattern):
                        matched_patterns.append(p)
                        break
            if matched_patterns:
                evidence.append(
                    {"type": "file_pattern", "detail": ", ".join(matched_patterns[:3])}
                )
            elif spec.get("patterns"):
                missing.append("framework file patterns")

            if require_dep_or_cfg and not has_dep_or_cfg:
                continue
            if len(evidence) < min_evidence:
                continue

            # Compute confidence based on distinct evidence types
            distinct_types = {e["type"] for e in evidence}
            if "dependency" in distinct_types and len(distinct_types) >= 2:
                confidence = min(0.95, 0.70 + 0.12 * len(evidence))
            elif has_dep_or_cfg:
                confidence = min(0.80, 0.50 + 0.12 * len(evidence))
            else:
                confidence = 0.45

            if confidence >= float(levels.get("high", 0.85)):
                level = "high"
            elif confidence >= float(levels.get("medium", 0.65)):
                level = "medium"
            else:
                level = "low"

            detections.append(
                FrameworkDetection(
                    name=name,
                    language=str(spec.get("language", "unknown")),
                    confidence=round(confidence, 2),
                    confidence_level=level,
                    role="secondary",
                    evidence=evidence,
                    missing_evidence=missing,
                )
            )

        detections.sort(key=lambda d: (-d.confidence, d.name))
        if detections:
            detections[0].role = "primary"
        return detections
