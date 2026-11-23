
import tempfile
import unittest
from pathlib import Path

from engine.repository.file_classifier import FileClassifier


class FileClassifierTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.languages = {
            "languages": {
                "python": {
                    "extensions": [".py"],
                    "parser": "python_ast",
                },
                "typescript": {
                    "extensions": [".ts"],
                    "parser": "typescript_compiler_api",
                },
            },
            "file_categories": {
                "test": {
                    "directory_names": ["tests", "test"],
                    "filename_patterns": ["test_*.py", "*.test.ts"],
                },
                "migration": {
                    "directory_names": ["migrations", "migration"],
                },
                "configuration": {
                    "filenames": ["pyproject.toml", "package.json"],
                },
                "generated": {
                    "filename_patterns": ["*.generated.*"],
                },
            },
        }

        self.exclusions = {
            "scan_policy": {
                "max_file_size_bytes": 2097152,
            },
            "directories": {
                "exact": [".git", "node_modules", "__pycache__"],
            },
            "files": {
                "exact": [".DS_Store"],
                "extensions": [".pyc", ".png"],
            },
            "sensitive_files": {
                "exact": [".env", ".env.production"],
                "policy": {
                    "action": "skip_content",
                },
            },
        }

        self.classifier = FileClassifier(
            self.languages,
            self.exclusions,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_file(self, relative_path, content="sample"):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_python_source_detection(self):
        path = self.create_file("app/main.py")

        result = self.classifier.classify(path, self.root)

        self.assertEqual(result.language, "python")
        self.assertEqual(result.parser, "python_ast")
        self.assertEqual(result.status, "analyze")

    def test_typescript_detection(self):
        path = self.create_file("src/app.ts")

        result = self.classifier.classify(path, self.root)

        self.assertEqual(result.language, "typescript")
        self.assertEqual(result.status, "analyze")

    def test_test_file_is_preserved(self):
        path = self.create_file("tests/test_auth.py")

        result = self.classifier.classify(path, self.root)

        self.assertIn("test", result.categories)
        self.assertTrue(result.analyzable)

    def test_migration_is_preserved(self):
        path = self.create_file(
            "app/migrations/0001_initial.py"
        )

        result = self.classifier.classify(path, self.root)

        self.assertIn("migration", result.categories)
        self.assertTrue(result.analyzable)

    def test_sensitive_file_is_inventory_only(self):
        path = self.create_file(".env", "SECRET=do-not-expose")

        result = self.classifier.classify(path, self.root)

        self.assertEqual(result.status, "inventory_only")
        self.assertIn("sensitive", result.categories)

    def test_excluded_directory_is_skipped(self):
        path = self.create_file("node_modules/example/index.js")

        result = self.classifier.classify(path, self.root)

        self.assertEqual(result.status, "skip")
        self.assertIn("excluded directory", result.reasons[0])

    def test_binary_extension_is_skipped(self):
        path = self.create_file("assets/image.png")

        result = self.classifier.classify(path, self.root)

        self.assertEqual(result.status, "skip")

    def test_unknown_extension_is_preserved(self):
        path = self.create_file("data/custom.unknownext")

        result = self.classifier.classify(path, self.root)

        self.assertIsNone(result.language)
        self.assertEqual(result.status, "analyze")
        self.assertIn("source", result.categories)

    def test_generated_file_is_flagged(self):
        path = self.create_file("src/schema.generated.py")

        result = self.classifier.classify(path, self.root)

        self.assertIn("generated", result.categories)
        self.assertTrue(result.analyzable)

    def test_oversized_file_is_inventory_only(self):
        path = self.create_file("large.py", "x" * 100)

        self.exclusions["scan_policy"]["max_file_size_bytes"] = 10

        classifier = FileClassifier(
            self.languages,
            self.exclusions,
        )

        result = classifier.classify(path, self.root)

        self.assertEqual(result.status, "inventory_only")
        self.assertIn("oversized", result.categories)

    def test_file_outside_root_is_rejected(self):
        outside = self.root.parent / "outside.py"
        outside.write_text("print('outside')", encoding="utf-8")

        try:
            result = self.classifier.classify(outside, self.root)

            self.assertEqual(result.status, "skip")
            self.assertIn("outside repository root", result.reasons[0])
        finally:
            outside.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

