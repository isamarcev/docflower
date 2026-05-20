#!/usr/bin/env python3
"""Bump the project version everywhere it is declared.

Called by semantic-release via the @semantic-release/exec plugin.
Updates: pyproject.toml, package.json, src/docflow/__init__.py.
"""

from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def update_pyproject(version: str) -> bool:
    path = os.path.join(ROOT, "pyproject.toml")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    project_match = re.search(r"\[project\].*?(\n\[|\Z)", content, flags=re.DOTALL)
    if not project_match:
        print("Error: [project] section not found in pyproject.toml")
        return False

    section = project_match.group(0)

    def replace(match: re.Match[str]) -> str:
        return match.group(1) + version + match.group(2)

    updated_section = re.sub(r'(version\s*=\s*")[^"]+(")', replace, section)
    if "version" not in section:
        # No version field — insert one after [project] header.
        updated_section = section.replace("[project]", f'[project]\nversion = "{version}"', 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(section, updated_section))
    return True


def update_package_json(version: str) -> bool:
    path = os.path.join(ROOT, "package.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = version
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return True


def update_init(version: str) -> bool:
    path = os.path.join(ROOT, "src", "docflow", "__init__.py")
    with open(path, encoding="utf-8") as f:
        content = f.read()

    if "__version__" in content:
        updated = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{version}"', content)
    else:
        updated = (content.rstrip() + f'\n\n__version__ = "{version}"\n').lstrip("\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)
    return True


def main(version: str) -> int:
    ok = all([update_pyproject(version), update_package_json(version), update_init(version)])
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: update_version.py <new-version>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
