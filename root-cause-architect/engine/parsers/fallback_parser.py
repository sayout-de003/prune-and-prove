from __future__ import annotations

from engine.parsers.parser_registry import ParseResult


class FallbackParser:
    """Retains unsupported files in the inventory and reports parser limitations honestly."""

    name = "fallback"

    def parse(self, file_path: str, source: str) -> ParseResult:
        return ParseResult(
            file_path=file_path,
            language=None,
            parser_name=self.name,
            provenance="fallback",
            limitations=[
                "No native AST or structural parser implemented for this language; file retained in inventory only."
            ],
        )
