from __future__ import annotations

import re

from engine.parsers.parser_registry import (
    CallInfo,
    DynamicSignal,
    ImportInfo,
    ParseResult,
    RouteInfo,
    SymbolInfo,
)


_ES_IMPORT_RE = re.compile(
    r"""^\s*import\s+(?:(?P<names>\{[^}]+\}|[*]\s+as\s+\w+|\w+(?:\s*,\s*\{[^}]+\})?)\s+from\s+)?["'](?P<module>[^"']+)["']""",
    re.MULTILINE,
)
_CJS_REQUIRE_RE = re.compile(
    r"""(?:const|let|var)\s+(?P<names>\{[^}]+\}|\w+)\s*=\s*require\(\s*["'](?P<module>[^"']+)["']\s*\)"""
)
_CLASS_RE = re.compile(
    r"""^\s*(?P<export>export\s+(?:default\s+)?)?class\s+(?P<name>[A-Za-z_$][\w$]*)(?:\s+extends\s+(?P<base>[A-Za-z_$][\w$.]*))?""",
    re.MULTILINE,
)
_FUNC_RE = re.compile(
    r"""^\s*(?P<export>export\s+(?:default\s+)?)?(?:async\s+)?function\s+(?P<name>[A-Za-z_$][\w$]*)\s*\((?P<params>[^)]*)\)""",
    re.MULTILINE,
)
_ARROW_FUNC_RE = re.compile(
    r"""^\s*(?P<export>export\s+)?(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?\((?P<params>[^)]*)\)\s*(?::[^=]+)?=>""",
    re.MULTILINE,
)
_ROUTE_RE = re.compile(
    r"""\b(?:app|router)\.(?P<method>get|post|put|patch|delete|use)\(\s*["'](?P<path>[^"']+)["']\s*,\s*(?P<handler>[A-Za-z_$][\w$.]*)"""
)
_CALL_RE = re.compile(r"""\b(?P<callee>[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\(""")
_DYNAMIC_IMPORT_RE = re.compile(r"""\bimport\s*\(""")

_NON_CALL_KEYWORDS = {
    "if", "for", "while", "switch", "catch", "function", "return", "typeof", "new", "super", "require",
}


def _line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def _clean_names(raw: str | None) -> list[str]:
    if not raw:
        return []
    cleaned = raw.replace("{", "").replace("}", "")
    names: list[str] = []
    for part in cleaned.split(","):
        token = part.strip().split(" as ")[0].strip()
        if token and token != "*":
            names.append(token)
    return names


class JavaScriptParser:
    """
    Structural JavaScript/JSX parser (stdlib-only).
    Marks all call edges as static_structural, never semantic_verified.
    shortcut: regex-based structural extraction; upgrade to TypeScript Compiler API or tree-sitter when full semantic type resolution is needed.
    """

    name = "js_structural"
    default_language = "javascript"

    def parse(self, file_path: str, source: str) -> ParseResult:
        result = ParseResult(
            file_path=file_path,
            language=self.default_language,
            parser_name=self.name,
            provenance="static_structural",
            limitations=["Structural regex extraction; does not perform full JS/TS type resolution."],
        )

        # Imports
        for m in _ES_IMPORT_RE.finditer(source):
            module = m.group("module")
            level = 1 if module.startswith(".") else 0
            result.imports.append(
                ImportInfo(
                    file_path=file_path,
                    module=module,
                    names=_clean_names(m.group("names")),
                    level=level,
                    line=_line_number(source, m.start()),
                )
            )
        for m in _CJS_REQUIRE_RE.finditer(source):
            module = m.group("module")
            level = 1 if module.startswith(".") else 0
            result.imports.append(
                ImportInfo(
                    file_path=file_path,
                    module=module,
                    names=_clean_names(m.group("names")),
                    level=level,
                    line=_line_number(source, m.start()),
                )
            )

        # Classes
        for m in _CLASS_RE.finditer(source):
            line = _line_number(source, m.start())
            bases = [m.group("base")] if m.group("base") else []
            result.symbols.append(
                SymbolInfo(
                    name=m.group("name"),
                    qualified_name=m.group("name"),
                    kind="class",
                    file_path=file_path,
                    start_line=line,
                    end_line=line,
                    bases=bases,
                    exported=bool(m.group("export")),
                )
            )

        # Functions and arrow functions
        for pattern in (_FUNC_RE, _ARROW_FUNC_RE):
            for m in pattern.finditer(source):
                line = _line_number(source, m.start())
                params = [p.strip().split(":")[0].split("=")[0].strip() for p in m.group("params").split(",") if p.strip()]
                result.symbols.append(
                    SymbolInfo(
                        name=m.group("name"),
                        qualified_name=m.group("name"),
                        kind="function",
                        file_path=file_path,
                        start_line=line,
                        end_line=line,
                        parameters=params,
                        exported=bool(m.group("export")),
                    )
                )

        # Routes
        for m in _ROUTE_RE.finditer(source):
            result.routes.append(
                RouteInfo(
                    file_path=file_path,
                    method=m.group("method").upper(),
                    path=m.group("path"),
                    handler=m.group("handler"),
                    line=_line_number(source, m.start()),
                )
            )

        # Dynamic imports
        for m in _DYNAMIC_IMPORT_RE.finditer(source):
            result.dynamic_signals.append(
                DynamicSignal(
                    file_path=file_path,
                    kind="dynamic_import",
                    detail="dynamic import(...)",
                    line=_line_number(source, m.start()),
                )
            )

        # Calls (attributed to nearest preceding top-level symbol or <module>)
        sym_lines = sorted(
            [(s.start_line, s.qualified_name) for s in result.symbols],
            key=lambda x: x[0],
        )
        defined_names = {s.name for s in result.symbols}
        for m in _CALL_RE.finditer(source):
            callee = m.group("callee")
            head = callee.split(".")[0]
            if head in _NON_CALL_KEYWORDS:
                continue
            line = _line_number(source, m.start())
            # Skip function declaration header itself
            if callee in defined_names and any(sl == line and sn == callee for sl, sn in sym_lines):
                continue
            caller = "<module>"
            for sl, sn in sym_lines:
                if sl <= line:
                    caller = sn
                else:
                    break
            result.calls.append(
                CallInfo(
                    file_path=file_path,
                    caller=caller,
                    callee=callee,
                    line=line,
                    provenance="static_structural",
                )
            )

        return result
