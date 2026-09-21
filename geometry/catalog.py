"""Published plant dimensions, and where each one came from.

Every dimension is a `Measure` that carries its provenance:

    published               stated in the source
    derived_from_reference  a published value times ONE named, dimensionless
                            ratio of the FLS reference tower
    model_assumption        stated in the source, but as that source's own
                            modelling assumption rather than a measurement

A dimension no source gives is None. Nothing here is computed from
capacity, flow, velocity, area or residence time, and there is no
scaling rule: `derive` accepts only the ratios in FLS_RATIOS, which are
the ones geometry/SOURCES.md lists.

All lengths are metres. `D` is the EFFECTIVE inner diameter (inside the
refractory), which is what bounds the fluid volume. `shell_D` is the
steel shell's inner diameter, which is what vendors quote as Phi.
"""

from dataclasses import dataclass, fields
import math


PUBLISHED = "published"
DERIVED = "derived_from_reference"
MODEL_ASSUMPTION = "model_assumption"

BASES = (PUBLISHED, DERIVED, MODEL_ASSUMPTION)


# Assumptions a value can rest on. The report prints them next to it.
W_IN_ASSUMPTION = (
    "FLS inlet width w_in = 0.4 r_c is the paper's modelling assumption, "
    "not a measured dimension"
)
C1_TRANSFER_ASSUMPTION = (
    "transfer: FLS Cy1 is a single top cyclone, this line's C1 is a "
    "multi-cyclone stage"
)

# Not an assumption: stated by the source. Table 7 of arXiv 2504.02886
# connects R_k's gas inlet to Cy(k+1)'s outlet (A_x,cy(k+1)/A_in,rk)
# and R_k's outlet to Cy(k) (A_out,rk/A_in,cyk).
RISER_MAPPING_REF = "connection: FLS Table 7, R_k from Cy(k+1) to Cy(k)"


SOURCES = {
    "PF1500": (
        "Jiangsu Pengfei, 1500 t/d line",
        "http://www.cementplant-engineering.com/products/"
        "cement-production-line/77.html",
    ),
    "PF2500": (
        "Jiangsu Pengfei, line page titled 3000tpd, kiln system 2500 t/d",
        "https://www.cementmachinery.com/Cement_Machinery/products/"
        "Production_line_EP_EPC/Cement_Production_Line/2020/0331/2670.html",
    ),
    "HFC2500": (
        "Hefei institute, HFC2500t/d preheater-calciner design, 2005",
        "https://m.ccement.com/news/content/700825.html",
    ),
    "PF5000": (
        "Jiangsu Pengfei, 5000 t/d line",
        "https://jspengfei.en.made-in-china.com/product/BewmtGNcXDha/"
        "China-5000t-D-Cement-Production-Line.html",
    ),
    "FLS": (
        "Svensen et al., FLSmidth reference scenario, arXiv 2504.02886, "
        "Table 8",
        "https://arxiv.org/abs/2504.02886",
    ),
}


@dataclass(frozen=True)
class Measure:
    value: float
    basis: str
    ref: str
    assumptions: tuple = ()

    def __post_init__(self):

        if self.basis not in BASES:
            raise ValueError(f"unknown basis {self.basis!r}")

        if not (math.isfinite(self.value) and self.value > 0.0):
            raise ValueError(f"{self.ref}: value must be positive, got {self.value}")

        if not self.ref:
            raise ValueError("every Measure needs a ref")


def published(value, ref, assumptions=()):
    return Measure(float(value), PUBLISHED, ref, tuple(assumptions))


def model_assumption(value, ref, assumption):
    return Measure(float(value), MODEL_ASSUMPTION, ref, (assumption,))


# ---------------------------------------------------------------------
# FLS reference tower, arXiv 2504.02886 Table 8, as printed [m, m^2]
# ---------------------------------------------------------------------

