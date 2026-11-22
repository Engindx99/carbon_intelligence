"""The plant drawing keeps every CFD domain exactly as solved.

geometry/macros/plant_topology_2d.bas draws C1 as the C1 CFD domain,
C2..C4 as the C4 one and C5 as its 6.50 / 6.30 copy. Both macros take
their constants from generated blocks (tools/gen_geometry.py, from
geometry/plant_geometry.yaml); geometry/macros/cyclone.bas built the
CFD solids. Both are read here as text and every dimension inside a
domain -- between its inlet and outlet faces -- must agree, so neither
can drift without the other (geometry/plant_topology.md, "CFD domenleri
ve serbest bölge"). Everything outside the faces is the drawing's own
and is not checked.
"""

import math
import re
import unittest

from tests.twin_harness import REPO_ROOT

MACROS = REPO_ROOT / "geometry" / "macros"
TOL = 1e-3  # m


def _number(token, consts):
    token = token.strip().rstrip("#")
    try:
        return float(token)
    except ValueError:
        return consts[token]


def _consts(text):
    """Every numeric (and Boolean) module-level Const."""
    out = {}
    for name, value in re.findall(
        r"^Const\s+(\w+)\s+As\s+\w+\s*=\s*([-\d.]+|True|False)#?", text, re.M
    ):
        out[name] = value == "True" if value in ("True", "False") else float(value)
    return out


def _cases(text, consts):
    """The assignments in each Case of cyclone.bas's SelectCyclone."""
    body = text[text.index("Private Sub SelectCyclone()"):]
    body = body[: body.index("End Sub")]
    out = {}
    for name, block in re.findall(
        r'Case "(\w+)"(.*?)(?=Case "|\Z)', body, re.S
    ):
        vals = {}
        for key, value in re.findall(
            r"^\s*(\w+)\s*=\s*([\w.#]+)\s*$", block, re.M
        ):
            if value in ("True", "False"):
                continue
            vals[key] = _number(value, {**consts, **vals})
        out[name] = vals
    return out


class CfdLock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cyc = (MACROS / "cyclone.bas").read_text(encoding="latin-1")
        drw = (MACROS / "plant_topology_2d.bas").read_text(encoding="latin-1")
        cls.cc = _consts(cyc)
        cls.case = _cases(cyc, cls.cc)
        cls.d = _consts(drw)

    def same(self, drawn, solved, what):
        self.assertAlmostEqual(
            drawn, solved, delta=TOL,
            msg=f"{what}: drawing {drawn} vs CFD {solved}",
        )

    def body(self, tag, c):
        d = self.d
        self.same(d[f"{tag}_D"], c["D_BARREL"], f"{tag} barrel D")
        self.same(d[f"{tag}_HB"], c["H_BARREL"], f"{tag} barrel height")
        self.same(d[f"{tag}_HC"], c["H_CONE"], f"{tag} cone height")
        self.same(d[f"{tag}_VD"], c["D_VORTEX"], f"{tag} vortex finder D")
        self.same(d[f"{tag}_DD"], c["D_DUST"], f"{tag} dust outlet D")

    def test_c4_domain(self):
        c, d, cc = self.case["C4"], self.d, self.cc
        self.body("C4", c)
        self.same(d["C4_VF_S"], c["L_VORTEX"], "C4 vortex finder immersion")
        self.same(d["C4_IN_H"], c["H_INLET"], "C4 inlet height")
        self.same(d["C4_IN_W"], c["W_INLET"], "C4 inlet width")
        self.same(d["C4_TONGUE"], cc["INLET_TONGUE"], "C4 volute tongue")
        self.same(d["C4_IN_L"], c["L_INLET_C"], "C4 level inlet duct length")
        self.same(d["C4_OUT_RISE"], c["OUTLET_EXT_OVER_VORTEX_D"] * c["D_VORTEX"],
                  "C4 outlet pipe rise")
        # since 17 Nov 2026 the outlet is straight and a riser turns in under
        # the inlet (R2 / R3 as the plant has them)
        self.assertEqual(c["OUTLET_TURN_DEG"], 0.0)
        self.same(d["C4_OUT_R"], 0.0, "C4 outlet bend radius (none)")
        self.same(d["RISER_CUT_DEG"], cc["RISER_CUT_DEG"], "the risers' cut under the elbow")

    def test_c5_is_the_c4_domain_scaled(self):
        c5, c4, d = self.case["C5"], self.case["C4"], self.d
        self.body("C5", c5)
        self.same(d["C5_HIN"], c5["H_INLET"], "C5 inlet height")
        k = d["C5_D"] / d["C4_D"]
        for key in ("H_BARREL", "H_CONE", "L_VORTEX", "D_VORTEX", "D_DUST",
                    "H_INLET", "W_INLET", "L_INLET_C"):
            self.same(c5[key], k * c4[key], f"cyclone.bas C5 {key} = C4 x {k:.4f}")
        for key in ("OUTLET_EXT_OVER_VORTEX_D", "ELBOW_R_OVER_VORTEX_D",
                    "OUTLET_DOWN_OVER_VORTEX_D", "OUTLET_TURN_DEG"):
            self.assertEqual(c5[key], c4[key], key)

    def test_c1_domain(self):
        c, d, cc = self.case["C1"], self.d, self.cc
        self.body("C1", c)
        self.same(d["C1_VF_S"], c["L_VORTEX"], "C1 vortex finder immersion")
        self.same(d["C1_DUCT_H"], c["H_INLET"], "C1 inlet duct height")
        self.same(d["C1_BEND_DEG"], 90.0 + c["INLET_SLOPE_DEG"], "C1 branch bend")
        self.same(d["C1_OUT_RISE"], c["OUTLET_EXT_OVER_VORTEX_D"] * c["D_VORTEX"],
                  "C1 outlet pipe rise")
        self.same(d["C1_OUT_R"], c["ELBOW_R_OVER_VORTEX_D"] * c["D_VORTEX"],
                  "C1 outlet bend radius")
        self.assertEqual(c["OUTLET_TURN_DEG"], 180.0)
        # the riser branch: half R1's area, its bend, transition, feed chute
        branch = cc["D_RISER_SRC"] * math.sqrt(cc["RISER_AREA_SHARE"])
        self.same(d["R1_D"] * math.sqrt(0.5), branch, "C1 riser branch D")
        self.same(d["C1_BEND_R"], cc["RISER_BEND_R_OVER_D"] * branch, "C1 branch bend radius")
        self.same(d["C1_TRANS_L"], cc["RISER_TRANS_LEN"], "C1 round-to-duct transition")
        self.same(d["C1_BEND_Z"] - d["C1_FEED_Z"], cc["RISER_ABOVE_FEED"], "C1 feed to bend")
        self.same(d["C1_FEED_Z"] - d["C1_RISER_Z0"], cc["RISER_BELOW_FEED"],
                  "C1 domain floor to feed")
        self.same(d["C1_FEED_W"], cc["FEED_W"], "C1 feed chute width")
        self.same(d["C1_FEED_L"], cc["FEED_DEPTH"], "C1 feed chute depth")
        self.same(d["MEAL_SLOPE_DEG"], cc["FEED_SLOPE_DEG"], "C1 feed chute slope")


if __name__ == "__main__":
    unittest.main()
