"""
The P&ID says only what the plant and the twin say.

geometry/pid/pid.yaml holds topology, tags and layout cells; sizes and
process values are references. These pin that every reference
resolves, every equipment tag is an inventory tag, the streams form
one connected plant with the twin's gas path from burner to stack,
every off-page connector pairs, and every variable the twin models in
scope (tools/pid/scope.py) is on exactly one instrument.
"""
import re
import unittest

from geometry import plant_geometry as pg
from tools import gen_geometry
from tools.pid import encode, model, scope, symbols, validate


class TheSourceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.p = model.load()
        cls.g = pg.load()

    def test_nothing_is_wrong(self):
        self.assertEqual(validate.validate(self.p, self.g), [])

    def test_every_key_in_scope_is_on_one_instrument_or_the_setpoint(self):
        keys = [i["key"] for i in self.p["instruments"].values()]
        keys += [s["manipulated"] for s in self.p["setpoints"].values()]
        self.assertEqual(sorted(keys), sorted(scope.SCOPE))

    def test_no_dimension_or_process_value_is_written_in_the_source(self):
        # sizes are strings (references); a bare number would be a copy
        for no, ln in self.p["lines"].items():
            with self.subTest(line=no):
                self.assertIsInstance(ln["size"], str)
        for tag, it in self.p["instruments"].items():
            with self.subTest(instrument=tag):
                self.assertIsInstance(it["key"], str)
                self.assertNotIn("value", it)

    def test_a_missing_size_is_unknown_not_invented(self):
        for no, ln in self.p["lines"].items():
            value, status, _ = model.resolve_size(self.g, ln["size"])
            with self.subTest(line=no):
                if ln["size"] == "absent":
                    self.assertIsNone(value)
                    self.assertEqual(status, "Unknown")
                else:
                    self.assertGreater(value, 0.0)


def _declared(decl):
    """The names a Dim line declares (commas inside bounds do not split)."""
    out, depth, cur = [], 0, ""
    for ch in decl.split("'")[0]:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [d.strip().split()[0].split("(")[0].lower() for d in out if d.strip()]


