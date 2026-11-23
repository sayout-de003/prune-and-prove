from __future__ import annotations

import re

from engine.parsers.javascript_parser import JavaScriptParser, _line_number
from engine.parsers.parser_registry import ParseResult, SymbolInfo


_INTERFACE_RE = re.compile(
    r"""^\s*(?P<export>export\s+)?interface\s+(?P<name>[A-Za-z_$][\w$]*)(?:\s+extends\s+(?P<base>[A-Za-z_$][\w$.]*))?""",
    re.MULTILINE,
)
_TYPE_ALIAS_RE = re.compile(
    r"""^\s*(?P<export>export\s+)?type\s+(?P<name>[A-Za-z_$][\w$]*)\s*=""",
    re.MULTILINE,
)


class TypeScriptParser(JavaScriptParser):
    """Structural TypeScript/TSX parser extending JavaScriptParser with interface and type definitions."""

    name = "ts_structural"
    default_language = "typescript"

    def parse(self, file_path: str, source: str) -> ParseResult:
        result = super().parse(file_path, source)
        result.parser_name = self.name
        result.language = self.default_language

        for m in _INTERFACE_RE.finditer(source):
            line = _line_number(source, m.start())
            bases = [m.group("base")] if m.group("base") else []
            result.symbols.append(
                SymbolInfo(
                    name=m.group("name"),
                    qualified_name=m.group("name"),
                    kind="interface",
                    file_path=file_path,
                    start_line=line,
                    end_line=line,
                    bases=bases,
                    exported=bool(m.group("export")),
                )
            )

        for m in _TYPE_ALIAS_RE.finditer(source):
            line = _line_number(source, m.start())
            result.symbols.append(
                SymbolInfo(
                    name=m.group("name"),
                    qualified_name=m.group("name"),
                    kind="type",
                    file_path=file_path,
                    start_line=line,
                    end_line=line,
                    exported=bool(m.group("export")),
                )
            )

        return result
