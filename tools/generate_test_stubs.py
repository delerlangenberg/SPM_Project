#generate_test_stubs.py
import os
from pathlib import Path

# Base directory of the project
base_dir = Path("D:/Documents/Project/SPM")

# Define target modules to scaffold tests for
target_modules = [
    "core/scan/modes",
    "core/z_control",
    "interface/layout",
    "ai"
]

# Define the test directory
tests_dir = base_dir / "tests"
tests_dir.mkdir(parents=True, exist_ok=True)

# Template for dummy test
def generate_test_stub(module_path, functions):
    class_name = module_path.stem.title().replace("_", "") + "Test"
    function_tests = "\n".join([f"    def test_{f}(self):\n        assert False  # TODO: implement\n" for f in functions])
    return f"""
import pytest
from {'.'.join(module_path.parts[:-1])}.{module_path.stem} import *

class Test{class_name}:
{function_tests}
""".strip()

# Identify .py files and define stubs
test_files = {}
for module in target_modules:
    module_path = base_dir / module
    if not module_path.exists():
        continue

    for py_file in module_path.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        # One dummy function per file
        test_stub = generate_test_stub(py_file.relative_to(base_dir), ["dummy_function"])
        test_file_path = tests_dir / f"test_{py_file.stem}.py"
        test_files[test_file_path] = test_stub

# Write test files
for path, content in test_files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created test: {path}")
