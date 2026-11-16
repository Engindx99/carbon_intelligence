"""Where every drawn number comes from, and how far to trust it.

Each value on a drawing is a Param: a primary entry of
geometry/plant_geometry.yaml (its own `source` tag), a value
geometry/plant_geometry.py derives from several entries (the inputs
are named, and the status is the weakest of theirs), or a quantity no
source in the repo gives (Unknown: listed, never drawn).

Status, from the yaml's source tags:

    published                                    -> Verified
    derived_from_reference, literature,
    cfd_decision, model                          -> Estimated
    schematic                                    -> Schematic (layout only,
                                                    never dimensioned)
    not in the source                            -> Unknown
"""

from dataclasses import dataclass, field

from geometry import plant_geometry as pg

VERIFIED = "Verified"
ESTIMATED = "Estimated"
SCHEMATIC = "Schematic"
UNKNOWN = "Unknown"

STATUS_OF_SOURCE = {
    "published": VERIFIED,
    "derived_from_reference": ESTIMATED,
    "literature": ESTIMATED,
    "cfd_decision": ESTIMATED,
    "model": ESTIMATED,
    "schematic": SCHEMATIC,
}
assert set(STATUS_OF_SOURCE) == set(pg.SOURCES)

# Weakest first: a derived value is as good as its weakest input.
_RANK = {UNKNOWN: 0, SCHEMATIC: 1, ESTIMATED: 2, VERIFIED: 3}

# What the source tags are called on the sheet (geometry docs' wording).
SOURCE_TR = {
    "published": "yayınlanmış",
    "derived_from_reference": "FLS oranıyla türetilmiş",
    "literature": "literatür",
    "cfd_decision": "CFD kararı",
    "model": "model parametresi",
    "schematic": "şematik",
    "derived": "türetilmiş",
    "unknown": "kaynak yok",
}

# Units the drawings print lengths in.
LENGTH_UNITS = ("m",)


def fmt_half_up(x, decimals=0):
    """`x` printed with `decimals` digits, a half rounded away from zero,
    as SolidWorks prints a dimension (848.5 -> 849). Python's own
    rounding sends a half to the even digit (848.5 -> 848), so a value
    on a half would read differently in the table and on the view.
    round(x, 6) first drops the binary noise (848.4999999 is 848.5),
    as value_mm does."""
    from decimal import ROUND_HALF_UP, Decimal
    return str(Decimal(repr(round(float(x), 6))).quantize(Decimal(1).scaleb(-decimals), ROUND_HALF_UP))


@dataclass
class Param:
    key: str                 # dotted name, unique on one drawing
    label: str               # what it is, on the sheet
    value: object            # SI value as the source holds it (None: Unknown)
    unit: str
    source: str              # a yaml source tag, "derived" or "unknown"
    status: str
    doc: str = ""
    inputs: list = field(default_factory=list)   # yaml keys it rests on

    @property
    def mm(self):
        """The value in mm (lengths only)."""
        if self.unit not in LENGTH_UNITS:
            raise ValueError(f"{self.key} is in {self.unit}, not a length")
        return 1000.0 * float(self.value)

    @property
    def estimated(self):
        return self.status == ESTIMATED

    def as_json(self):
        out = {
            "key": self.key,
            "label": self.label,
            "value": self.value,
            "unit": self.unit,
            "source": self.source,
            "status": self.status,
            "doc": self.doc,
            "inputs": list(self.inputs),
        }
        if self.unit in LENGTH_UNITS and self.value is not None:
            out["value_mm"] = round(self.mm, 6)
        return out


def _node(g, dotted):
    node = g
    for part in dotted.split("."):
        node = node[part]
    return node


def primary(g, dotted, label, key=None):
    """A yaml entry as it stands."""
    e = _node(g, dotted)
    return Param(
        key=key or dotted,
        label=label,
        value=e["value"],
        unit=e["unit"],
        source=e["source"],
        status=STATUS_OF_SOURCE[e["source"]],
        doc=e["doc"],
        inputs=[dotted],
    )


def weakest(params):
    return min((p.status for p in params), key=_RANK.__getitem__)


def derived(key, label, value, unit, inputs, doc=""):
    """A value plant_geometry derives; `inputs` are the Params it is
    computed from."""
    keys = []
    for p in inputs:
        for k in p.inputs:
            if k not in keys:
                keys.append(k)
    return Param(
        key=key,
        label=label,
        value=value,
        unit=unit,
        source="derived",
        status=weakest(inputs),
        doc=doc or next((p.doc for p in inputs if p.doc), ""),
        inputs=keys,
    )


def unknown(key, label, why):
    """A quantity the drawing would need but no source gives."""
    return Param(
        key=key, label=label, value=None, unit="", source="unknown",
        status=UNKNOWN, doc=why,
    )


def cyclone_dim(g, name, dim, label):
    """One of a cyclone's resolved dimensions (cyclone(): C2, C3 =
    C4; C5 = C4 x D_C5 / D_C4), with the entries it rests on."""
    node = g["cyclones"][name]
    if "same_as" in node:
        base = node["same_as"]
        p = primary(g, f"cyclones.{base}.{dim}", label, key=f"{name}.{dim}")
        p.doc = node["per_string"]["doc"]
        return p
    if "scaled_from" in node:
        base = node["scaled_from"]
        if dim == "D_barrel":
            # the scale is set by this cyclone's own published D: that row
            # is the published value, not a scaled one (16 Nov sheet check:
            # C5 printed D 6500 as "derived" though Verified)
            p = primary(g, f"cyclones.{name}.D_barrel_published", label, key=f"{name}.D_barrel")
            assert abs(p.value - pg.cyclone(g, name)["D_barrel"]) < 1e-9, (name, p.value)
            p.doc = node["per_string"]["doc"]
            return p
        parts = [
            primary(g, f"cyclones.{base}.{dim}", label),
            primary(g, f"cyclones.{name}.D_barrel_published", label),
            primary(g, f"cyclones.{base}.D_barrel", label),
        ]
        value = pg.cyclone(g, name)[dim]
        unit = parts[0].unit
        return derived(f"{name}.{dim}", label, value, unit, parts,
                       doc=node["per_string"]["doc"])
    return primary(g, f"cyclones.{name}.{dim}", label, key=f"{name}.{dim}")
