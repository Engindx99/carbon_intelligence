"""
No text on a committed drawing sheet is crossed by a line or printed
into another text, but for the crossings tools/sheet_overlaps.py ALLOW
lists with their reasons (16 Nov 2026 review, item 6).

The sheets are SolidWorks' PDFs (drawings.bas, pid.bas); this reads what
was printed. PyMuPDF lives in ~/.drawing-libs, not in the test
environment: without it the test is skipped.
"""
import os
import unittest

try:
    from tools import sheet_overlaps
except ImportError:  # PyMuPDF missing
    sheet_overlaps = None


@unittest.skipIf(sheet_overlaps is None, "PyMuPDF not found (pip install --target ~/.drawing-libs pymupdf)")
class NoTextCollidesOnASheetTest(unittest.TestCase):

    def test_every_committed_sheet(self):
        sheets = sheet_overlaps.committed_sheets()
        self.assertTrue(sheets)
        for pdf in sheets:
            with self.subTest(sheet=os.path.basename(pdf)):
                self.assertEqual(sheet_overlaps.check(pdf), [])

    def test_every_allowed_crossing_still_happens(self):
        """An ALLOW entry that no longer matches anything is stale: drop it."""
        import tools.sheet_overlaps as so
        saved = dict(so.ALLOW)
        try:
            so.ALLOW.clear()
            seen = set()
            for pdf in so.committed_sheets():
                name = os.path.basename(pdf)
                seen |= {(name, t, k) for k, t, _ in so.check(pdf)}
        finally:
            so.ALLOW.update(saved)
        self.assertEqual(sorted(set(saved) - seen), [])


if __name__ == "__main__":
    unittest.main()
