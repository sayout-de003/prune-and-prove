# Troubleshooting

### `ModuleNotFoundError: No module named 'engine'`
Run commands from inside `root-cause-architect/` or invoke `python3 /path/to/root-cause-architect/scripts/analyze.py ...` (the CLI scripts automatically add the package root to `sys.path`).

### `python3 -m unittest discover -s tests` runs 0 tests
Pass `-t .` or explicit test files because `tests/` does not require `__init__.py`:
```bash
python3 -m unittest tests/unit/test_file_classifier.py tests/unit/test_detectors.py tests/parsers/test_parsers.py tests/graph/test_graph.py tests/integration/test_cli.py -v
```

### Framework not detected
`FrameworkDetector` requires at least 2 evidence signals AND framework-specific dependency/config evidence (`package.json` alone does not trigger React/Express). Run `scripts/analyze.py map <repo> --json` to inspect detected manifests and dependencies.

### `impact` exits with code 2
The target file path or symbol name did not match any node in the graph. Pass the repository-relative POSIX path (e.g., `app/services/payment.py`) or exact symbol name.