FLS_CYCLONES = {
    1: dict(h_t=18.28, h_c=7.43, h_x=3.45, A_in=10.95, r_c=3.45, r_r=3.59, r_d=0.32, r_x=1.92, w_in=1.38),
    2: dict(h_t=11.38, h_c=7.28, h_x=3.41, A_in=13.34, r_c=3.41, r_r=3.59, r_d=0.45, r_x=2.43, w_in=1.37),
    3: dict(h_t=11.24, h_c=7.79, h_x=3.38, A_in=13.70, r_c=3.38, r_r=3.59, r_d=0.45, r_x=2.48, w_in=1.35),
    4: dict(h_t=11.98, h_c=8.13, h_x=3.53, A_in=14.83, r_c=3.51, r_r=3.74, r_d=0.45, r_x=2.58, w_in=1.41),
    5: dict(h_t=11.94, h_c=8.09, h_x=3.54, A_in=14.83, r_c=3.54, r_r=3.74, r_d=0.45, r_x=2.58, w_in=1.42),
}

# R1..R4; which cyclones each connects is stated in Table 7
# (RISER_MAPPING_REF). R5 (61 m, r_c 1.13 m) runs from the cooler to
# the calciner in Table 7 and the text implies it is the tertiary pipe,
# without saying so; it is not used (no tertiary duct, SOURCES.md).
FLS_RISERS = {
    1: dict(h_tot=21.38, h_cl=4.83, r_c=2.45, r_r=2.47, r_u=1.72),
    2: dict(h_tot=19.38, h_cl=4.18, r_c=2.45, r_r=2.47, r_u=1.90),
    3: dict(h_tot=20.37, h_cl=4.18, r_c=2.55, r_r=2.57, r_u=1.90),
    4: dict(h_tot=19.87, h_cl=4.37, r_c=2.55, r_r=2.57, r_u=1.99),
}

FLS_CALCINER = dict(h_tot=33.00, r_c=3.08, r_r=3.29)
FLS_KILN = dict(L=51.0, r_c=1.98, r_r=2.18, rpm=4.0)
FLS_COOLER = dict(L=36.0, w=4.0)


def _cyclone_ratios(stage):

    c = FLS_CYCLONES[stage]
    D = 2.0 * c["r_c"]

    return {
        "eff_over_shell": c["r_c"] / c["r_r"],
        "barrel_h/D": (c["h_t"] - c["h_c"]) / D,
        "cone_h/D": c["h_c"] / D,
        "vortex_len/D": c["h_x"] / D,
        "vortex_D/D": c["r_x"] / c["r_c"],
        "dust_D/D": c["r_d"] / c["r_c"],
        "inlet_w/D": c["w_in"] / D,
        "inlet_h/D": c["A_in"] / c["w_in"] / D,
    }


# The ONLY ratios `derive` accepts: (name, key) -> value. The key is
# the FLS cyclone stage, the riser number, or None.
FLS_RATIOS = {}

for _stage in FLS_CYCLONES:
    for _name, _value in _cyclone_ratios(_stage).items():
        FLS_RATIOS[(_name, _stage)] = _value

# R_k's diameter over that of the cyclone it leaves, Cy(k+1): the
# pairing is Table 7's (RISER_MAPPING_REF), not an assumption.
for _k, _riser in FLS_RISERS.items():
    FLS_RATIOS[("riser_D/D_src", _k)] = (
        _riser["r_c"] / FLS_CYCLONES[_k + 1]["r_c"]
    )

FLS_RATIOS[("calciner_eff_over_shell", None)] = (
    FLS_CALCINER["r_c"] / FLS_CALCINER["r_r"]
)
FLS_RATIOS[("calciner_H/D", None)] = (
    FLS_CALCINER["h_tot"] / (2.0 * FLS_CALCINER["r_c"])
)
FLS_RATIOS[("kiln_eff_over_shell", None)] = FLS_KILN["r_c"] / FLS_KILN["r_r"]


# Assumptions a ratio carries into every value derived from it.
_RATIO_ASSUMPTIONS = {
    "inlet_w/D": (W_IN_ASSUMPTION,),
    "inlet_h/D": (W_IN_ASSUMPTION,),
}


