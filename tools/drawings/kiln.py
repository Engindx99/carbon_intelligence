"""The rotary kiln's sheet: its gas bore (the CFD's flow volume) and its
wall as the twin models it (physics/shell.py DEFAULT_WALL_STACKS burning /
transition, placed at r_inner = D / 2 by burning.py / transition.py):
every value geometry/macros/drawings.bas shows or lists, with where it
comes from (one sheet for the kiln, user 22 Nov 2026; it replaced the
gas-volume-only sheet, whose values are here too).

The solid drawn is kiln_wall.SLDPRT (kiln_wall.bas): ONE brick tube and
ONE steel shell tube over the whole kiln, plus the two end rings built
brick by brick (ISO 5417). The brick's hot face is the bore D, the gas
volume's wall: the CFD solid kiln.SLDPRT is that bore from z_cfd0 (the
kiln inlet chamber's stub of the tube before it, stub + solid = L). The
twin's zones (transition z 0 .. transition_L alumina, burning the rest
magnesia-spinel) differ only in the brick grade: a model split. The slope
is installed, not built in. Not a fabrication drawing.
"""

from geometry import plant_geometry as pg
from physics.shell import DEFAULT_WALL_STACKS

from . import provenance as pv
from .cyclone import SOURCE_EN, cell, unit  # noqa: F401  (the sheet's table text)

# What the macro dimensions (its log names them "dim <key> <mm>"), each
# between edges the wall solid has.
DIMENSIONED = ("D_kiln", "D_shell", "L_kiln", "brick_t", "shell_t")

ALSO = {}

ORDER = (
    "D_kiln", "D_shell",
    "L_kiln", "z_cfd0", "L_cfd", "slope", "transition_L", "burning_L",
    "volume", "wall_area",
    "shell_t", "brick_t",
    "V_brick_transition", "V_brick_burning", "V_shell",
    "brick_A", "brick_L", "brick_B", "brick_n", "brick_rings", "brick_total",
    "u_coating", "u_tyre", "u_shape", "u_ends",
)

# The legend, hot face outward, as the twin's stacks name the layers:
# (the solid's body, where along it, zones whose stack holds the layer,
# layer name in DEFAULT_WALL_STACKS). The shell is one body: both zones'
# stacks must give it the same properties.
BODIES = (
    ("brick", "transition zone", ("transition",), "alumina brick"),
    ("brick", "burning zone", ("burning",), "magnesia-spinel brick"),
    ("steel_shell", "whole kiln", ("transition", "burning"), "steel shell"),
)


def _layer(zone, layer):
    rows = [row for row in DEFAULT_WALL_STACKS[zone]["layers"] if row[0] == layer]
    if len(rows) != 1:
        raise KeyError(f"wall stack {zone}: {len(rows)} layers named {layer!r}")
    return rows[0]


def layer_properties():
    """[(body, where, layer, k, rho, cp)] from the twin's stacks, so the
    sheet's legend is the model's own numbers (no hand copy)."""
    out = []
    for body, where, zones, layer in BODIES:
        rows = {_layer(z, layer)[2:] for z in zones}
        if len(rows) != 1:
            raise ValueError(f"{layer!r} differs between the zones {zones}; one body cannot carry both")
        k, rho, cp = rows.pop()
        out.append((body, where, layer, k, rho, cp))
    return out


