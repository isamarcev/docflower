"""Logic for generating next version labels.

Kept as plain functions (no DB access) so they can be unit-tested without fixtures.
The label scheme matches the wireframes:

* ``main``-style branches:  ``v1.0``, ``v1.1``, ..., ``v2.0`` (minor bumps by default,
  callers can request a major bump).
* draft branches:           ``d1.0``, ``d1.1``, ``d1.2``, ...

If a label is unparseable, we fall back to appending a numeric suffix so we never
fail to produce *some* unique-looking label.
"""

from __future__ import annotations

import re

_PATTERN = re.compile(r"^(?P<prefix>[a-zA-Z]+)(?P<major>\d+)\.(?P<minor>\d+)$")


def next_minor(label: str) -> str:
    """v3.2 -> v3.3. d1.0 -> d1.1."""
    m = _PATTERN.match(label)
    if not m:
        return f"{label}.1"
    return f"{m['prefix']}{m['major']}.{int(m['minor']) + 1}"


def next_major(label: str) -> str:
    """v3.2 -> v4.0."""
    m = _PATTERN.match(label)
    if not m:
        return f"{label}.next"
    return f"{m['prefix']}{int(m['major']) + 1}.0"


def initial_label_for_branch(branch_name: str) -> str:
    """First label inside a new branch.

    main -> v1.0; anything else -> d1.0 (treated as a draft series).
    """
    return "v1.0" if branch_name == "main" else "d1.0"
