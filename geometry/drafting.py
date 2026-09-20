"""2-D technical drawings, for any unit.

A drawing here is a VIEW OF THE PARAMETER MODEL, never a second model.
That distinction is the whole reason this module exists: a layout
drawing that carries its own arithmetic is a drawing that can agree
with itself while disagreeing with the geometry it claims to document,
and it is then worse than no drawing at all.

So every dimension, every level and every angle on a sheet is FETCHED
from the spec object by name:

    panel.dim_v(x, z0, z1, "pitch")

`"pitch"` is resolved against the model with `value_of`, and the number
that lands on the paper is `TowerSpec.pitch` itself. Two things follow.

  * A sheet cannot quote a number the geometry package does not hold.
    There is no argument by which a value gets typed in.
  * The DRAWN length and the QUOTED value are compared, and they must
    agree to `AGREEMENT_TOLERANCE_M`, or the call raises. So if the
    outline is plotted from one place and the dimension read from
    another, the sheet does not come out wrong -- it does not come out.

Every quote is also recorded (`Sheet.quotes`), which lets a test walk a
finished sheet and re-resolve each source against a fresh spec. That
test is what keeps the drawing honest after the geometry moves.

UNITS. Metres and degrees, like the rest of the repository. Paper sizes
and line weights are in millimetres and points, because that is what
paper and ink are measured in; they are drafting, not physics, and they
never touch a model coordinate.

NO CAD KERNEL. matplotlib only, so the drawings run in the twin's own
environment -- the same place the layout arithmetic runs.
"""

import math
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402


# ==========================================================
# PAPER
# ==========================================================
SHEET_SIZES_MM = {
    "A4": (297.0, 210.0),
    "A3": (420.0, 297.0),
    "A2": (594.0, 420.0),
    "A1": (841.0, 594.0),
}

# Scales a drawing is allowed to be at. A view is fitted to the
# smallest of these that holds it, so a sheet says 1:500 and means it,
# rather than carrying whatever ratio the bounding box happened to give.
STANDARD_SCALES = (
    1, 2, 5, 10, 20, 25, 50, 75, 100, 125, 150, 200, 250,
    500, 750, 1000, 2000, 5000,
)

MM_PER_INCH = 25.4
POINTS_PER_INCH = 72.0

FRAME_MARGIN_MM = 10.0
FRAME_BINDING_MM = 20.0
TITLE_BLOCK_MM = (180.0, 46.0)

# How far the drawn geometry may differ from the value quoted over it.
# The two come from the same properties, so the real disagreement is
# floating-point noise; anything above this is a drafting error.
AGREEMENT_TOLERANCE_M = 1.0e-6


# ==========================================================
# INK
# ==========================================================
INK = "#1a1a1a"
DIM_INK = "#1f4e79"
CENTRE_INK = "#8c4a4a"
GAS_INK = "#b0442a"
SOLIDS_INK = "#2e6b3f"
FILL = "#ececec"
FRAME_INK = "#000000"
PAPER = "white"

LINE_STYLES = {
    # name           (width pt, dash, colour)
    "visible":       (1.20, "solid", INK),
    "outline":       (0.90, "solid", INK),
    "hidden":        (0.70, (0, (4, 2)), INK),
    "thin":          (0.50, "solid", "#3c3c3c"),
    "centre":        (0.50, (0, (8, 2, 1, 2)), CENTRE_INK),
    "dimension":     (0.50, "solid", DIM_INK),
    "gas":           (0.80, "solid", GAS_INK),
    "solids":        (0.80, "solid", SOLIDS_INK),
    "construction":  (0.40, (0, (1, 2)), "#7a7a7a"),
}

DUCT_INK = {"gas": GAS_INK, "solids": SOLIDS_INK}

TEXT_DIM = 6.0
TEXT_LABEL = 7.0
TEXT_PANEL = 8.5
TEXT_TITLE = 12.0

