"""The equipment inventory: every piece of equipment the model has, by
process area, with the dimensions the one source holds for it (and
their status), what it connects to, what is missing, whether a CFD
solid exists to draw it from, and whether it is drawn.

Only equipment the plant model really has is listed (the twin's zones,
the geometry docs); nothing is added for completeness. The dimensions
are read from geometry/plant_geometry.yaml; the "missing" notes are the
docs' own TBDs.
"""

from geometry import plant_geometry as pg

from . import provenance as pv

# area, tag, name, quantity (plant: 2 strings), yaml prefixes, connections,
# missing (doc: what), CFD solid (cyclone.bas / calciner.bas output)
EQUIPMENT = [
    ("Raw meal", "FEED", "Raw meal feed chute into the C1 riser", "2",
     ["cyclone_domain.c1_feed_", "cyclone_domain.meal_slope"],
     "raw meal in -> R1 branch of each C1",
     ["preheater/riser_R1.md: feed system upstream of the chute is not modelled"], ""),
    ("Raw meal", "MP", "Meal pipes C1-C5 (with flap valves)", "per cyclone",
     [],
     "cyclone dust outlet -> next stage's riser / calciner / kiln inlet",
     ["preheater/meal_pipe_C1.md .. C5.md: diameter, length, slope, route, flap position TBD"], ""),
    ("Preheater", "C1", "Cyclone C1 (stage 1, top)", "2 per string",
     ["cyclones.C1.", "cyclone_domain.vortex_wall", "cyclone_domain.inlet_", "cyclone_domain.volute_tongue"],
     "gas: R1 -> C1 -> to the ID fan; meal: C1 -> C2 riser",
     [], "C1.SLDPRT"),
    ("Preheater", "C2", "Cyclone C2", "1 per string",
     ["cyclones.C2.", "cyclones.C4."],
     "gas: R2 -> C2 -> R1; meal: C2 -> C3 riser", [], "C4.SLDPRT (same geometry)"),
    ("Preheater", "C3", "Cyclone C3", "1 per string",
     ["cyclones.C3.", "cyclones.C4."],
     "gas: R3 -> C3 -> R2; meal: C3 -> C4 riser", [], "C4.SLDPRT (same geometry)"),
    ("Preheater", "C4", "Cyclone C4", "1 per string",
     ["cyclones.C4.", "cyclone_domain.vortex_wall", "cyclone_domain.inlet_duct_length",
      "cyclone_domain.volute_"],
     "gas: R4 -> C4 -> R3; meal: C4 -> calciner", [], "C4.SLDPRT"),
    ("Preheater", "C5", "Cyclone C5 (calciner outlet cyclone)", "1 per string",
     ["cyclones.C5.", "cyclones.C4."],
     "gas: gooseneck -> C5 -> R4; meal: C5 -> kiln inlet chamber", [], "C5.SLDPRT"),
    ("Preheater", "VF", "Vortex finders (dip tubes) of C1-C5", "per cyclone",
     ["cyclones.C1.L_vortex", "cyclones.C1.D_vortex", "cyclones.C4.L_vortex",
      "cyclones.C4.D_vortex", "cyclone_domain.vortex_wall"],
     "inside each cyclone, gas out", ["(no structure: wall 0.08 m is a CFD model parameter)"],
     "in each cyclone solid"),
    ("Preheater", "R1-R4", "Gas risers / ducts between stages", "per string",
     ["risers.R1.", "layout.c1_twin_gap"],
     "R1: C2 -> its Y -> the twin C1; R2-R4: C3..C5 outlet pipes up to C2..C4",
     ["preheater/riser_R2.md .. R4.md: the outlet pipes are the risers; route lengths are layout"],
     "C1_twin.SLDPRT (R1 stub, Y, both C1)"),
    ("Calciner", "GN", "Gooseneck (Y) from the calciner to C5", "1 per calciner",
     ["gooseneck."],
     "calciner roof -> 2 legs -> C5 of each string", [], "calciner.SLDPRT"),
    ("Calciner", "ILC", "In-line calciner (ILC) vessel", "1",
     ["calciner.D", "calciner.H", "calciner.cone_angle", "calciner.throat_", "calciner.D_shell"],
     "kiln gas (throat) + tertiary air + C4 meal + fuel -> gooseneck", [], "calciner.SLDPRT"),
    ("Calciner", "TAD", "Tertiary air duct", "1",
     ["calciner.D_tertiary_air", "calciner.tertiary_air_"],
     "cooler hood -> calciner (tangential)",
     ["fluid_volumes.md: duct length and route absent (drawn route is schematic)"],
     "calciner.SLDPRT (3 m stub only)"),
    ("Calciner", "NOZ", "Calciner meal and fuel inlet pipes", "2 + 2",
     ["calciner.D_feed", "calciner.feed_", "calciner.D_fuel", "calciner.fuel_slope"],
     "C4 meal, calciner fuel -> calciner", [], "calciner.SLDPRT"),
    ("Rotary kiln", "KILN", "Rotary kiln tube", "1",
     ["kiln."],
     "kiln inlet chamber <- clinker -> kiln hood / cooler", [], "kiln.SLDPRT"),
    ("Rotary kiln", "KIC", "Kiln inlet chamber", "1",
     [], "C5 meal + kiln gas -> calciner throat",
     ["kiln/kiln_inlet_chamber.md: geometry TBD (only a schematic margin in the layout)"], ""),
    ("Rotary kiln", "HOOD", "Kiln hood", "1",
     [], "cooler -> secondary air -> kiln; -> tertiary air duct",
     ["fluid_volumes.md: all dimensions absent"], ""),
    ("Rotary kiln", "BRN", "Kiln burner", "1",
     [], "primary air + fuel -> kiln",
     ["plant_topology.md: drawn as an arrow only; no dimensions"], ""),
    ("Clinker cooler", "COOL", "Grate cooler", "1",
     ["cooler."],
     "kiln clinker -> cooler; air -> secondary / tertiary / vent",
     ["cooler/cooler.md: vent outlet TBD"], "cooler.SLDPRT"),
    ("ID fan", "IDF", "Preheater ID fan", "per string",
     [], "C1 gas -> ID fan",
     ["plant_topology.md: drawn as an arrow only; no dimensions"], ""),
]