def derive(base, ratio, key=None, assumptions=()):
    """`base` times one named FLS ratio, marked derived_from_reference."""

    if (ratio, key) not in FLS_RATIOS:
        raise KeyError(f"FLS ratio {ratio}[{key}] is not defined in SOURCES.md")

    label = ratio if key is None else f"{ratio}[{key}]"
    carried = base.assumptions + _RATIO_ASSUMPTIONS.get(ratio, ()) + tuple(assumptions)

    return Measure(
        base.value * FLS_RATIOS[(ratio, key)],
        DERIVED,
        f"{base.ref} x FLS:{label}",
        tuple(dict.fromkeys(carried)),
    )


# ---------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CycloneStage:
    """One cyclone of stage C<stage>; `count` of them work in parallel."""

    stage: int
    count: int
    shell_D: Measure = None
    D: Measure = None
    barrel_h: Measure = None
    cone_h: Measure = None
    vortex_len: Measure = None
    vortex_D: Measure = None
    dust_D: Measure = None
    inlet_w: Measure = None
    inlet_h: Measure = None
    inlet_area: Measure = None


@dataclass(frozen=True)
class Duct:
    """Riser R<name>: from C<from_stage>'s gas outlet to C<to_stage>."""

    name: str
    from_stage: int
    to_stage: int
    shell_D: Measure = None
    D: Measure = None
    length: Measure = None
    end_cone_len: Measure = None
    end_D: Measure = None


@dataclass(frozen=True)
class Vessel:
    shell_D: Measure = None
    D: Measure = None
    length: Measure = None


@dataclass(frozen=True)
class Kiln:
    shell_D: Measure = None
    D: Measure = None
    length: Measure = None
    slope_pct: Measure = None
    speed_min_rpm: Measure = None
    speed_max_rpm: Measure = None
    speed_operating_rpm: Measure = None


@dataclass(frozen=True)
class Cooler:
    grate_area: Measure = None
    length: Measure = None
    width: Measure = None


@dataclass(frozen=True)
class ReferenceLine:
    key: str
    capacity_t_d: Measure
    strings: int
    kiln: Kiln
    cooler: Cooler
    cyclones: tuple
    ducts: tuple
    calciner: Vessel
    gooseneck: Vessel

    def measures(self):
        """Every (path, Measure-or-None) in the line, in a fixed order."""

        out = [("capacity_t_d", self.capacity_t_d)]

        for name, part in (
            ("kiln", self.kiln),
            ("cooler", self.cooler),
            ("calciner", self.calciner),
            ("gooseneck", self.gooseneck),
        ):
            out += [(f"{name}.{f.name}", getattr(part, f.name)) for f in fields(part)]

        for c in self.cyclones:
            out += [
                (f"C{c.stage}.{f.name}", getattr(c, f.name))
                for f in fields(c)
                if f.name not in ("stage", "count")
            ]

        for d in self.ducts:
            out += [
                (f"{d.name}.{f.name}", getattr(d, f.name))
                for f in fields(d)
                if f.name not in ("name", "from_stage", "to_stage")
            ]

        return out


# ---------------------------------------------------------------------
# Vendor lines: published shells and effective diameters, the rest
# through the named FLS ratios, stage C<k> <-> FLS Cy<k>
# ---------------------------------------------------------------------

def _vendor_cyclone(stage, count, shell_D, D):
    """A stage whose shell (and possibly effective) diameter is published.

    With no published effective diameter, it is the shell times the FLS
    lining ratio. Every other length is D times its FLS ratio.
    """

    extra = (C1_TRANSFER_ASSUMPTION,) if stage == 1 else ()

    if D is None:
        D = derive(shell_D, "eff_over_shell", stage, extra)

    def r(name):
        return derive(D, name, stage, extra)

    return CycloneStage(
        stage=stage,
        count=count,
        shell_D=shell_D,
        D=D,
        barrel_h=r("barrel_h/D"),
        cone_h=r("cone_h/D"),
        vortex_len=r("vortex_len/D"),
        vortex_D=r("vortex_D/D"),
        dust_D=r("dust_D/D"),
        inlet_w=r("inlet_w/D"),
        inlet_h=r("inlet_h/D"),
    )