class TheMacroRecordsAreTheSourceTest(unittest.TestCase):

    def test_the_macro_holds_exactly_the_encoded_records(self):
        text = (gen_geometry.MACROS / "pid.bas").read_text(encoding="latin-1")
        p, g = model.load(), pg.load()
        for sh in p["sheets"]:
            chunks = re.findall(rf'^Const PID_{sh}_\d+\s+As String\s+=\s+"(.*?)"\s+\'', text, re.M)
            self.assertEqual(len(chunks), encode.CHUNKS)
            got = [r for r in "".join(chunks).split(";") if r]
            self.assertEqual(got, [r.rstrip(";") for r in encode.sheet_rows(p, g, sh)])

    def test_the_macro_holds_each_sheets_fingerprint(self):
        text = (gen_geometry.MACROS / "pid.bas").read_text(encoding="latin-1")
        p, g = model.load(), pg.load()
        for sh in p["sheets"]:
            with self.subTest(sheet=sh):
                got = re.findall(rf'^Const PID_{sh}_HASH\s+As String\s+=\s+"(\w+)"', text, re.M)
                self.assertEqual(got, [encode.sheet_hash(p, g, sh)])
                self.assertIn(f'Case "{sh}": SheetHash = PID_{sh}_HASH', text)

    def test_each_sheet_says_which_strings_it_draws(self):
        """The title block's 'as the twin models it, <scope>': string A only
        where the sheet draws string A's equipment (ids ending in A); the
        calciner, kiln and cooler are one for both strings (16 Nov sheet
        check: every sheet said "string A")."""
        text = (gen_geometry.MACROS / "pid.bas").read_text(encoding="latin-1")
        p = model.load()
        for sh, s in p["sheets"].items():
            with self.subTest(sheet=sh):
                ids = [i for i, e in p["equipment"].items() if e["sheet"] == sh]
                self.assertEqual("string A" in s["scope"], all(i.endswith("A") for i in ids))
                self.assertRegex(text, rf'Const PID_{sh}_SCOPE\s+As String\s+=\s+"{re.escape(s["scope"])}"')
                self.assertIn(f'Case "{sh}": SheetScope = PID_{sh}_SCOPE', text)
        self.assertNotIn('"as the twin models it, string A"', text)

    def test_the_fingerprint_follows_the_records_and_the_code(self):
        import copy
        from unittest import mock
        p, g = model.load(), pg.load()
        base = encode.sheet_hash(p, g, "KI")
        q = copy.deepcopy(p)
        q["connectors"]["OPC-03"]["label"] += " X"
        self.assertNotEqual(encode.sheet_hash(q, g, "KI"), base)
        with mock.patch.object(encode, "macro_code", return_value=encode.macro_code() + "\n' edit"):
            self.assertNotEqual(encode.sheet_hash(p, g, "KI"), base)

    def test_module_declarations_come_before_the_first_procedure(self):
        """VBA: only comments may follow an End Sub, so a module-level
        Dim or Const after the first procedure does not compile."""
        text = (gen_geometry.MACROS / "pid.bas").read_text(encoding="latin-1")
        first = re.search(r"^\s*(?:Private |Public )?(?:Sub|Function) ", text, re.M).start()
        late = re.findall(r"^(?:Dim|Const) \w+", text[first:], re.M)
        self.assertEqual(late, [])

    def test_no_name_collides_case_insensitively(self):
        """VBA is case-insensitive: a Sub called Cell next to a Const CELL
        does not compile, and a local `txt` over a Const TXT silently
        changes what the Const's uses mean. Every module-level name
        (Const, Dim, procedure) is distinct, and no local or parameter
        reuses one."""
        text = (gen_geometry.MACROS / "pid.bas").read_text(encoding="latin-1")
        text = text.replace(" _\n", " ")
        first = re.search(r"^\s*(?:Private |Public )?(?:Sub|Function) ", text, re.M).start()
        head, body = text[:first], text[first:]
        names = [m.lower() for m in re.findall(r"^Const (\w+)", head, re.M)]
        for decl in re.findall(r"^Dim (.*)$", head, re.M):
            names += _declared(decl)
        procs = [m.lower() for m in re.findall(r"^(?:Private |Public )?(?:Sub|Function) (\w+)", body, re.M)]
        everything = names + procs
        dup = sorted({n for n in everything if everything.count(n) > 1})
        self.assertEqual(dup, [], "module-level names used twice")
        local = []
        for decl in re.findall(r"^\s+Dim (.*)$", body, re.M):
            local += _declared(decl)
        local += [m.lower() for m in re.findall(r"^\s+Const (\w+)", body, re.M)]
        local += [m.lower() for m in re.findall(r"By(?:Val|Ref) (\w+)", body)]
        clash = sorted({n for n in local if n in set(everything)})
        self.assertEqual(clash, [], "locals or parameters named like a module-level name")

    def test_the_macro_knows_every_symbol_and_port_the_source_may_use(self):
        text = (gen_geometry.MACROS / "pid.bas").read_text(encoding="latin-1")
        ports = text[text.index("Private Sub PortPos"):text.index("Private Sub RouteLines")]
        blocks = re.split(r'^    Case "(\w+)"\s*$', ports, flags=re.M)
        by_symbol = dict(zip(blocks[1::2], blocks[2::2]))
        draw = text[text.index("Private Sub DrawEquipment"):text.index("Private Sub EquipLabel")]
        for sym, want in symbols.SYMBOLS.items():
            with self.subTest(symbol=sym):
                self.assertIn(f'"{sym}"', draw, "DrawEquipment cannot draw it")
                self.assertIn(sym, by_symbol, "PortPos has no case for it")
                have = set(re.findall(r'Case "(\w+)":', by_symbol[sym]))
                self.assertEqual(have, set(want))

    def test_no_macro_line_nears_the_vba_limit(self):
        text = (gen_geometry.MACROS / "pid.bas").read_text(encoding="latin-1")
        self.assertLess(max(len(l) for l in text.splitlines()), 1000)


