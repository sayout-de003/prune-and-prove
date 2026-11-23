
from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from engine.repository.file_classifier import (
    FileClassification,
    FileClassifier,
)


@dataclass
class ScanError:
    path: str
    operation: str
    error: str


@dataclass
class RepositoryScan:
    root: str
    files: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    total_discovered: int = 0
    total_analyzed: int = 0
    total_inventory_only: int = 0
    total_skipped: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RepositoryScanner:
    """
    Read-only repository inventory scanner.

    The scanner records metadata and classification results.
    It does not execute project code or read file contents.
    """

    def __init__(self, classifier: FileClassifier):
        self.classifier = classifier

    def scan(
        self,
        root: str | Path,
        include_skipped: bool = False,
    ) -> RepositoryScan:

        root_path = Path(root).resolve(strict=True)

        if not root_path.is_dir():
            raise NotADirectoryError(str(root_path))

        result = RepositoryScan(root=str(root_path))

        def on_walk_error(error: OSError) -> None:
            result.errors.append(
                asdict(
                    ScanError(
                        path=str(getattr(error, "filename", "") or root_path),
                        operation="walk",
                        error=str(error),
                    )
                )
            )

        for current_root, directories, filenames in os.walk(
            root_path,
            topdown=True,
            followlinks=False,
            onerror=on_walk_error,
        ):
            current_path = Path(current_root)

            retained_directories = []

            for directory in sorted(directories):
                candidate = current_path / directory

                if candidate.is_symlink():
                    continue

                relative = candidate.relative_to(root_path).as_posix()

                # Reuse the classifier's exclusion policy.
                excluded = self.classifier._is_excluded_directory(
                    relative + "/placeholder"
                )

                if excluded:
                    continue

                retained_directories.append(directory)

            directories[:] = retained_directories

            for filename in sorted(filenames):
                candidate = current_path / filename

                if candidate.is_symlink():
                    continue

                relative = candidate.relative_to(root_path).as_posix()

                classification = self.classifier.classify(
                    candidate,
                    root_path,
                )

                try:
                    stat = candidate.stat(follow_symlinks=False)

                    metadata = {
                        "size_bytes": stat.st_size,
                        "modified_time_ns": stat.st_mtime_ns,
                    }

                except OSError as error:
                    metadata = {
                        "size_bytes": None,
                        "modified_time_ns": None,
                    }

                    result.errors.append(
                        asdict(
                            ScanError(
                                path=relative,
                                operation="stat",
                                error=str(error),
                            )
                        )
                    )

                result.total_discovered += 1

                if classification.status == "analyze":
                    result.total_analyzed += 1

                elif classification.status == "inventory_only":
                    result.total_inventory_only += 1

                else:
                    result.total_skipped += 1

                if classification.status == "skip" and not include_skipped:
                    continue

                entry = {
                    "path": relative,
                    "language": classification.language,
                    "parser": classification.parser,
                    "categories": list(classification.categories),
                    "status": classification.status,
                    "reasons": list(classification.reasons),
                    **metadata,
                }

                result.files.append(entry)

        result.files.sort(key=lambda item: item["path"])

        return result