Z_FILL = 1.0
Z_DUCT = 2.0
Z_OUTLINE = 3.0
Z_CENTRE = 3.5

# A duct that passes BETWEEN the viewer and a vessel has to hide the
# vessel, or the flat projection reads as if the duct went through it.
# Z_FRONT is above every line a cyclone owns -- outline, scroll band,
# vortex finder and axis -- and below the dimensions, which are on the
# paper rather than in the model and are never hidden by anything.
Z_FRONT = 3.6

Z_DIM = 4.0
Z_TEXT = 5.0


# ==========================================================
# READING A VALUE OUT OF THE MODEL
# ==========================================================
_STEP = re.compile(r"^([A-Za-z_]\w*)(?:\(([^()]*)\))?((?:\[-?\d+\])*)$")
_INDEX = re.compile(r"\[(-?\d+)\]")


def value_of(model, source):
    """The value `source` names on `model`.

    The grammar is deliberately tiny -- attributes, integer-argument
    calls and integer indices:

        "pitch"                       TowerSpec.pitch
        "cyclone.cylinder_height"     the cyclone's own property
        "stage_base_z(3)"             a stage's dipleg level
        "meal_line_path(2)[-1][2]"    z of a meal line's entry point

    It is small on purpose. Anything this grammar cannot express is
    something the geometry package does not expose, and the answer to
    that is to expose it there -- not to compute it on the drawing.
    """

    obj = model

    for raw in source.split("."):

        step = raw.strip()
        match = _STEP.match(step)

        if match is None:
            raise ValueError(
                f"drafting: {source!r} is not a readable source; "
                f"the step {step!r} is not name, name(int,...) or [int]"
            )

        name, args, indices = match.groups()

        try:
            obj = getattr(obj, name)
        except AttributeError:
            raise ValueError(
                f"drafting: {source!r} cannot be read from "
                f"{type(model).__name__}: there is no {name!r}. A "
                "drawing may only quote what the geometry package holds"
            ) from None

        if args is not None:
            obj = obj(*[int(a) for a in args.split(",") if a.strip()])

        for index in _INDEX.findall(indices):
            obj = obj[int(index)]

    return float(obj)


def format_length(value):
    """A length, as it is written on a drawing."""

    return f"{value:.3f} m" if abs(value) < 10.0 else f"{value:.2f} m"


def format_level(value):
    """An elevation. The datum is written the way site drawings do."""

    if abs(value) < 5.0e-4:
        return "±0.000"

    return f"{value:+.3f}"


def format_angle(value):
    return f"{value:.1f}°"


@dataclass(frozen=True)
class Quote:
    """One number on a sheet, and where it came from."""

    sheet: str
    panel: str
    kind: str          # "length" | "level" | "angle"
    source: str        # resolvable against the model
    value: float       # what the model returned
    drawn: float       # what the geometry on the paper measures
    unit: str


