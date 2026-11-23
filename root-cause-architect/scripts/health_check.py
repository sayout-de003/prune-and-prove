#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.config_loader import load_toolkit_configs
from engine.parsers.parser_registry import ParserRegistry


def run_health_check() -> dict[str, object]:
    configs = load_toolkit_configs()
    registry = ParserRegistry()
    missing_configs = [name for name, data in configs.items() if not data]
    skill_exists = (ROOT / "SKILL.md").exists()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else "unknown"

    return {
        "status": "ok" if (skill_exists and not missing_configs) else "degraded",
        "version": version,
        "skill_present": skill_exists,
        "configs_loaded": sorted(k for k, v in configs.items() if v),
        "missing_configs": missing_configs,
        "supported_languages": registry.supported_languages,
        "python_version": sys.version.split()[0],
    }


def main(argv: list[str] | None = None) -> int:
    report = run_health_check()
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
