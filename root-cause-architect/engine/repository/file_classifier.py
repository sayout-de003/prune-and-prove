
from __future__ import annotations

import fnmatch
import mimetypes
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FileClassification:
    path: str
    language: str | None
    categories: tuple[str, ...]
    status: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    parser: str | None = None

    @property
    def analyzable(self) -> bool:
        return self.status == "analyze"

    @property
    def inventoried(self) -> bool:
        return self.status in {"analyze", "inventory_only"}


class FileClassifier:
    """
    Classifies repository files using language and exclusion configuration.

    Classification is read-only. It never modifies repository files.

    Status values:
        analyze:
            Eligible for source or configuration analysis.

        inventory_only:
            Record file metadata but do not read its content.

        skip:
            Excluded from normal repository processing.
    """

    def __init__(
        self,
        languages_config: dict[str, Any],
        exclusions_config: dict[str, Any],
    ) -> None:
        self.languages_config = languages_config
        self.exclusions_config = exclusions_config

        self._language_extensions = self._build_extension_map()
        self._language_filenames = self._build_filename_map()

    def _build_extension_map(self) -> dict[str, tuple[str, str | None]]:
        result: dict[str, tuple[str, str | None]] = {}

        languages = self.languages_config.get("languages", {})

        for language, definition in languages.items():
            parser = definition.get("parser")

            for extension in definition.get("extensions", []):
                result[extension.lower()] = (language, parser)

        return result

    def _build_filename_map(self) -> dict[str, tuple[str, str | None]]:
        result: dict[str, tuple[str, str | None]] = {}

        languages = self.languages_config.get("languages", {})

        for language, definition in languages.items():
            parser = definition.get("parser")

            for filename in definition.get("filenames", []):
                result[filename.lower()] = (language, parser)

        return result

    @staticmethod
    def _matches_pattern(path: str, patterns: list[str]) -> bool:
        normalized = path.replace("\\", "/")

        for pattern in patterns:
            if fnmatch.fnmatch(normalized, pattern):
                return True

            if fnmatch.fnmatch(Path(normalized).name, pattern):
                return True

        return False

    @staticmethod
    def _directory_names(relative_path: str) -> set[str]:
        return {
            part
            for part in Path(relative_path).parts[:-1]
        }

    def _is_excluded_directory(self, relative_path: str) -> str | None:
        excluded = set(
            self.exclusions_config
            .get("directories", {})
            .get("exact", [])
        )

        for directory in self._directory_names(relative_path):
            if directory in excluded:
                return directory

        return None

    def _is_excluded_file(self, filename: str) -> str | None:
        file_config = self.exclusions_config.get("files", {})

        exact = {
            name.lower()
            for name in file_config.get("exact", [])
        }

        if filename.lower() in exact:
            return f"excluded filename: {filename}"

        extensions = {
            extension.lower()
            for extension in file_config.get("extensions", [])
        }

        if Path(filename).suffix.lower() in extensions:
            return f"excluded binary/generated extension: {Path(filename).suffix}"

        return None

    def _is_sensitive_file(self, filename: str) -> bool:
        sensitive = self.exclusions_config.get("sensitive_files", {})
        exact = {
            name.lower()
            for name in sensitive.get("exact", [])
        }

        return filename.lower() in exact

    def _detect_language(
        self,
        relative_path: str,
    ) -> tuple[str | None, str | None]:
        filename = Path(relative_path).name.lower()

        if filename in self._language_filenames:
            return self._language_filenames[filename]

        extension = Path(filename).suffix.lower()

        return self._language_extensions.get(extension, (None, None))

    def _classify_categories(
        self,
        relative_path: str,
    ) -> tuple[str, ...]:
        categories: set[str] = set()

        config = self.languages_config.get("file_categories", {})
        filename = Path(relative_path).name
        directories = self._directory_names(relative_path)

        for category, rules in config.items():
            directory_names = set(rules.get("directory_names", []))

            if directories.intersection(directory_names):
                categories.add(category)

            filenames = rules.get("filenames", [])

            if filename in filenames:
                categories.add(category)

            extensions = {
                extension.lower()
                for extension in rules.get("extensions", [])
            }

            if Path(filename).suffix.lower() in extensions:
                categories.add(category)

            patterns = rules.get("filename_patterns", [])

            if self._matches_pattern(relative_path, patterns):
                categories.add(category)

        if not categories:
            categories.add("source")

        return tuple(sorted(categories))

    def _is_generated(self, relative_path: str) -> bool:
        rules = (
            self.languages_config
            .get("file_categories", {})
            .get("generated", {})
        )

        return self._matches_pattern(
            relative_path,
            rules.get("filename_patterns", []),
        )

    def classify(self, path: str | Path, root: str | Path) -> FileClassification:
        root_path = Path(root).resolve()
        candidate = Path(path)

        if not candidate.is_absolute():
            candidate = root_path / candidate

        try:
            resolved = candidate.resolve(strict=False)
            relative = resolved.relative_to(root_path).as_posix()
        except (ValueError, OSError):
            return FileClassification(
                path=str(path),
                language=None,
                categories=(),
                status="skip",
                reasons=("path is outside repository root",),
            )

        if candidate.is_symlink():
            return FileClassification(
                path=relative,
                language=None,
                categories=(),
                status="skip",
                reasons=("symbolic links are not followed",),
            )

        excluded_directory = self._is_excluded_directory(relative)

        if excluded_directory:
            return FileClassification(
                path=relative,
                language=None,
                categories=(),
                status="skip",
                reasons=(f"excluded directory: {excluded_directory}",),
            )

        filename = candidate.name

        if self._is_sensitive_file(filename):
            return FileClassification(
                path=relative,
                language=None,
                categories=("sensitive",),
                status="inventory_only",
                reasons=("sensitive file: content access prohibited",),
            )

        excluded_file = self._is_excluded_file(filename)

        if excluded_file:
            return FileClassification(
                path=relative,
                language=None,
                categories=(),
                status="skip",
                reasons=(excluded_file,),
            )

        if not candidate.exists() or not candidate.is_file():
            return FileClassification(
                path=relative,
                language=None,
                categories=(),
                status="skip",
                reasons=("not a regular file",),
            )

        max_size = (
            self.exclusions_config
            .get("scan_policy", {})
            .get("max_file_size_bytes", 2097152)
        )

        try:
            size = candidate.stat().st_size
        except OSError:
            return FileClassification(
                path=relative,
                language=None,
                categories=(),
                status="inventory_only",
                reasons=("file metadata could not be read",),
            )

        if size > max_size:
            return FileClassification(
                path=relative,
                language=None,
                categories=("oversized",),
                status="inventory_only",
                reasons=(f"file exceeds size limit: {size} bytes",),
            )

        language, parser = self._detect_language(relative)
        categories = self._classify_categories(relative)

        if self._is_generated(relative):
            categories = tuple(sorted(set(categories) | {"generated"}))

        reasons = []

        if language:
            reasons.append(f"recognized language: {language}")
        else:
            reasons.append("unknown language; retained in inventory")

        if "test" in categories:
            reasons.append("test file retained for verification")

        if "migration" in categories:
            reasons.append("migration retained for database analysis")

        if "configuration" in categories:
            reasons.append("configuration retained for architecture analysis")

        if "generated" in categories:
            reasons.append("generated file retained but flagged")

        return FileClassification(
            path=relative,
            language=language,
            categories=categories,
            status="analyze",
            reasons=tuple(reasons),
            parser=parser,
        )
