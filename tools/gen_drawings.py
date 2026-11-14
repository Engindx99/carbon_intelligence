"""Write the drawings' data files from the plant's one geometry source.

The drawings themselves are made in SolidWorks by
geometry/macros/drawings.bas (geometry/drawings/<name>/<name>.pdf, .dxf);
this writes what goes with them:

    geometry/drawings/<name>/<name>.json   every value on the sheet: value,
                                           unit, source, status, inputs, and
                                           which are dimensioned
    geometry/drawings/inventory.json, .md  every piece of equipment, by
                                           process area, with what the
                                           source holds for it

    python3 tools/gen_drawings.py
    python3 tools/gen_drawings.py --check     # exit 1 if any file is stale
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from geometry import plant_geometry as pg  # noqa: E402
from tools.drawings import cyclone, inventory, twin  # noqa: E402

OUT = ROOT / "geometry" / "drawings"
LOG_DIR = ROOT / "geometry" / "output" / "2500"

STATUS_RULE = ("published -> Verified; derived_from_reference, literature, cfd_decision, "
               "model -> Estimated; schematic -> not dimensioned; absent -> Unknown (not "
               "drawn). A derived value takes the weakest status of its inputs.")

# name -> the module giving its params(g, name), ORDER and DIMENSIONED
EQUIPMENT = {
    "C1": cyclone,
    "C1_twin": twin,
}

# Drawings made in SolidWorks and checked against their build log; the
# rest of EQUIPMENT is ready in drawings.bas but not yet run.
DRAWN = ("C1", "C1_twin")


def payload(name, g=None):
    g = g or pg.load()
    mod = EQUIPMENT[name]
    P = mod.params(g, name)
    return {
        "equipment": name,
        "drawing": {
            "macro": "geometry/macros/drawings.bas",
            "files": [f"geometry/drawings/{name}/{name}.pdf", f"geometry/drawings/{name}/{name}.dxf"],
            "build_log": f"geometry/output/2500/drawings_{name}_build.log",
            "sheet": "A1, ISO 5457 frame, ISO 7200 title block",
            "projection": "first angle (ISO 5456-2)",
            "units": "mm",
        },
        "source": "geometry/plant_geometry.yaml",
        "status_rule": STATUS_RULE,
        "params": [dict(P[k].as_json(), short=k) for k in mod.ORDER],
        "dimensioned": list(mod.DIMENSIONED),
    }


def _text(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def files(g=None):
    """{path: text} of every file this writes."""
    g = g or pg.load()
    out = {OUT / n / f"{n}.json": _text(payload(n, g)) for n in EQUIPMENT}
    inv = inventory.build(g, drawn=DRAWN, ready=[n for n in EQUIPMENT if n not in DRAWN])
    out[OUT / "inventory.json"] = _text(inv)
    out[OUT / "inventory.md"] = inventory.markdown(inv)
    return out


def run(check=False):
    stale = []
    for path, text in files().items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            stale.append(str(path.relative_to(ROOT)))
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    return stale


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if a file is stale")
    a = ap.parse_args(argv)
    stale = run(check=a.check)
    for s in stale:
        print(("stale: " if a.check else "wrote: ") + s)
    if a.check and stale:
        return 1
    if not stale:
        print("drawings: every data file is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