class TheValidatorCatchesTest(unittest.TestCase):
    """The checks are not vacuous: break the source and each one fires."""

    def _broken(self, edit):
        import copy
        p = copy.deepcopy(model.load())
        edit(p)
        return validate.validate(p, pg.load())

    def test_an_unknown_tag(self):
        self.assertTrue(self._broken(lambda p: p["equipment"]["C4A"].update(tag="C9")))

    def test_an_unpaired_connector(self):
        self.assertTrue(self._broken(lambda p: p["lines"].pop("G101")))

    def test_a_twin_key_that_does_not_exist(self):
        self.assertTrue(self._broken(lambda p: p["instruments"]["TT-104"].update(key="state:Tg_nonexistent")))

    def test_a_status_that_disagrees_with_the_key(self):
        self.assertTrue(self._broken(lambda p: p["instruments"]["FT-101"].update(status="Modelled")))

    def test_an_instrument_outside_the_scope(self):
        self.assertTrue(self._broken(lambda p: p["instruments"].update(
            {"PT-101": {"var": "x", "key": "state:Tg_preheater", "status": "Modelled", "at": "G103", "mount": "F"}})))

    def test_a_broken_gas_path(self):
        self.assertTrue(self._broken(lambda p: p["lines"].pop("G108")))


class TheCommittedSheetsAreCurrentTest(unittest.TestCase):
    """pid.bas writes geometry/drawings/pid/pid_<SH>.stamp (committed, next
    to the PDF) with the fingerprint it drew from. Unlike the build log it
    is in the repository, so a sheet left stale after a source change
    fails here on every machine."""

    MACRO = {"PH": "preheater", "CA": "calciner", "KI": "kiln", "CO": "cooler"}

    def test_each_stamp_is_the_current_source(self):
        p, g = model.load(), pg.load()
        for sh in p["sheets"]:
            stamp = model.ROOT / "geometry" / "drawings" / "pid" / f"pid_{sh}.stamp"
            hint = f"pid_{sh}.pdf is stale: run geometry/macros/pid.bas -> {self.MACRO[sh]} and commit pdf, dxf, stamp"
            with self.subTest(sheet=sh):
                self.assertTrue(stamp.exists(), hint)
                self.assertEqual(stamp.read_text(encoding="latin-1").strip(), encode.sheet_hash(p, g, sh), hint)


class TheSheetsWereBuiltTest(unittest.TestCase):
    """pid.bas logs 'pid <sheet> built: equipment n, lines n, instruments n,
    connectors n' and a count per layer; skipped until the macro has run here."""

    def test_the_logged_counts(self):
        from tools import gen_drawings
        p = model.load()
        ran = False
        for sh in p["sheets"]:
            log = gen_drawings.LOG_DIR / f"pid_{sh}_build.log"
            if not log.exists():
                continue
            ran = True
            text = log.read_text(encoding="latin-1")
            self.assertNotIn("ABORTED", text)
            self.assertNotIn("WARNING", text)
            n_eq = sum(e["sheet"] == sh for e in p["equipment"].values())
            n_ln = sum(l["sheet"] == sh for l in p["lines"].values())
            n_in = sum((p["lines"][i["at"]]["sheet"] if i["at"] in p["lines"] else p["equipment"][i["at"]]["sheet"]) == sh
                       for i in p["instruments"].values())
            n_oc = sum(sh in (c["from_sheet"], c["to_sheet"]) for c in p["connectors"].values())
            want = f"pid {sh} built: equipment {n_eq}, lines {n_ln}, instruments {n_in}, connectors {n_oc}"
            with self.subTest(sheet=sh):
                self.assertEqual(text.splitlines()[0], want)
                doc = (model.ROOT / "geometry" / "pid" / "pid.md").read_text(encoding="utf-8")
                table = re.findall(rf"^\| {sh} \| (\w+) \| (\d+) \| (\d+) \|$", doc, re.M)
                if table:
                    got = re.findall(r"^layer (\w+): (\d+) lines .*?, (\d+) arcs", text, re.M)
                    self.assertEqual(table, got, "pid.md's layer table is not the log's")
        if not ran:
            self.skipTest("no pid_*_build.log: run geometry/macros/pid.bas")


if __name__ == "__main__":
    unittest.main()
