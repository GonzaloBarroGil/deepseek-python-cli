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
        """__init__.py must export DeepSeekCLI and the entry_point alias."""
        import deepseek_cli
        assert hasattr(deepseek_cli, "DeepSeekCLI"), (
            "deepseek_cli must export 'DeepSeekCLI' class"
        )
        assert hasattr(deepseek_cli, "entry_point"), (
            "deepseek_cli must export 'entry_point' function"
        )
        assert callable(deepseek_cli.entry_point)

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
        """Package version must match the spec version (1.2.0)."""
        version = self.data["project"]["version"]
        assert version == "1.2.0", (
            f"pyproject.toml version {version} != spec version 1.2.0"
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


# ---------------------------------------------------------------------------
# TestPyPIReadiness — validates PyPI publication metadata per v1.2.0 spec
# ---------------------------------------------------------------------------
class TestPyPIReadiness:
    """Validate pyproject.toml and Makefile are ready for PyPI publication."""

    @pytest.fixture(autouse=True)
    def load_pyproject(self):
        """Load and parse pyproject.toml once per test."""
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.is_file():
            pytest.skip("pyproject.toml does not exist yet")
        with open(pyproject_path, "rb") as f:
            self.data = tomllib.load(f)

    def test_pyproject_has_urls(self):
        """Spec v1.2.0 pypi: project.urls must have Homepage, Repository, Bug Tracker."""
        urls = self.data["project"].get("urls", {})
        assert "Homepage" in urls, "project.urls must contain 'Homepage'"
        assert "Repository" in urls, "project.urls must contain 'Repository'"
        assert "Bug Tracker" in urls, "project.urls must contain 'Bug Tracker'"
        assert urls["Homepage"].startswith("https://"), (
            "Homepage must be a valid URL"
        )
        assert urls["Repository"].startswith("https://"), (
            "Repository must be a valid URL"
        )

    def test_pyproject_has_classifiers(self):
        """Spec v1.2.0 pypi: at least 3 Trove classifiers required."""
        classifiers = self.data["project"].get("classifiers", [])
        assert len(classifiers) >= 3, (
            f"Expected >= 3 classifiers, got {len(classifiers)}"
        )
        # Must include license classifier
        license_classifiers = [c for c in classifiers if c.startswith("License ::")]
        assert len(license_classifiers) >= 1, (
            "At least one License classifier is required"
        )
        # Must include Python version classifiers
        python_classifiers = [c for c in classifiers if "Python :: 3" in c]
        assert len(python_classifiers) >= 1, (
            "At least one Programming Language :: Python :: 3 classifier is required"
        )

    def test_pyproject_has_keywords(self):
        """Spec v1.2.0 pypi: keywords field must be non-empty."""
        keywords = self.data["project"].get("keywords", [])
        assert len(keywords) >= 3, (
            f"Expected >= 3 keywords, got {len(keywords)}: {keywords}"
        )

    def test_pyproject_has_readme(self):
        """Spec v1.2.0 pypi: readme field must point to README.md."""
        readme = self.data["project"].get("readme", "")
        assert readme == "README.md", (
            f"readme must be 'README.md', got '{readme}'"
        )
        assert Path("README.md").is_file(), (
            "README.md must exist at project root"
        )

    def test_description_content_type(self):
        """Spec v1.2.0 pypi: description-content-type should be text/markdown."""
        content_type = self.data["project"].get("description-content-type", "")
        assert content_type == "text/markdown", (
            f"description-content-type must be 'text/markdown', got '{content_type}'"
        )

    def test_makefile_has_build_target(self):
        """Spec v1.2.0 pypi: Makefile must have a build target."""
        makefile = Path("Makefile")
        assert makefile.is_file(), "Makefile must exist"
        content = makefile.read_text()
        assert "build:" in content, (
            "Makefile must contain a 'build:' target"
        )
        assert "python -m build" in content or "pyproject-build" in content, (
            "Makefile build target must invoke 'python -m build'"
        )

    def test_makefile_has_publish_target(self):
        """Spec v1.2.0 pypi: Makefile must have a publish target."""
        makefile = Path("Makefile")
        assert makefile.is_file(), "Makefile must exist"
        content = makefile.read_text()
        assert "publish:" in content, (
            "Makefile must contain a 'publish:' target"
        )
        assert "twine" in content, (
            "Makefile publish target must reference twine"
        )

    def test_version_consistency(self):
        """Spec v1.2.0: pyproject.toml, __init__.py, and spec must agree on version."""
        # pyproject.toml version
        pyproject_version = self.data["project"]["version"]

        # __init__.py version
        init_path = Path("src/deepseek_cli/__init__.py")
        assert init_path.is_file(), "__init__.py must exist"
        init_content = init_path.read_text()
        import re
        version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_content)
        assert version_match, "__init__.py must define __version__"
        init_version = version_match.group(1)

        assert pyproject_version == init_version, (
            f"Version mismatch: pyproject.toml={pyproject_version}, "
            f"__init__.py={init_version}"
        )
        assert pyproject_version == "1.2.0", (
            f"Both must be 1.2.0, got {pyproject_version}"
        )
