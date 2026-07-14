"""Split ``langgraph.*`` imports between this CRM package and the installed library.

This repository ships an application package under ``langgraph/`` (graphs, nodes,
state, …). The official orchestration library is also named ``langgraph``.

Rule:
- ``langgraph.graphs|state|nodes|tools|prompts|engine|_shadow_fix`` → CRM package
- any other ``langgraph.*`` (e.g. ``langgraph.graph``, ``langgraph.runtime``)
  → installed distribution in site-packages

Note: CRM uses ``engine/`` instead of ``runtime/`` to avoid colliding with the
official library's ``langgraph.runtime`` module.
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Sequence


OUR_SUBPACKAGES = frozenset(
    {
        "graphs",
        "state",
        "nodes",
        "tools",
        "prompts",
        "engine",
        "_shadow_fix",
    }
)

_THIS_ROOT = Path(__file__).resolve().parent
_FINDER_INSTALLED = False
_DIST_ROOT: Path | None = None


def installed_dist_root() -> Path:
    global _DIST_ROOT
    if _DIST_ROOT is not None:
        return _DIST_ROOT
    for entry in sys.path:
        if not entry:
            continue
        pkg = Path(entry) / "langgraph"
        try:
            resolved = pkg.resolve()
            if not pkg.is_dir() or resolved == _THIS_ROOT.resolve():
                continue
        except OSError:
            continue
        if (
            (pkg / "graph").exists()
            or (pkg / "graph.py").exists()
            or (pkg / "constants.py").exists()
        ):
            _DIST_ROOT = pkg
            return pkg
    raise ImportError(
        "Installed langgraph library not found in site-packages "
        "(required for StateGraph / graph runtime)."
    )


def _namespace_spec(fullname: str, directory: Path):
    spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
    spec.submodule_search_locations = [str(directory)]
    return spec


class OfficialLangGraphFinder(importlib.abc.MetaPathFinder):
    """Resolve non-CRM ``langgraph.*`` names from the installed distribution."""

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: ModuleType | None = None,
    ):
        if fullname == "langgraph" or not fullname.startswith("langgraph."):
            return None

        first = fullname.split(".", 2)[1]
        if first in OUR_SUBPACKAGES:
            return None

        try:
            dist = installed_dist_root()
        except ImportError:
            return None

        rel_parts = fullname.split(".")[1:]
        directory = dist.joinpath(*rel_parts)
        if directory.is_dir():
            init = directory / "__init__.py"
            if init.is_file():
                return importlib.util.spec_from_file_location(
                    fullname,
                    init,
                    submodule_search_locations=[str(directory)],
                )
            # PEP 420 namespace package (e.g. langgraph.cache)
            return _namespace_spec(fullname, directory)

        module_file = dist
        for i, part in enumerate(rel_parts):
            module_file = module_file / (f"{part}.py" if i == len(rel_parts) - 1 else part)
        if module_file.is_file():
            return importlib.util.spec_from_file_location(fullname, module_file)
        return None


def install_shadow_finder() -> None:
    """Install the meta path finder once (idempotent)."""
    global _FINDER_INSTALLED
    if _FINDER_INSTALLED:
        return
    sys.meta_path.insert(0, OfficialLangGraphFinder())
    _FINDER_INSTALLED = True
