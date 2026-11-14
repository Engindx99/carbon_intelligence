"""Render a PDF page to PNG so a drawing sheet can be looked at.

    python3 tools/render_pdf.py sheet.pdf out_prefix [dpi] [x0 y0 x1 y1]

The optional box (fractions 0..1 of the page, top-left origin) crops a
region, e.g. 0.5 0 1 0.5 for the top-right quarter. PyMuPDF is read
from ~/.drawing-libs (pip install --target ~/.drawing-libs pymupdf).
"""
import os
import sys

sys.path.insert(0, os.path.expanduser("~/.drawing-libs"))
import pymupdf as fitz  # noqa: E402


def main(argv):
    pdf, prefix = argv[0], argv[1]
    dpi = int(argv[2]) if len(argv) > 2 else 80
    box = [float(v) for v in argv[3:7]] if len(argv) >= 7 else None
    with fitz.open(pdf) as doc:
        for i, page in enumerate(doc):
            r = page.rect
            clip = None
            if box:
                clip = fitz.Rect(r.x0 + box[0] * r.width, r.y0 + box[1] * r.height,
                                 r.x0 + box[2] * r.width, r.y0 + box[3] * r.height)
            out = f"{prefix}_{i + 1}.png"
            page.get_pixmap(dpi=dpi, clip=clip).save(out)
            print(out, int(r.width), "x", int(r.height), "pt")


if __name__ == "__main__":
    main(sys.argv[1:])