def _vendor_kiln(ref, shell_D, length, slope_pct, rpm_min, rpm_max):

    shell = published(shell_D, ref)

    return Kiln(
        shell_D=shell,
        D=derive(shell, "kiln_eff_over_shell"),
        length=published(length, ref),
        slope_pct=published(slope_pct, ref),
        speed_min_rpm=published(rpm_min, ref),
        speed_max_rpm=published(rpm_max, ref),
    )


def _risers_from_ratio(cyclones):
    """Effective riser diameters from the cyclone each riser leaves.

    Only the diameter has a defined ratio. Length, end cone and end
    diameter have none and stay None.
    """

    by_stage = {c.stage: c for c in cyclones}

    return tuple(
        Duct(
            name=f"R{k}",
            from_stage=k + 1,
            to_stage=k,
            D=derive(by_stage[k + 1].D, "riser_D/D_src", k),
        )
        for k in (1, 2, 3, 4)
    )


def _line_1500():

    ref = "PF1500"
    shells = {1: (2, 4.3), 2: (1, 5.6), 3: (1, 5.6), 4: (1, 5.9), 5: (1, 5.9)}

    cyclones = tuple(
        _vendor_cyclone(s, n, published(d, ref), None)
        for s, (n, d) in shells.items()
    )

    calciner_shell = published(6.3, ref)
    calciner_D = derive(calciner_shell, "calciner_eff_over_shell")

    return ReferenceLine(
        key="1500",
        capacity_t_d=published(1500.0, ref),
        strings=1,
        kiln=_vendor_kiln(ref, 3.5, 54.0, 4.0, 0.4, 3.96),
        cooler=Cooler(grate_area=published(61.8, ref)),
        cyclones=cyclones,
        ducts=_risers_from_ratio(cyclones),
        calciner=Vessel(
            shell_D=calciner_shell,
            D=calciner_D,
            length=derive(calciner_D, "calciner_H/D"),
        ),
        gooseneck=Vessel(),
    )


def _line_2500():
    """Preheater and calciner from HFC2500 (it publishes effective
    diameters); kiln and cooler from PF2500."""

    hfc = "HFC2500"
    stages = {
        1: (2, 4.70, 4.32),
        2: (1, 6.60, 6.10),
        3: (1, 6.80, 6.30),
        4: (1, 6.80, 6.30),
        5: (1, 7.00, 6.50),
    }

    cyclones = tuple(
        _vendor_cyclone(s, n, published(shell, hfc), published(eff, hfc))
        for s, (n, shell, eff) in stages.items()
    )

    # HFC's "C<k+1> outlet duct" is the riser from C<k+1> to C<k>.
    ducts = tuple(
        Duct(
            name=f"R{k}",
            from_stage=k + 1,
            to_stage=k,
            shell_D=published(shell, hfc),
            D=published(eff, hfc),
        )
        for k, (shell, eff) in {
            1: (3.45, 3.07),
            2: (3.85, 3.35),
            3: (3.95, 3.45),
            4: (4.10, 3.60),
        }.items()
    )

    calciner_D = published(5.50, hfc)

    return ReferenceLine(
        key="2500",
        capacity_t_d=published(2500.0, hfc),
        strings=1,
        kiln=_vendor_kiln("PF2500", 4.0, 60.0, 4.0, 0.39, 4.10),
        cooler=Cooler(grate_area=published(65.0, "PF2500")),
        cyclones=cyclones,
        ducts=ducts,
        calciner=Vessel(
            shell_D=published(6.00, hfc),
            D=calciner_D,
            length=derive(calciner_D, "calciner_H/D"),
        ),
        gooseneck=Vessel(
            shell_D=published(4.00, hfc),
            D=published(3.50, hfc),
        ),
    )


def _line_5000():
    """Double string: counts are the whole stage, ducts are per string."""

    ref = "PF5000"
    shells = {1: (4, 5.0), 2: (2, 6.9), 3: (2, 6.9), 4: (2, 7.2), 5: (2, 7.2)}

    cyclones = tuple(
        _vendor_cyclone(s, n, published(d, ref), None)
        for s, (n, d) in shells.items()
    )

    calciner_shell = published(7.2, ref)

    return ReferenceLine(
        key="5000",
        capacity_t_d=published(5000.0, ref),
        strings=2,
        kiln=_vendor_kiln(ref, 4.8, 74.0, 4.0, 0.6, 4.0),
        cooler=Cooler(grate_area=published(119.6, ref)),
        cyclones=cyclones,
        ducts=_risers_from_ratio(cyclones),
        calciner=Vessel(
            shell_D=calciner_shell,
            D=derive(calciner_shell, "calciner_eff_over_shell"),
            length=published(30.0, ref),
        ),
        gooseneck=Vessel(),
    )


