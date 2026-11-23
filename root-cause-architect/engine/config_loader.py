from __future__ import annotations

from pathlib import Path
from typing import Any


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in {"null", "none", "~"}:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for idx, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if idx == 0 or line[idx - 1].isspace():
                return line[:idx]
    return line


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """
    Minimal indentation-based YAML subset parser (mappings, sequences, scalars).
    shortcut: supports block mappings/lists used in config/*.yaml; install PyYAML for full YAML 1.2 (anchors, flow collections, multiline blocks).
    """
    tokens: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        cleaned = _strip_comment(raw_line).rstrip()
        if not cleaned.strip():
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        tokens.append((indent, cleaned.lstrip(" ")))

    def parse_block(index: int, min_indent: int) -> tuple[Any, int]:
        if index >= len(tokens):
            return {}, index

        indent, content = tokens[index]
        if content.startswith("- "):
            items: list[Any] = []
            while index < len(tokens):
                cur_indent, cur_content = tokens[index]
                if cur_indent < min_indent or cur_indent != indent or not cur_content.startswith("- "):
                    break
                items.append(_parse_scalar(cur_content[2:]))
                index += 1
            return items, index

        mapping: dict[str, Any] = {}
        while index < len(tokens):
            cur_indent, cur_content = tokens[index]
            if cur_indent < min_indent or cur_indent != indent:
                break
            if cur_content.startswith("- "):
                break
            if ":" not in cur_content:
                index += 1
                continue
            key, _, rest = cur_content.partition(":")
            key = key.strip().strip('"').strip("'")
            rest = rest.strip()
            index += 1
            if rest:
                mapping[key] = _parse_scalar(rest)
            elif index < len(tokens) and tokens[index][0] > cur_indent:
                child, index = parse_block(index, tokens[index][0])
                mapping[key] = child
            else:
                mapping[key] = {}
        return mapping, index

    parsed, _ = parse_block(0, 0)
    return parsed if isinstance(parsed, dict) else {}


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-not-found]

        loaded = yaml.safe_load(text)
        return loaded if isinstance(loaded, dict) else {}
    except ImportError:
        return _parse_simple_yaml(text)


def load_toolkit_configs(config_dir: str | Path | None = None) -> dict[str, dict[str, Any]]:
    base = Path(config_dir) if config_dir is not None else CONFIG_DIR
    result: dict[str, dict[str, Any]] = {}
    for name in (
        "default",
        "languages",
        "exclusions",
        "frameworks",
        "safety",
        "verification",
        "quality-gates",
    ):
        candidate = base / f"{name}.yaml"
        result[name] = load_yaml_file(candidate) if candidate.exists() else {}
    return result