# ==========================================================
# A VIEW ON A SHEET
# ==========================================================
class Panel:
    """One orthographic view, at one stated scale.

    Model coordinates go straight in. The panel knows its scale, so it
    can also draw something at its true width -- a duct's bore, for
    instance, is a line weight computed from metres.
    """

    def __init__(self, sheet, ax, rect_mm, title):

        self.sheet = sheet
        self.ax = ax
        self.rect_mm = rect_mm
        self.title = title
        self.scale = None

    # ---------- fitting ----------
    @property
    def width_m(self):
        """How much model the panel shows across [m]."""

        self._require_scale()

        return self.rect_mm[2] / 1000.0 * self.scale

    @property
    def points_per_m(self):
        """Paper points per model metre, at this panel's scale."""

        self._require_scale()

        return POINTS_PER_INCH / MM_PER_INCH * (1000.0 / self.scale)

    def _require_scale(self):

        if self.scale is None:
            raise ValueError(
                f"panel {self.title!r}: fit() must be called before "
                "anything is drawn -- the scale sets the line weights"
            )

    def fit(self, xlim, ylim, scale=None, margin=1.06, anchor=(0.5, 0.5)):
        """Choose a standard scale that holds the given model extent."""

        span_x = float(xlim[1] - xlim[0])
        span_y = float(ylim[1] - ylim[0])

        if span_x <= 0.0 or span_y <= 0.0:
            raise ValueError(
                f"panel {self.title!r}: extent must be positive, got "
                f"{span_x} x {span_y} m"
            )

        width_m = self.rect_mm[2] / 1000.0
        height_m = self.rect_mm[3] / 1000.0

        needed = margin * max(span_x / width_m, span_y / height_m)

        if scale is None:

            for candidate in STANDARD_SCALES:
                if candidate >= needed:
                    scale = candidate
                    break

            else:
                raise ValueError(
                    f"panel {self.title!r}: needs 1:{needed:.0f}, which is "
                    f"past the largest standard scale "
                    f"1:{STANDARD_SCALES[-1]}"
                )

        elif scale < needed:
            raise ValueError(
                f"panel {self.title!r}: 1:{scale} does not hold the view; "
                f"it needs at least 1:{needed:.0f}"
            )

        self.scale = scale

        half_x = 0.5 * width_m * scale
        half_y = 0.5 * height_m * scale

        cx = xlim[0] + anchor[0] * span_x + (0.5 - anchor[0]) * 2.0 * half_x
        cy = ylim[0] + anchor[1] * span_y + (0.5 - anchor[1]) * 2.0 * half_y

        self.ax.set_xlim(cx - half_x, cx + half_x)
        self.ax.set_ylim(cy - half_y, cy + half_y)

        self.sheet._panel_fitted(self)

        return self.scale

    # ---------- geometry ----------
    def polyline(self, points, style="visible", zorder=Z_OUTLINE, **kw):

        width, dash, colour = LINE_STYLES[style]

        self.ax.plot(
            [p[0] for p in points],
            [p[1] for p in points],
            linewidth=kw.pop("linewidth", width),
            linestyle=kw.pop("linestyle", dash),
            color=kw.pop("color", colour),
            solid_capstyle="round",
            zorder=zorder,
            **kw,
        )

    def polygon(self, points, style="outline", fill=FILL, zorder=Z_FILL):

        width, dash, colour = LINE_STYLES[style]

        self.ax.add_patch(
            Polygon(
                [(p[0], p[1]) for p in points],
                closed=True,
                facecolor=fill if fill else "none",
                edgecolor=colour,
                linewidth=width,
                linestyle=dash,
                zorder=zorder,
            )
        )

    def circle(self, centre, diameter, style="outline", fill=None,
               zorder=Z_OUTLINE, sections=180):

        radius = 0.5 * diameter
        points = [
            (
                centre[0] + radius * math.cos(2.0 * math.pi * i / sections),
                centre[1] + radius * math.sin(2.0 * math.pi * i / sections),
            )
            for i in range(sections + 1)
        ]

        if fill:
            self.polygon(points, style=style, fill=fill, zorder=zorder - 2.0)
        else:
            self.polyline(points, style=style, zorder=zorder)

    def duct(self, points, bore, kind, label=None, alpha=0.30,
             zorder=Z_DUCT, halo=False):
        """A duct at its true bore, plus its centre-line.

        The round joins are not decoration: geometry/pipes.py closes
        every elbow with a sphere of the same radius, so a round join is
        what the solid actually has.

        `halo` paints the bore in paper first, so the duct hides what it
        covers instead of letting it show through. That is only correct
        where the duct really is in front of the thing it covers, so the
        caller -- which is the only party that knows the depth -- asks
        for it; see `tower_draw.draw_ducts`.
        """

        self._require_scale()

        colour = DUCT_INK[kind]
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        if halo:
            self.ax.plot(
                xs, ys,
                linewidth=bore * self.points_per_m,
                color=PAPER,
                solid_capstyle="round",
                solid_joinstyle="round",
                zorder=zorder - 0.05,
            )

        self.ax.plot(
            xs, ys,
            linewidth=bore * self.points_per_m,
            color=colour,
            alpha=alpha,
            solid_capstyle="round",
            solid_joinstyle="round",
            zorder=zorder,
        )

        self.polyline(points, style=kind, zorder=zorder + 0.1)

        if label:
            self.ax.text(
                xs[-1], ys[-1], f" {label}",
                fontsize=TEXT_DIM, color=colour, zorder=Z_TEXT, clip_on=True,
                ha="left", va="center",
            )

    def centre_line(self, points):

        self.polyline(points, style="centre", zorder=Z_CENTRE)

    def label(self, x, y, text, size=TEXT_LABEL, ha="left", va="center",
              colour=INK, **kw):

        self.ax.text(
            x, y, text, fontsize=size, color=colour,
            ha=ha, va=va, zorder=Z_TEXT, clip_on=True, **kw,
        )

    def leader(self, point, offset, text, size=TEXT_DIM, colour=INK):
        """A note pointing at something."""

        end = (point[0] + offset[0], point[1] + offset[1])

        self.polyline([point, end], style="thin", zorder=Z_DIM)

        ha = "left" if offset[0] >= 0.0 else "right"
        pad = 0.01 * self.width_m

        self.ax.text(
            end[0] + (pad if offset[0] >= 0.0 else -pad), end[1], text,
            fontsize=size, color=colour, ha=ha, va="center", zorder=Z_TEXT, clip_on=True,
        )

    # ---------- dimensions: every one of them is a quote ----------
    def _quote(self, kind, source, drawn, unit):

        return self.sheet.quote(self.title, kind, source, drawn, unit)

    def _arrowed(self, a, b):

        width, _, colour = LINE_STYLES["dimension"]

        self.ax.annotate(
            "", xy=a, xytext=b,
            arrowprops=dict(
                arrowstyle="<|-|>,head_length=0.32,head_width=0.11",
                linewidth=width, color=colour,
                shrinkA=0.0, shrinkB=0.0,
            ),
            zorder=Z_DIM,
        )

    def dim_h(self, x1, x2, y, source, above=True, extend_to=None,
              text=None, oriented=False):
        """A horizontal dimension whose value comes from the model.

        `oriented` keeps the sign of the run, for a source that is a
        signed coordinate rather than a size -- `riser_approach_y` is
        -5.563 m and quoting it as +5.563 would be quoting a different
        number.
        """

        drawn = (x2 - x1) if oriented else abs(x2 - x1)
        value, _ = self._quote("length", source, drawn, "m")

        if extend_to is not None:
            for x in (x1, x2):
                self.polyline(
                    [(x, extend_to), (x, y)], style="thin", zorder=Z_DIM,
                )

        self._arrowed((x1, y), (x2, y))

        pad = 0.012 * self.width_m

        self.ax.text(
            0.5 * (x1 + x2), y + (pad if above else -pad),
            text or format_length(value),
            fontsize=TEXT_DIM, color=DIM_INK, ha="center",
            va="bottom" if above else "top", zorder=Z_TEXT, clip_on=True,
        )

        return value

    def dim_v(self, x, y1, y2, source, right=True, extend_to=None,
              text=None, oriented=False):
        """A vertical dimension whose value comes from the model.

        `oriented` as in `dim_h`: it keeps the sign, for a source that
        is a signed coordinate rather than a size.
        """

        drawn = (y2 - y1) if oriented else abs(y2 - y1)
        value, _ = self._quote("length", source, drawn, "m")

        if extend_to is not None:
            for y in (y1, y2):
                self.polyline(
                    [(extend_to, y), (x, y)], style="thin", zorder=Z_DIM,
                )

        self._arrowed((x, y1), (x, y2))

        pad = 0.010 * self.width_m

        self.ax.text(
            x + (pad if right else -pad), 0.5 * (y1 + y2),
            text or format_length(value),
            fontsize=TEXT_DIM, color=DIM_INK, rotation=90.0,
            ha="left" if right else "right", va="center", zorder=Z_TEXT, clip_on=True,
        )

        return value

    def dim_aligned(self, a, b, offset, source, text=None, extend=True):
        """A dimension along the line a-b, quoted from the model.

        For a distance that is neither an x nor a y. `riser_reach` is
        the one this was written for: the riser column stands off its
        cyclone's axis diagonally, and dimensioning it as a horizontal
        or a vertical would quote a projection of it, not the distance.

        `offset` is how far the dimension line sits to the LEFT of a->b.
        """

        drawn = math.hypot(b[0] - a[0], b[1] - a[1])
        value, _ = self._quote("length", source, drawn, "m")

        nx, ny = -(b[1] - a[1]) / drawn, (b[0] - a[0]) / drawn

        a_off = (a[0] + offset * nx, a[1] + offset * ny)
        b_off = (b[0] + offset * nx, b[1] + offset * ny)

        if extend:
            for point, shifted in ((a, a_off), (b, b_off)):
                self.polyline(
                    [point, shifted], style="thin", zorder=Z_DIM,
                )

        self._arrowed(a_off, b_off)

        pad = 0.012 * self.width_m
        angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))

        if angle > 90.0 or angle <= -90.0:
            angle += 180.0

        self.ax.text(
            0.5 * (a_off[0] + b_off[0]) + pad * nx,
            0.5 * (a_off[1] + b_off[1]) + pad * ny,
            text or format_length(value),
            fontsize=TEXT_DIM, color=DIM_INK, rotation=angle,
            rotation_mode="anchor",
            ha="center", va="bottom", zorder=Z_TEXT, clip_on=True,
        )

        return value

    def dim_angle(self, vertex, radius, from_deg, to_deg, source,
                  text=None):
        """An angle, quoted from the model in degrees."""

        value, _ = self._quote(
            "angle", source, abs(to_deg - from_deg), "deg",
        )

        span = [
            (
                vertex[0] + radius * math.cos(math.radians(a)),
                vertex[1] + radius * math.sin(math.radians(a)),
            )
            for a in [
                from_deg + (to_deg - from_deg) * i / 48.0
                for i in range(49)
            ]
        ]

        self.polyline(span, style="dimension", zorder=Z_DIM)

        mid = math.radians(0.5 * (from_deg + to_deg))

        self.ax.text(
            vertex[0] + 1.18 * radius * math.cos(mid),
            vertex[1] + 1.18 * radius * math.sin(mid),
            text or format_angle(value),
            fontsize=TEXT_DIM, color=DIM_INK,
            ha="center", va="center", zorder=Z_TEXT, clip_on=True,
        )

        return value

    def level(self, x_from, z, source, x_text, text=None):
        """An elevation mark: the level triangle site drawings use.

        `z` is where the mark is drawn and `source` is what the model
        says that level is. They are checked against each other, which
        is the point.
        """

        value, _ = self._quote("level", source, z, "m")

        self.polyline([(x_from, z), (x_text, z)], style="thin", zorder=Z_DIM)

        size = 0.012 * self.width_m
        tip = (x_text, z)

        self.ax.add_patch(
            Polygon(
                [
                    tip,
                    (x_text - 1.1 * size, z + 1.5 * size),
                    (x_text + 1.1 * size, z + 1.5 * size),
                ],
                closed=True,
                facecolor="none",
                edgecolor=DIM_INK,
                linewidth=LINE_STYLES["dimension"][0],
                zorder=Z_DIM,
            )
        )

        self.ax.text(
            x_text + 1.6 * size, z + 0.4 * size,
            text or format_level(value),
            fontsize=TEXT_DIM, color=DIM_INK,
            ha="left", va="bottom", zorder=Z_TEXT, clip_on=True,
        )

        return value