def _line_fls():
    """The FLS reference tower itself. Diameters are 2 r and barrel
    height is h_t - h_c: arithmetic on printed values, not ratios."""

    ref = "FLS"

    def p(value, what):
        return published(value, f"{ref}: {what}")

    cyclones = tuple(
        CycloneStage(
            stage=s,
            count=1,
            shell_D=p(2.0 * c["r_r"], f"2 r_r[Cy{s}]"),
            D=p(2.0 * c["r_c"], f"2 r_c[Cy{s}]"),
            barrel_h=p(c["h_t"] - c["h_c"], f"h_t - h_c[Cy{s}]"),
            cone_h=p(c["h_c"], f"h_c[Cy{s}]"),
            vortex_len=p(c["h_x"], f"h_x[Cy{s}]"),
            vortex_D=p(2.0 * c["r_x"], f"2 r_x[Cy{s}]"),
            dust_D=p(2.0 * c["r_d"], f"2 r_d[Cy{s}]"),
            inlet_w=model_assumption(c["w_in"], f"{ref}: w_in[Cy{s}]", W_IN_ASSUMPTION),
            inlet_h=model_assumption(
                c["A_in"] / c["w_in"], f"{ref}: A_in / w_in[Cy{s}]", W_IN_ASSUMPTION
            ),
            inlet_area=p(c["A_in"], f"A_in[Cy{s}]"),
        )
        for s, c in FLS_CYCLONES.items()
    )

    ducts = tuple(
        Duct(
            name=f"R{k}",
            from_stage=k + 1,
            to_stage=k,
            shell_D=p(2.0 * r["r_r"], f"2 r_r[R{k}]; {RISER_MAPPING_REF}"),
            D=p(2.0 * r["r_c"], f"2 r_c[R{k}]; {RISER_MAPPING_REF}"),
            length=p(r["h_tot"], f"h_tot[R{k}]; {RISER_MAPPING_REF}"),
            end_cone_len=p(r["h_cl"], f"h_cl[R{k}]; {RISER_MAPPING_REF}"),
            end_D=p(2.0 * r["r_u"], f"2 r_u[R{k}]; {RISER_MAPPING_REF}"),
        )
        for k, r in FLS_RISERS.items()
    )

    return ReferenceLine(
        key="FLS",
        capacity_t_d=None,
        strings=1,
        kiln=Kiln(
            shell_D=p(2.0 * FLS_KILN["r_r"], "2 r_r[kiln]"),
            D=p(2.0 * FLS_KILN["r_c"], "2 r_c[kiln]"),
            length=p(FLS_KILN["L"], "L[kiln]"),
            speed_operating_rpm=p(FLS_KILN["rpm"], "kiln rotation, scenario text"),
        ),
        cooler=Cooler(
            length=p(FLS_COOLER["L"], "L[cooler]"),
            width=p(FLS_COOLER["w"], "w[cooler]"),
        ),
        cyclones=cyclones,
        ducts=ducts,
        calciner=Vessel(
            shell_D=p(2.0 * FLS_CALCINER["r_r"], "2 r_r[calciner]"),
            D=p(2.0 * FLS_CALCINER["r_c"], "2 r_c[calciner]"),
            length=p(FLS_CALCINER["h_tot"], "h_tot[calciner]"),
        ),
        gooseneck=Vessel(),
    )


CATALOG = {
    line.key: line
    for line in (_line_1500(), _line_2500(), _line_5000(), _line_fls())
}


def reference_line(key):
    """One catalogue line, or a KeyError naming the ones that exist."""

    key = str(key)

    if key not in CATALOG:
        raise KeyError(f"no reference line {key!r}; catalogue has {sorted(CATALOG)}")

    return CATALOG[key]
