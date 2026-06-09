#!/usr/bin/env python3
"""Validate a spec YAML file against the CONSTITUTION Section V requirements."""
import sys
import os
import yaml

SPEC_FILE = sys.argv[1] if len(sys.argv) > 1 else "spec/deepseek-cli/v1.0.0.yml"
REQUIRED_KEYS = ["name", "version", "description", "inputs", "outputs", "behavior", "examples"]


def main():
    if not os.path.exists(SPEC_FILE):
        print(f"FAIL: spec file not found: {SPEC_FILE}")
        sys.exit(1)

    with open(SPEC_FILE) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        print(f"FAIL: spec file is not a YAML mapping")
        sys.exit(1)

    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        print(f"FAIL: missing required keys: {missing}")
        sys.exit(1)

    basename = os.path.basename(SPEC_FILE)
    version_in_file = str(data["version"])
    version_in_name = basename.replace(".yml", "").lstrip("v")
    if version_in_file != version_in_name:
        print(
            f"FAIL: YAML version '{version_in_file}' != filename version '{version_in_name}'"
        )
        sys.exit(1)

    print(f"OK: {SPEC_FILE} is valid (version {version_in_file})")


if __name__ == "__main__":
    main()