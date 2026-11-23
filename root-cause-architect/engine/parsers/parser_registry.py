from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class SymbolInfo:
    name: str
    qualified_name: str
    kind: str  # "function", "method", "class", "interface", "type"
    file_path: str
    start_line: int
    end_line: int
    parameters: list[str] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    exported: bool = True


@dataclass
class ImportInfo:
    file_path: str
    module: str
    names: list[str] = field(default_factory=list)
    alias: str | None = None
    level: int = 0  # >0 for relative imports
    line: int = 0


@dataclass
class CallInfo:
    file_path: str
    caller: str  # qualified symbol name or "<module>"
    callee: str  # raw call target expression (e.g., "validate", "service.charge")
    line: int = 0
    provenance: str = "static_ast"  # "static_ast" | "static_structural"


@dataclass
class RouteInfo:
    file_path: str
    method: str
    path: str
    handler: str
    line: int = 0


@dataclass
class DynamicSignal:
    file_path: str
    kind: str  # "reflection", "dynamic_import", "decorator_registration", "signal_receiver"
    detail: str
    line: int = 0


@dataclass
class ParseResult:
    file_path: str
    language: str | None
    parser_name: str
    provenance: str  # "static_ast" | "static_structural" | "fallback"
    symbols: list[SymbolInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    calls: list[CallInfo] = field(default_factory=list)
    routes: list[RouteInfo] = field(default_factory=list)
    dynamic_signals: list[DynamicSignal] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceParser(Protocol):
    name: str

    def parse(self, file_path: str, source: str) -> ParseResult: ...


class ParserRegistry:
    """Dispatches source files to the appropriate language parser with honest fallback."""

    def __init__(self) -> None:
        from engine.parsers.fallback_parser import FallbackParser
        from engine.parsers.javascript_parser import JavaScriptParser
        from engine.parsers.python_parser import PythonParser
        from engine.parsers.typescript_parser import TypeScriptParser

        self._python = PythonParser()
        self._js = JavaScriptParser()
        self._ts = TypeScriptParser()
        self._fallback = FallbackParser()

        self._by_language: dict[str, SourceParser] = {
            "python": self._python,
            "javascript": self._js,
            "javascript_react": self._js,
            "typescript": self._ts,
            "typescript_react": self._ts,
        }

    def get_parser(self, language: str | None) -> SourceParser:
        if language and language in self._by_language:
            return self._by_language[language]
        return self._fallback

    def parse_file(
        self,
        root: str | Path,
        relative_path: str,
        language: str | None,
    ) -> ParseResult:
        parser = self.get_parser(language)
        full_path = Path(root) / relative_path
        try:
            source = full_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return ParseResult(
                file_path=relative_path,
                language=language,
                parser_name=parser.name,
                provenance="fallback",
                errors=[f"Failed to read file: {exc}"],
            )
        result = parser.parse(relative_path, source)
        result.language = language
        return result

    @property
    def supported_languages(self) -> list[str]:
        return sorted(self._by_language.keys())