# Equipment drawn on another's sheet (same geometry, one solid).
SAME_SHEET = {"KILN": "kiln", "COOL": "cooler", "C2": "C4", "C3": "C4", "GN": "calciner", "ILC": "calciner", "TAD": "calciner", "NOZ": "calciner"}


def _matches(key, prefixes):
    return any(key == p or key.startswith(p) for p in prefixes)


def build(g, drawn, ready=()):
    """drawn: tags whose drawing has been made and checked in SolidWorks;
    ready: tags drawings.bas can draw, not yet run."""
    out = []
    for area, tag, name, qty, prefixes, conn, missing, solid in EQUIPMENT:
        dims = []
        for key, e in pg.entries(g):
            if _matches(key, prefixes):
                dims.append({
                    "key": key, "value": e["value"], "unit": e["unit"],
                    "source": e["source"], "status": pv.STATUS_OF_SOURCE[e["source"]],
                    "doc": e["doc"],
                })
        counts = {}
        for d in dims:
            counts[d["status"]] = counts.get(d["status"], 0) + 1
        out.append({
            "area": area, "tag": tag, "name": name, "quantity": qty,
            "connections": conn,
            "dimensions": dims,
            "status_counts": counts,
            "missing": missing,
            "cfd_solid": solid,
            "drawing": ("drawn: geometry/drawings/" + SAME_SHEET.get(tag, tag) + "/")
                       if SAME_SHEET.get(tag, tag) in drawn else
                       "drawings.bas ready, not yet run" if SAME_SHEET.get(tag, tag) in ready else
                       ("no data: source research first" if not dims else "to draw"),
        })
    return {"source": "geometry/plant_geometry.yaml", "equipment": out}


def markdown(inv):
    lines = [
        "# Equipment inventory",
        "",
        "Generated by `tools/gen_drawings.py` from `geometry/plant_geometry.yaml`; do not edit by hand.",
        "Status: published = Verified; FLS ratio, literature, CFD decision, model = Estimated;",
        "schematic = layout only; absent = Unknown.",
        "",
        "| Area | Tag | Equipment | Qty | Dimensions (V / E / S) | CFD solid | Drawing | Missing |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for e in inv["equipment"]:
        c = e["status_counts"]
        dims = f"{c.get('Verified', 0)} / {c.get('Estimated', 0)} / {c.get('Schematic', 0)}"
        miss = "; ".join(e["missing"]) or "-"
        lines.append(f"| {e['area']} | {e['tag']} | {e['name']} | {e['quantity']} | {dims} | "
                     f"{e['cfd_solid'] or '-'} | {e['drawing']} | {miss} |")
    return "\n".join(lines) + "\n"
