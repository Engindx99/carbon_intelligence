"""
The equipment drawings say what the geometry source says.

The drawings are made in SolidWorks by geometry/macros/drawings.bas
from its generated Const block; the JSON next to each lists every value
on the sheet (tools/gen_drawings.py). These pin that every listed value
comes from geometry/plant_geometry.yaml with the status its source tag
earns (Verified only for a published figure), that the macro's table is
the JSON's, that nothing without a source is dimensioned, and -- once
the macro has run -- that every dimension SolidWorks measured on the
sheet is the source's value.
"""
import json
import re
import unittest
from pathlib import Path

from geometry import plant_geometry as pg
from tools import gen_drawings, gen_geometry

ROOT = Path(__file__).resolve().parents[1]
STATUS = {
    "published": "Verified",
    "derived_from_reference": "Estimated",
    "literature": "Estimated",
    "cfd_decision": "Estimated",
    "model": "Estimated",
    "schematic": "Schematic",
}
RANK = {"Unknown": 0, "Schematic": 1, "Estimated": 2, "Verified": 3}


def _yaml_entry(dotted):
    node = pg.load()
    for part in dotted.split("."):
        node = node[part]
    return node


def _payload(name):
    return json.loads((gen_drawings.OUT / name / f"{name}.json").read_text(encoding="utf-8"))


class TheDataFilesTest(unittest.TestCase):

    def test_no_data_file_is_stale(self):
        """python3 tools/gen_drawings.py --check"""
        self.assertEqual(gen_drawings.run(check=True), [])

    def test_every_listed_value_traces_to_the_source(self):
        for name in gen_drawings.EQUIPMENT:
            for p in _payload(name)["params"]:
                with self.subTest(name=name, key=p["key"]):
                    if p["status"] == "Unknown":
                        self.assertIsNone(p["value"])
                        self.assertEqual(p["inputs"], [])
                        continue
                    self.assertTrue(p["inputs"])
                    statuses = [STATUS[_yaml_entry(k)["source"]] for k in p["inputs"]]
                    if p["source"] == "derived":
                        self.assertEqual(p["status"], min(statuses, key=RANK.get))
                    else:
                        e = _yaml_entry(p["inputs"][0])
                        self.assertEqual(p["status"], STATUS[e["source"]])
                        if len(p["inputs"]) == 1:
                            self.assertEqual(p["value"], e["value"])

    def test_only_sourced_values_are_dimensioned(self):
        for name in gen_drawings.EQUIPMENT:
            data = _payload(name)
            status = {p["short"]: p["status"] for p in data["params"]}
            for k in data["dimensioned"]:
                with self.subTest(name=name, key=k):
                    self.assertIn(status[k], ("Verified", "Estimated"))


class TheMacroTableIsTheJsonTest(unittest.TestCase):

    def test_the_sheet_table_is_the_json(self):
        text = (gen_geometry.MACROS / "drawings.bas").read_text(encoding="latin-1")
        for name in gen_drawings.EQUIPMENT:
            chunks = re.findall(rf'^Const {name}_TAB_\d+\s+As String\s+=\s+"(.*)"', text, re.M)
            rows = [r.split("~") for r in "".join(chunks).split(";") if r]
            data = _payload(name)
            self.assertEqual([r[0] for r in rows], [p["short"] for p in data["params"]])
            self.assertEqual([r[5] for r in rows], [p["status"] for p in data["params"]])


def _table_rows(name):
    """The sheet's parameter table as the macro prints it: {key: value text}."""
    text = (gen_geometry.MACROS / "drawings.bas").read_text(encoding="latin-1")
    chunks = re.findall(rf'^Const {name}_TAB_\d+\s+As String\s+=\s+"(.*)"', text, re.M)
    return {r.split("~")[0]: r.split("~")[2] for r in "".join(chunks).split(";") if r}


def _half_up(x, decimals=0):
    """SolidWorks' display rounding: a half goes up (848.5 -> 849)."""
    from decimal import ROUND_HALF_UP, Decimal
    return str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-decimals), ROUND_HALF_UP))


class TheTableRoundsAsTheDimensionsTest(unittest.TestCase):
    """A value sits on a sheet twice, as a SolidWorks dimension and in the
    parameter table; both must print the same digits."""

    def test_a_half_goes_up(self):
        from tools.drawings import cyclone, provenance as pv
        cases = [(0.8485, "m", "849"), (0.0025, "m", "3"), (1.0, "m", "1000"),
                 (-2.1015, "m", "-2102"), (1009.705, "m3", "1009.71"), (635.955, "m2", "635.96")]
        for value, unit, want in cases:
            with self.subTest(value=value, unit=unit):
                p = pv.Param(key="k", label="k", value=value, unit=unit, source="derived",
                             status="Estimated", doc="-", inputs=["x"])
                self.assertEqual(cyclone.cell(p), want)

    def test_the_pid_size_rounds_the_same_way(self):
        from tools.pid import model
        self.assertEqual(model.size_text(0.8485, "Estimated"), "D 0.849 E")
        self.assertEqual(model.size_text(0.0005, "Verified"), "D 0.001")

    def test_the_table_prints_each_logged_dimension(self):
        ran = False
        for name in gen_drawings.EQUIPMENT:
            log = gen_drawings.LOG_DIR / f"drawings_{name}_build.log"
            if not log.exists():
                continue
            ran = True
            table = _table_rows(name)
            units = {p["short"]: p["unit"] for p in _payload(name)["params"]}
            for k, v in re.findall(r"^dim (\S+) (-?[\d.]+)$", log.read_text(encoding="latin-1"), re.M):
                if units[k] != "m":
                    continue
                with self.subTest(name=name, key=k):
                    self.assertEqual(table[k], _half_up(float(v)))
        if not ran:
            self.skipTest("no drawings_*_build.log: run geometry/macros/drawings.bas")


class TheSheetMeasuresTheSourceTest(unittest.TestCase):
    """drawings.bas logs every dimension SolidWorks measured as
    'dim <key> <mm or deg>'; skipped until the macro has run here."""

    def test_the_logged_dimensions(self):
        ran = False
        for name in gen_drawings.EQUIPMENT:
            log = gen_drawings.LOG_DIR / f"drawings_{name}_build.log"
            if not log.exists():
                continue
            ran = True
            text = log.read_text(encoding="latin-1")
            first = text.splitlines()[0]
            self.assertTrue(first.startswith(f"drawings {name} built:"), first)
            self.assertNotIn("ABORTED", text)
            self.assertNotIn("MISMATCH", text)
            self.assertNotIn("MISSING", text)
            # the CFD solid drawn from is a verified input: left untouched
            self.assertIn("part unchanged: ", text)
            data = _payload(name)
            params = {p["short"]: p for p in data["params"]}
            got = dict(re.findall(r"^dim (\S+) (-?[\d.]+)$", text, re.M))
            self.assertEqual(sorted(got), sorted(data["dimensioned"]))
            for k, v in got.items():
                with self.subTest(name=name, key=k):
                    p = params[k]
                    want = p["value"] if p["unit"] == "deg" else p["value_mm"]
                    self.assertAlmostEqual(float(v), want, delta=0.5)
        if not ran:
            self.skipTest("no drawings_*_build.log: run geometry/macros/drawings.bas")


if __name__ == "__main__":
    unittest.main()
