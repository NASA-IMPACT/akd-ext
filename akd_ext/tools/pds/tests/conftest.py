"""Conftest: shimming akd_ext.tools.pds.* so tests can import without the full framework."""

import importlib.util
import sys
import types
from pathlib import Path

PDS_ROOT = Path(__file__).resolve().parent.parent

# ── Step 1: stub the framework packages the source files import from ──
for name in [
    "akd",
    "akd._base",
    "akd.tools",
    "akd_ext",
    "akd_ext.tools",
    "akd_ext.mcp",
    "akd_ext.mcp.decorators",
]:
    if name not in sys.modules:
        m = types.ModuleType(name)
        m.__package__ = name
        m.__path__ = []
        sys.modules[name] = m

sys.modules["akd._base"].InputSchema = type("InputSchema", (), {})
sys.modules["akd._base"].OutputSchema = type("OutputSchema", (), {})
sys.modules["akd.tools"].BaseTool = type("BaseTool", (), {"__class_getitem__": classmethod(lambda cls, *a: cls)})
sys.modules["akd.tools"].BaseToolConfig = type("BaseToolConfig", (), {})
sys.modules["akd_ext.mcp.decorators"].mcp_tool = lambda cls: cls

# ── Step 2: build akd_ext.tools.pds namespace ──
akd_ext = sys.modules["akd_ext"]
akd_ext_tools = sys.modules["akd_ext.tools"]
akd_ext.tools = akd_ext_tools

pds = types.ModuleType("akd_ext.tools.pds")
pds.__package__ = "akd_ext.tools.pds"
pds.__path__ = [str(PDS_ROOT)]
sys.modules["akd_ext.tools.pds"] = pds
akd_ext_tools.pds = pds


def _load(full_name: str, filepath: Path, package: str):
    if full_name in sys.modules:
        return sys.modules[full_name]
    spec = importlib.util.spec_from_file_location(full_name, str(filepath))
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = package
    sys.modules[full_name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        pass  # partial is fine
    return mod


# ── Step 3: load utils/*.py ──
utils = types.ModuleType("akd_ext.tools.pds.utils")
utils.__package__ = "akd_ext.tools.pds.utils"
utils.__path__ = [str(PDS_ROOT / "utils")]
sys.modules["akd_ext.tools.pds.utils"] = utils
pds.utils = utils

for f in sorted((PDS_ROOT / "utils").glob("*.py")):
    if f.name == "__init__.py":
        continue
    full = f"akd_ext.tools.pds.utils.{f.stem}"
    mod = _load(full, f, "akd_ext.tools.pds.utils")
    if mod:
        setattr(utils, f.stem, mod)

# ── Step 4: load sub-packages (opus, ode, img, sbn, pds4, pds_catalog) ──
for pkg in ["opus", "ode", "img", "sbn", "pds4", "pds_catalog"]:
    pkg_dir = PDS_ROOT / pkg
    if not pkg_dir.is_dir():
        continue
    full_pkg = f"akd_ext.tools.pds.{pkg}"
    ns = types.ModuleType(full_pkg)
    ns.__package__ = full_pkg
    ns.__path__ = [str(pkg_dir)]
    sys.modules[full_pkg] = ns
    setattr(pds, pkg, ns)
    for f in sorted(pkg_dir.glob("*.py")):
        if f.name == "__init__.py":
            continue
        full = f"{full_pkg}.{f.stem}"
        mod = _load(full, f, full_pkg)
        if mod:
            setattr(ns, f.stem, mod)
