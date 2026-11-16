"""Find text that collides on a drawing sheet: text over text, or a line
drawn through the letters.

    python3 tools/sheet_overlaps.py                 every committed sheet
    python3 tools/sheet_overlaps.py sheet.pdf ...   these sheets

Read from the PDF the macros write (PyMuPDF from ~/.drawing-libs, as
tools/render_pdf.py), so what is checked is what is printed, not what
the macro meant to place. The rules (16 Nov 2026 review, item 6):

- a text's box is its glyph core: the span's box less the ascent and
  descent bands across the writing direction, so a leader that touches
  the text's edge is not a crossing;
- a line parallel to the writing (a dimension line under its value, an
  underline) is not a crossing; one across or oblique through the core is;
- two texts collide when their half-shrunk boxes overlap (catches two
  tags printed into one another, and a tag glued onto a line flag);
- the parameter table, notes, title block and frame (the right-hand
  panel, the border strips) are not checked: they are ruled tables;
- PyMuPDF joins texts on one baseline into one span ("3130 E  3871 E");
  a run of two or more spaces splits it again, the box shared out by
  character count along the writing.

ALLOW lists the crossings accepted on purpose, each with its reason.
"""
import glob
import math
import os
import re
import sys

sys.path.insert(0, os.path.expanduser("~/.drawing-libs"))
import pymupdf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEETS = os.path.join(ROOT, "geometry", "drawings")

PANEL_X = 0.765          # the right-hand panel (notes, table, title) starts here [page width]
CORE_ACROSS = 0.30       # ascent / descent band dropped from each side, across the writing
CORE_ALONG = 0.04        # side bearing dropped at each end, along the writing
TT_ACROSS = 0.15         # text against text: half the band, so glued lines still count
PARALLEL_SIN = 0.17      # |sin| of the angle under which a line runs with the text (~10 deg)
MIN_LINE = 0.5           # [pt] shorter segments are arrowhead or hatch stubs' ends

# (sheet file, text, kind) -> why it is accepted
ALLOW = {
    ("C1.pdf", "80 E", "line"): "detail B: the vortex finder wall, hatched on both sides; no clear place inside",
    ("C4.pdf", "B", "line"): "detail circle's letter, placed by SolidWorks inside the section",
    ("C5.pdf", "B", "line"): "detail circle's letter, placed by SolidWorks inside the section",
}


def _spans(page):
    """(text, core box, half box, angle) for every text on the drawing field."""
    W, H = page.rect.width, page.rect.height
    out = []
    for b in page.get_text("dict")["blocks"]:
        for line in b.get("lines", []):
            dx, dy = line["dir"]
            horiz = abs(dx) >= abs(dy)
            ang = math.atan2(dy, dx)
            for s in line["spans"]:
                raw = s["text"]
                if not raw.strip() or "SOLIDWORKS" in raw:
                    continue
                x0, y0, x1, y1 = s["bbox"]
                if x0 > PANEL_X * W or y1 < 0.02 * H or y0 > 0.975 * H or x1 < 0.03 * W:
                    continue
                # split a joined span at runs of 2+ spaces, sharing the box out along the writing
                n = len(raw)
                for m in re.finditer(r"\S(?:.*?\S)?(?=\s{2,}|\s*$)", raw):
                    t = m.group(0)
                    a, z = m.start() / n, m.end() / n
                    if horiz:
                        bx = (x0 + a * (x1 - x0), y0, x0 + z * (x1 - x0), y1) if dx > 0 else \
                             (x1 - z * (x1 - x0), y0, x1 - a * (x1 - x0), y1)
                    else:
                        bx = (x0, y1 - z * (y1 - y0), x1, y1 - a * (y1 - y0)) if dy < 0 else \
                             (x0, y0 + a * (y1 - y0), x1, y0 + z * (y1 - y0))
                    out.append((t, _shrink(bx, horiz, CORE_ACROSS), _shrink(bx, horiz, TT_ACROSS), ang))
    return out


def _shrink(b, horiz, across):
    x0, y0, x1, y1 = b
    w, h = x1 - x0, y1 - y0
    if horiz:
        return (x0 + CORE_ALONG * w, y0 + across * h, x1 - CORE_ALONG * w, y1 - across * h)
    return (x0 + across * w, y0 + CORE_ALONG * h, x1 - across * w, y1 - CORE_ALONG * h)


def _segments(page):
    segs = []
    for d in page.get_drawings():
        # a dashed path is a centre or hidden line: printed as dashes from one
        # long segment (C1's axis is one 853 pt line), its gaps fall where
        # they fall; values on a centreline are accepted (user, 16 Nov 2026)
        if d.get("dashes") and d["dashes"] not in ("[] 0", "[] 0.0"):
            continue
        for it in d["items"]:
            if it[0] == "l":
                segs.append(((it[1].x, it[1].y), (it[2].x, it[2].y)))
            elif it[0] == "c":
                segs.append(((it[1].x, it[1].y), (it[4].x, it[4].y)))
            elif it[0] == "re":
                r = it[1]
                segs += [((r.x0, r.y0), (r.x1, r.y0)), ((r.x1, r.y0), (r.x1, r.y1)),
                         ((r.x1, r.y1), (r.x0, r.y1)), ((r.x0, r.y1), (r.x0, r.y0))]
    return segs


def _overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def _crosses(box, p, q):
    """Segment p-q enters the box (Liang-Barsky)."""
    x0, y0, x1, y1 = box
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pp == 0:
            if qq < 0:
                return False
        else:
            t = qq / pp
            if pp < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    return t0 < t1


def check(pdf):
    """Collisions on one sheet, not in ALLOW: [(kind, text, detail)]."""
    name = os.path.basename(pdf)
    with pymupdf.open(pdf) as doc:
        page = doc[0]
        spans, segs = _spans(page), _segments(page)
    found = []
    for i, (ta, core, half, ang) in enumerate(spans):
        for tb, _, half_b, _ in spans[i + 1:]:
            if _overlap(half, half_b) and (name, ta, "text") not in ALLOW:
                found.append(("text", ta, tb))
        hits = 0
        for p, q in segs:
            if math.hypot(q[0] - p[0], q[1] - p[1]) < MIN_LINE:
                continue
            if abs(math.sin(math.atan2(q[1] - p[1], q[0] - p[0]) - ang)) < PARALLEL_SIN:
                continue
            if _crosses(core, p, q):
                hits += 1
        if hits and (name, ta, "line") not in ALLOW:
            found.append(("line", ta, f"{hits} line(s) through it"))
    return found


def committed_sheets():
    return sorted(glob.glob(os.path.join(SHEETS, "*", "*.pdf")))


def main(argv):
    pdfs = argv or committed_sheets()
    bad = 0
    for pdf in pdfs:
        found = check(pdf)
        bad += len(found)
        print(f"{os.path.basename(pdf)}: {'clean' if not found else f'{len(found)} collision(s)'}")
        for kind, t, detail in found:
            print(f"    {kind:5s} {t!r}: {detail}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