# ==========================================================
# THE SHEET
# ==========================================================
class Sheet:
    """A framed drawing sheet with a title block.

    It owns the model. Panels quote through it, so the whole sheet's
    numbers come from one object and `Sheet.quotes` is the record of
    every one of them.
    """

    def __init__(self, model, title, unit, number, source_note,
                 size="A3", subtitle="", datum=""):

        if size not in SHEET_SIZES_MM:
            raise ValueError(
                f"unknown sheet size {size!r}; have "
                f"{sorted(SHEET_SIZES_MM)}"
            )

        self.model = model
        self.title = title
        self.unit = unit
        self.number = number
        self.source_note = source_note
        self.subtitle = subtitle
        self.datum = datum

        self.width_mm, self.height_mm = SHEET_SIZES_MM[size]
        self.size = size

        self.quotes = []
        self.panels = []

        self.fig = plt.figure(
            figsize=(self.width_mm / MM_PER_INCH, self.height_mm / MM_PER_INCH)
        )
        self.fig.patch.set_facecolor("white")

        self.paper = self.fig.add_axes([0.0, 0.0, 1.0, 1.0])
        self.paper.set_xlim(0.0, self.width_mm)
        self.paper.set_ylim(0.0, self.height_mm)
        self.paper.set_axis_off()

        self._draw_frame()

    # ---------- the sheet's own furniture ----------
    @property
    def frame_mm(self):
        """(x, y, w, h) of the drawing frame, in millimetres."""

        return (
            FRAME_BINDING_MM,
            FRAME_MARGIN_MM,
            self.width_mm - FRAME_BINDING_MM - FRAME_MARGIN_MM,
            self.height_mm - 2.0 * FRAME_MARGIN_MM,
        )

    def _rect(self, rect_mm, linewidth=0.5, colour=FRAME_INK):

        x, y, w, h = rect_mm

        self.paper.plot(
            [x, x + w, x + w, x, x],
            [y, y, y + h, y + h, y],
            linewidth=linewidth, color=colour, zorder=Z_OUTLINE,
        )

    def _draw_frame(self):

        self._rect(self.frame_mm, linewidth=0.9)

        fx, fy, fw, fh = self.frame_mm
        tw, th = TITLE_BLOCK_MM
        tx, ty = fx + fw - tw, fy

        self._rect((tx, ty, tw, th), linewidth=0.9)

        self.paper.plot(
            [tx, tx + tw], [ty + th - 11.0, ty + th - 11.0],
            linewidth=0.5, color=FRAME_INK,
        )
        self.paper.plot(
            [tx, tx + tw], [ty + 12.5, ty + 12.5],
            linewidth=0.5, color=FRAME_INK,
        )

        self.paper.text(
            tx + 4.0, ty + th - 6.0,
            "CARBON INTELLIGENCE  —  PYROPROCESS DIGITAL TWIN",
            fontsize=7.0, color=INK, va="center",
        )
        self.paper.text(
            tx + 4.0, ty + th - 21.0, self.title,
            fontsize=TEXT_TITLE, color=INK, va="center", fontweight="bold",
        )
        self.paper.text(
            tx + 4.0, ty + th - 30.0, self.subtitle,
            fontsize=7.0, color="#444444", va="center",
        )
        self.paper.text(
            tx + 4.0, ty + 8.5,
            f"BİRİM: {self.unit}     SI: metre / derece",
            fontsize=6.5, color=INK, va="center",
        )
        self.paper.text(
            tx + 4.0, ty + 4.0,
            f"KAYNAK: {self.source_note}",
            fontsize=6.0, color="#444444", va="center",
        )
        self.paper.text(
            tx + tw - 4.0, ty + 8.5, self.number,
            fontsize=8.0, color=INK, va="center", ha="right",
            fontweight="bold",
        )

        if self.datum:
            self.paper.text(
                tx + tw - 4.0, ty + 4.0, self.datum,
                fontsize=6.0, color="#444444", va="center", ha="right",
            )

        # The sentence that keeps a drawing from being read as a design
        # authority it is not.
        self.paper.text(
            fx + 2.0, fy + fh + 3.0,
            "Bu sayfadaki her ölçü, kot ve açı geometry/ paketinden "
            "okunmuştur; çizimde bağımsız yerleşim hesabı yoktur.",
            fontsize=6.0, color="#444444", va="bottom",
        )

    # ---------- panels ----------
    def panel(self, rect_mm, title, border=True):

        x, y, w, h = rect_mm

        ax = self.fig.add_axes(
            [
                x / self.width_mm,
                y / self.height_mm,
                w / self.width_mm,
                h / self.height_mm,
            ]
        )
        ax.set_aspect("equal", adjustable="box")
        ax.set_axis_off()

        if border:
            self._rect(rect_mm, linewidth=0.4, colour="#9a9a9a")

        panel = Panel(self, ax, rect_mm, title)
        self.panels.append(panel)

        return panel

    def _panel_fitted(self, panel):
        """Write a panel's caption once it knows its scale."""

        x, y, w, _ = panel.rect_mm

        self.paper.text(
            x + 0.5 * w, y - 6.0,
            f"{panel.title}        ÖLÇEK 1:{panel.scale}",
            fontsize=TEXT_PANEL, color=INK, ha="center", va="center",
            fontweight="bold",
        )

    # ---------- text blocks ----------
    def text_block(self, rect_mm, title, lines, size=6.2, leading=3.6,
                   border=True):
        """A table or a note block, in sheet millimetres.

        With a height of None the block sizes itself to its content and
        `y` is read as the TOP edge instead of the bottom, so blocks can
        be stacked down a column from the return value. A box that is
        mostly empty is a box that was measured by hand.
        """

        x, y, w, h = rect_mm

        if h is None:
            h = 13.0 + leading * len(lines)
            y = y - h

        if border:
            self._rect((x, y, w, h), linewidth=0.4, colour="#9a9a9a")

        cursor = y + h - 6.0

        self.paper.text(
            x + 3.0, cursor, title,
            fontsize=7.0, color=INK, va="center", fontweight="bold",
        )

        self.paper.plot(
            [x + 3.0, x + w - 3.0], [cursor - 3.0, cursor - 3.0],
            linewidth=0.4, color="#9a9a9a",
        )

        cursor -= 7.0

        for line in lines:
            self.paper.text(
                x + 3.0, cursor, line,
                fontsize=size, color=INK, va="center",
                family="DejaVu Sans Mono",
            )
            cursor -= leading

        return y

    # ---------- quoting ----------
    def quote(self, panel_title, kind, source, drawn, unit):
        """Resolve `source` on the model and check the drawing against it."""

        value = value_of(self.model, source)

        if abs(value - drawn) > AGREEMENT_TOLERANCE_M:
            raise ValueError(
                f"{self.number} / {panel_title}: the geometry drawn for "
                f"{source!r} measures {drawn:.9f} {unit} but the model "
                f"says {value:.9f} {unit}. The drawing and the parameter "
                "model have diverged; fix the view, do not re-type the "
                "number"
            )

        self.quotes.append(
            Quote(
                sheet=self.number,
                panel=panel_title,
                kind=kind,
                source=source,
                value=value,
                drawn=drawn,
                unit=unit,
            )
        )

        return value, self.quotes[-1]

    def quote_report(self):
        """Every number on the sheet, with the source it was read from."""

        out = [f"{self.number}  {self.title}", "-" * 72]

        for q in self.quotes:
            out.append(
                f"  {q.kind:<7}{q.source:<34}"
                f"{q.value:>12.4f} {q.unit:<4}{q.panel}"
            )

        return "\n".join(out)

    # ---------- output ----------
    def save(self, path):

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self.fig.savefig(path, dpi=200, facecolor="white")

        return path

    def close(self):

        plt.close(self.fig)


def save_pdf(sheets, path):
    """All the sheets, in order, as one drawing set."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(path) as pdf:
        for sheet in sheets:
            pdf.savefig(sheet.fig, facecolor="white")

    return path
