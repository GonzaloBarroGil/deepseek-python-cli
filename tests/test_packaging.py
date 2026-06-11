"""BDD tests for the packaging section of spec/deepseek-cli/v1.1.0.yml."""

import importlib
import os
import tomllib
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# TestPackageStructure — validates the package directory exists per spec
# ---------------------------------------------------------------------------
class TestPackageStructure:
    """Validate physical package structure matches spec packaging requirements."""

    def test_package_directory_exists(self):
        """Spec: package_name is deepseek-cli, implemented as src/deepseek_cli/."""
        pkg_dir = Path("src/deepseek_cli")
        assert pkg_dir.is_dir(), f"Expected {pkg_dir} to be a directory"

    def test_init_py_exists(self):
        """Package must have __init__.py for importability."""
        init_file = Path("src/deepseek_cli/__init__.py")
        assert init_file.is_file(), f"Expected {init_file} to exist"

    def test_main_py_exists(self):
        """Entry point module (main.py) must exist per spec."""
        main_file = Path("src/deepseek_cli/main.py")
        assert main_file.is_file(), f"Expected {main_file} to exist"

    def test_py_typed_exists(self):
        """PEP 561 marker for typed packages."""
        typed_file = Path("src/deepseek_cli/py.typed")
        assert typed_file.is_file(), f"Expected {typed_file} to exist"


# ---------------------------------------------------------------------------
# TestEntryPointExports — validates the module exports match spec
# ---------------------------------------------------------------------------
class TestEntryPointExports:
    """Validate that the package exports the expected symbols."""

    def test_init_exports_main_function(self):
        """__init__.py must export a main function."""
        import deepseek_cli
        assert hasattr(deepseek_cli, "main"), (
            "deepseek_cli must export 'main' function"
        )
        assert callable(deepseek_cli.main)

    def test_main_module_has_main_function(self):
        """deepseek_cli.main must define a callable main()."""
        from deepseek_cli import main as main_module
        assert hasattr(main_module, "main"), (
            "deepseek_cli.main must define 'main' function"
        )
        assert callable(main_module.main)


# ---------------------------------------------------------------------------
# TestPyprojectToml — validates pyproject.toml against packaging spec
# ---------------------------------------------------------------------------
class TestPyprojectToml:
    """Validate pyproject.toml matches the packaging section of the spec."""

    @pytest.fixture(autouse=True)
    def load_pyproject(self):
        """Load and parse pyproject.toml once per test."""
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.is_file():
            pytest.skip("pyproject.toml does not exist yet")
        with open(pyproject_path, "rb") as f:
            self.data = tomllib.load(f)

    def test_pyproject_toml_exists(self):
        """Spec requires pyproject.toml at project root."""
        assert Path("pyproject.toml").is_file(), (
            "pyproject.toml must exist at project root"
        )

    def test_build_system_is_setuptools(self):
        """Spec: build_system is setuptools."""
        build_backend = self.data["build-system"]["build-backend"]
        assert build_backend == "setuptools.build_meta", (
            f"build-backend must be setuptools.build_meta, got {build_backend}"
        )

    def test_console_script_entry_point(self):
        """Spec: console_script deepseek-cli → deepseek_cli.main:main."""
        scripts = self.data["project"]["scripts"]
        assert "deepseek-cli" in scripts, (
            "console_script 'deepseek-cli' must be defined"
        )
        assert scripts["deepseek-cli"] == "deepseek_cli.main:main", (
            f"Entry point mismatch: {scripts['deepseek-cli']}"
        )

    def test_version_matches_spec(self):
        """Package version must match the spec version (1.1.0)."""
        version = self.data["project"]["version"]
        assert version == "1.1.0", (
            f"pyproject.toml version {version} != spec version 1.1.0"
        )

    def test_python_minimum_3_9(self):
        """Spec: python_minimum is 3.9."""
        requires_python = self.data["project"]["requires-python"]
        assert requires_python == ">=3.9", (
            f"requires-python must be >=3.9, got {requires_python}"
        )


# ---------------------------------------------------------------------------
# TestOldFileRemoved — validates migration from single-file to package
# ---------------------------------------------------------------------------
class TestOldFileRemoved:
    """Ensure the old single-file module has been removed."""

    def test_old_single_file_does_not_exist(self):
        """After packaging, src/deepseek_cli.py must NOT exist."""
        old_file = Path("src/deepseek_cli.py")
        assert not old_file.exists(), (
            "src/deepseek_cli.py must be removed after packaging migration"
        )