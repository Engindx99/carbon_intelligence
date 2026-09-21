"""A text report of one catalogue line: every value with its provenance.

    P  published                 stated in the source
    R  derived_from_reference    published value x one named FLS ratio
    M  model_assumption          the source's modelling assumption
    -  no source gives it

Assumptions a value rests on are numbered once and cited by number.
"""

from geometry.catalog import DERIVED, MODEL_ASSUMPTION, PUBLISHED, SOURCES
from geometry.properties import (
    MissingGeometry,
    cyclone_properties,
    duct_section,
    vessel_properties,
)


MARK = {PUBLISHED: "P", DERIVED: "R", MODEL_ASSUMPTION: "M"}


def line_report(line):

    notes = []
    rows = []

    for path, m in line.measures():

        if m is None:
            rows.append(f"  {path:<26} {'-':>10}  -")
            continue

        cited = []

        for a in m.assumptions:
            if a not in notes:
                notes.append(a)
            cited.append(str(notes.index(a) + 1))

        tail = f"  [{','.join(cited)}]" if cited else ""
        rows.append(f"  {path:<26} {m.value:>10.3f}  {MARK[m.basis]}  {m.ref}{tail}")

    out = [
        f"Reference line {line.key}   strings: {line.strings}",
        "",
        "Catalogue (P published, R derived_from_reference, M model_assumption, - none)",
        *rows,
        "",
        "Assumptions",
        *[f"  [{i + 1}] {a}" for i, a in enumerate(notes)],
        "",
        "Equipment volumes and areas, catalogue dimensions only, no CFD extensions",
        "(one cyclone; x count for the stage). Use these for residence time and hold-up.",
    ]

    for stage in line.cyclones:
        p = cyclone_properties(stage)
        out.append(
            f"  C{p.stage} x{p.count}: V {p.body_volume:8.1f} m3   wetted {p.wetted_area:7.1f} m2"
            f"   H {p.height:6.2f} m   cone wall {90.0 - p.cone_half_angle_deg:5.1f} deg"
            f"   inlet {p.inlet.area:6.2f} m2 (D_h {p.inlet.hydraulic_D:.2f} m)"
        )

    for name, part, fn in (
        ("calciner", line.calciner, vessel_properties),
        ("kiln", line.kiln, vessel_properties),
    ):
        try:
            p = fn(part, name)
            out.append(
                f"  {name}: V {p.volume:8.1f} m3   wetted {p.wetted_area:7.1f} m2"
                f"   section {p.section.area:6.2f} m2"
            )
        except MissingGeometry as e:
            out.append(f"  {e}")

    for duct in line.ducts:
        s = duct_section(duct, duct.name)
        out.append(
            f"  {duct.name} (C{duct.from_stage} -> C{duct.to_stage}): section {s.area:6.2f} m2;"
            " no volume (SOURCES.md, Açık belirsizlikler)"
        )

    try:
        s = duct_section(line.gooseneck, "gooseneck")
        out.append(f"  gooseneck: section {s.area:6.2f} m2")
    except MissingGeometry as e:
        out.append(f"  {e}")

    out += ["", "Sources"]
    out += [f"  {k:<8} {title}  {url}" for k, (title, url) in SOURCES.items()]

    return "\n".join(out)