def params(g, name="kiln"):
    """{short key: Param} for the kiln (name is the sheet's, unused)."""
    k = pg.kiln(g)
    w = k["wall"]
    P = {}
    P["D_kiln"] = pv.primary(g, "kiln.D", "Flow bore D = brick hot face (whole tube)", key="kiln.D")
    P["L_kiln"] = pv.primary(g, "kiln.L", "Kiln length (all lined)", key="kiln.L")
    P["transition_L"] = pv.primary(g, "kiln.transition_L", "Transition zone (alumina), model split",
                                   key="kiln.transition_L")
    P["burning_L"] = pv.derived("kiln.burning_L", "Burning zone (magnesia-spinel)", k["burning_L"], "m",
                                [P["L_kiln"], P["transition_L"]])
    P["slope"] = pv.primary(g, "kiln.slope", "Slope (installed, not built in)", key="kiln.slope")
    stub = pv.primary(g, "kiln_inlet_chamber.mouth_stub_over_D", "Kiln inlet chamber's stub over D",
                      key="kiln_inlet_chamber.mouth_stub_over_D")
    P["z_cfd0"] = pv.derived("kiln.z_cfd0", "CFD solid from z0 (the KIC's stub before it)",
                             k["z_cfd0"], "m", [P["D_kiln"], stub])
    P["L_cfd"] = pv.derived("kiln.L_cfd", "CFD solid's length (L minus the KIC's stub)", k["L_cfd"], "m",
                            [P["L_kiln"], P["D_kiln"], stub])
    P["volume"] = pv.derived("kiln.volume_cfd", "Gas volume (CFD solid)", k["volume_cfd"], "m3",
                             [P["D_kiln"], P["L_cfd"]])
    P["wall_area"] = pv.derived("kiln.wall_area_cfd", "Wetted area (CFD solid)", k["wall_area_cfd"], "m2",
                                [P["D_kiln"], P["L_cfd"]])
    P["shell_t"] = pv.primary(g, "kiln.shell_t", "Steel shell plate", key="kiln.shell_t")
    P["brick_t"] = pv.primary(g, "kiln.lining_t", "Brick ring H (both zones)", key="kiln.lining_t")
    zl = {"transition": P["transition_L"], "burning": P["burning_L"]}
    if w["D_shell_transition"] != w["D_shell_burning"]:
        raise ValueError("kiln wall: the zones' shells differ; one shell tube cannot hold both")
    P["D_shell"] = pv.derived("kiln.D_shell", "Shell outer D (one tube)", w["D_shell_burning"], "m",
                              [P["D_kiln"], P["brick_t"], P["shell_t"]])
    P["V_shell"] = pv.derived("kiln.V_shell", "Volume, steel shell", w["V_shell_transition"] + w["V_shell_burning"],
                              "m3", [P["D_kiln"], P["brick_t"], P["shell_t"], P["L_kiln"]])
    for zone in ("transition", "burning"):
        P[f"V_brick_{zone}"] = pv.derived(f"kiln.V_brick_{zone}",
                                          "Volume, " + ("alumina" if zone == "transition" else "magnesia-spinel")
                                          + " brick", w[f"V_brick_{zone}"], "m3",
                                          [P["D_kiln"], P["brick_t"], zl[zone]])
    # the bricks (ISO 5417): the zones' rings are alike (one wall), so the
    # burning zone's numbers stand for both; the counts are per zone summed
    P["brick_A"] = pv.primary(g, "kiln.brick_cold_face", "Brick cold face A (ISO 5417)", key="kiln.brick_cold_face")
    P["brick_L"] = pv.primary(g, "kiln.brick_length", "Brick length L, one ring (ISO 5417)", key="kiln.brick_length")
    shape = [P["D_kiln"], P["brick_t"], P["brick_A"]]
    P["brick_B"] = pv.derived("kiln.brick_hot_chord", "Brick hot face B, equivalent (ISO 522/622 mix)",
                              w["brick_hot_chord_burning"], "m", shape)
    P["brick_n"] = pv.derived("kiln.brick_n", "Bricks per ring", w["brick_n_burning"], "-", shape)
    rings = w["brick_rings_transition"] + w["brick_rings_burning"]
    P["brick_rings"] = pv.derived("kiln.brick_rings", "Rings (each zone's last one cut)", rings, "-",
                                  [P["L_kiln"], P["transition_L"], P["brick_L"]])
    total = (w["brick_n_transition"] * w["brick_rings_transition"]
             + w["brick_n_burning"] * w["brick_rings_burning"])
    P["brick_total"] = pv.derived("kiln.brick_total", "Bricks in all (2 end rings modelled brick by brick)", total, "-",
                                  [P["brick_n"], P["brick_rings"]])
    doc = P["D_kiln"].doc
    P["u_coating"] = pv.unknown("kiln.coating", "Clinker coating (left out, user 22 Nov 2026)",
                                f"{doc}: not modelled for now")
    P["u_tyre"] = pv.unknown("kiln.tyres", "Tyres, rollers, drive, seals (kiln_rotax.SLDPRT, ROTAX-2)",
                             f"{doc}: on the kiln_rotax sheet")
    P["u_shape"] = pv.unknown("kiln.brick_joints", "Joints, mortar, metal plates, key bricks", f"{doc}: no source")
    P["u_ends"] = pv.unknown("kiln.end_castables", "Inlet / outlet castable, nose ring", f"{doc}: no source")
    assert set(ORDER) == set(P) and set(DIMENSIONED) <= set(P), set(ORDER) ^ set(P)
    return P
