"""Load geometry/pid/pid.yaml and resolve what it refers to.

pid.yaml holds topology, tags and layout cells only. A line's size is
a reference into geometry/plant_geometry.yaml; an instrument's value
is a key into the twin. Nothing numeric is written there.
"""

import ast
import functools
import json
import re
from pathlib import Path

import yaml

from geometry import plant_geometry as pg
from tools.drawings import provenance as pv

from . import scope as sc

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "geometry" / "pid" / "pid.yaml"
CONFIG = ROOT / "configs" / "twin_cfg.yaml"
REFERENCE = ROOT / "tests" / "data" / "twin_state_reference.json"

# plant_geometry functions a size reference may call, with the
# arguments they take after the source
DERIVED = {
    "stage_riser": pg.stage_riser,
    "r1_path": pg.r1_path,
    "meal_pipes": pg.meal_pipes,
    "gooseneck": pg.gooseneck,
    "calciner": pg.calciner,
    "cyclone": pg.cyclone,
    "c1_twin": pg.c1_twin,
    "kiln": pg.kiln,
    "cooler": pg.cooler,
}


def load(path=SOURCE):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ----------------------------------------------------------------------
# sizes
# ----------------------------------------------------------------------
def _walk(node, path):
    for tok in re.findall(r"\.(\w+)|\[([^\]]+)\]", path):
        name, idx = tok
        if name:
            node = node[name]
        else:
            key = ast.literal_eval(idx)
            node = node[key]
    return node


def resolve_size(g, ref):
    """(value in m or None, status, inputs) of a size reference."""
    if ref == "absent":
        return None, pv.UNKNOWN, []
    kind, _, rest = ref.partition(":")
    if kind == "yaml":
        node = g
        for part in rest.split("."):
            node = node[part]
        if not (isinstance(node, dict) and "value" in node):
            raise KeyError(f"{ref}: not an entry of plant_geometry.yaml")
        return float(node["value"]), pv.STATUS_OF_SOURCE[node["source"]], [rest]
    if kind == "derived":
        m = re.match(r"^(\w+)\(([^)]*)\)(.*)$", rest)
        if not m or m.group(1) not in DERIVED:
            raise KeyError(f"{ref}: not a whitelisted derived value")
        args = ast.literal_eval("(" + m.group(2) + ",)") if m.group(2).strip() else ()
        value = _walk(DERIVED[m.group(1)](g, *args), m.group(3))
        return float(value), pv.ESTIMATED, []
    raise KeyError(f"{ref}: a size is yaml:, derived: or absent")


def size_text(value, status):
    """The size as the sheet prints it: 'D 3.070', 'D 0.849 E', '-'."""
    if value is None:
        return "-"
    return f"D {pv.fmt_half_up(value, 3)}" + ("" if status == pv.VERIFIED else " E")


# ----------------------------------------------------------------------
# twin keys
# ----------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def _config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _split_index(rest):
    m = re.match(r"^(\w+)(\[-?\d+\])?$", rest)
    if not m:
        raise KeyError(f"{rest}: not a field name with an optional [i]")
    return m.group(1), m.group(2)


@functools.lru_cache(maxsize=None)
def _assigned_on_state():
    """Names assigned as state.<name> anywhere in the twin (tuple
    targets included), by ast."""
    names = set()
    for sub in ("pyroprocess", "physics", "chemistry"):
        for path in (ROOT / sub).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store)
                        and isinstance(node.value, ast.Name) and node.value.id == "state"):
                    names.add(node.attr)
    return names


@functools.lru_cache(maxsize=None)
def _class_fields(path, cls):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == cls:
            return {n.target.id for n in node.body if isinstance(n, ast.AnnAssign)}
    raise KeyError(f"{cls} not found in {path}")


@functools.lru_cache(maxsize=None)
def _tuple_constant(path, name):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == name for t in node.targets):
            return set(ast.literal_eval(node.value))
    raise KeyError(f"{name} not found in {path}")


@functools.lru_cache(maxsize=None)
def _function_names(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    return {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}


@functools.lru_cache(maxsize=None)
def _preheater_attrs():
    text = (ROOT / "pyroprocess" / "preheater" / "preheater.py").read_text(encoding="utf-8")
    return set(re.findall(r"self\.(\w+)\s*=", text))


def resolve_twin_key(key):
    """(status the key's prefix gives, where it was found); KeyError
    if the twin has no such thing."""
    prefix, _, rest = key.partition(":")
    if prefix not in sc.STATUS_OF_PREFIX:
        raise KeyError(f"{key}: unknown prefix {prefix!r}")
    status = sc.STATUS_OF_PREFIX[prefix]

    if prefix == "cfg":
        node = _config()
        for part in rest.split("."):
            node = node[part]
        return status, "configs/twin_cfg.yaml"

    if prefix == "mass":
        name, idx = _split_index(rest)
        if name not in _class_fields(ROOT / "physics" / "steady_state_mass.py", "SteadyStateMassFlow"):
            raise KeyError(f"{key}: not a SteadyStateMassFlow field")
        return status, "physics/steady_state_mass.py"

    if prefix == "state":
        name, idx = _split_index(rest)
        if name in _class_fields(ROOT / "pyroprocess" / "globalstate.py", "GlobalState"):
            return status, "pyroprocess/globalstate.py"
        if name in _assigned_on_state():
            return status, "assigned on state in the zones"
        raise KeyError(f"{key}: the twin never sets state.{name}")

    if prefix == "stage":
        m = re.match(r"^([1-4])\.(\w+)$", rest)
        if not m:
            raise KeyError(f"{key}: stage:<1..4>.<field>")
        if m.group(2) not in _tuple_constant(ROOT / "tests" / "twin_harness.py", "STAGE_FIELDS"):
            raise KeyError(f"{key}: not a preheater stage field")
        return status, "tests/twin_harness.py STAGE_FIELDS"

    if prefix == "attr":
        obj, _, field = rest.partition(".")
        if obj != "preheater" or field not in _preheater_attrs():
            raise KeyError(f"{key}: not an attribute set in pyroprocess/preheater/preheater.py")
        return status, "pyroprocess/preheater/preheater.py"

    # diag
    fn, _, path = rest.partition(".")
    if fn not in _function_names(ROOT / "reporter" / "diagnostics.py"):
        raise KeyError(f"{key}: reporter.diagnostics has no {fn}()")
    if path not in sc.DIAG_PATHS.get(fn, set()):
        raise KeyError(f"{key}: {path!r} is not a listed result of {fn}()")
    return status, "reporter/diagnostics.py"


def reference_value(key, snapshot=None):
    """The value in the frozen reference state, or None."""
    if snapshot is None:
        snapshot = json.loads(REFERENCE.read_text(encoding="utf-8"))["snapshot"]
    prefix, _, rest = key.partition(":")
    if prefix == "mass":
        return snapshot.get(f"mass_flow_{rest}")
    if prefix == "stage":
        k, _, field = rest.partition(".")
        return snapshot.get(f"stage{k}_{field}")
    if prefix == "state":
        name, idx = _split_index(rest)
        v = snapshot.get(name)
        if v is None:
            v = snapshot.get(f"state_{name}")
        if isinstance(v, list) and idx:
            return v[int(idx.strip("[]"))]
        return None if isinstance(v, list) else v
    return None
