"""
Faz 6 -- shell / refractory loss closure.

Replaces the single-layer PLANE wall with a constant external film
coefficient that every zone used up to Faz 5:

    R = t/(k A) + 1/(h_ext A),  h_ext = 10..18 W/(m^2 K), fixed

That form has three defects, all of which show up as a shell
temperature the diagnostics (D2) flagged at 868 K, far above the
~670 K at which refractory anchors fail:

  1. It is a plane wall. A kiln lining is 0.2 m of refractory on a
     2.1 m inner radius; the outer surface is 12% larger than the
     inner one, and the conduction resistance of a cylindrical
     shell is ln(r_out/r_in)/(2 pi k L), not t/(k A).

  2. There is only one layer. A real wall is a series stack --
     coating, refractory, insulation, steel casing -- and the
     steel is what the outside world actually sees.

  3. The outside is convection only. A surface at 550 K radiating
     to a 300 K surrounding loses MORE by radiation than by
     natural convection (h_rad ~ 15, h_conv ~ 6.5 W/(m^2 K)).
     Dropping radiation forces the model to carry the whole flux
     through the convective film, which is exactly why the
     reconstructed shell temperature ran 300 K too hot.

What replaces it here is a closure with no free parameters:

    Q = (T_hotface - T_amb) / R_total

    R_total = sum_j ln(r_{j+1}/r_j)/(2 pi k_j L_cell)
              + 1 / ((h_conv(T_shell) + h_rad(T_shell)) A_outer)

    h_conv  Churchill & Chu natural convection, air properties at
            the film temperature
    h_rad   linearised grey-body exchange with the surroundings

R_total depends on T_shell, which depends on R_total, so the shell
temperature is solved from the surface energy balance

    (T_hotface - T_shell)/R_cond = (h_conv + h_rad) A_outer
                                   (T_shell - T_amb)

for every cell. The zones then use R_total exactly as they used the
old constant one -- frozen at the current Picard iterate, refreshed
each pass, exact at the fixed point. This is the same linearisation
Faz 5 applied to the radiative coefficients inside the enclosure,
and it keeps the wall row's diagonal negative (R_total > 0 always),
so the matrix stays an M-matrix.

The insulation_factor = 0.27 calibration that physics.wall_losses
carried is gone. It existed to divide a plane-wall flux down to
something plausible; with the resistance built from the real layer
stack there is nothing left for it to correct.
"""

from math import isfinite

import numpy as np

from physics.physics import k_gas
from physics.physics import mu_gas
from physics.physics import sigma


# ======================================================
# AMBIENT AIR
#
# The gas OUTSIDE the shell is ambient air, not the process gas,
# so it gets its own cp. physics.cp_gas is a combustion-product
# correlation with a 1050 J/(kg K) floor; dry air sits below that
# floor over the whole film-temperature range that matters here
# (300-700 K), and Pr = mu cp / k would come out ~10% high.
#
# mu_gas and k_gas are reused as they stand: SUTHERLAND_AIR is
# already air, and both track NIST to better than 2% from 250 K
# to 800 K.
#
# cp fit: Cengel, 4-term polynomial for dry air, 250-1000 K.
# ======================================================
P_ATM = 101325.0        # Pa
R_SPECIFIC_AIR = 287.05     # J/(kg K)
GRAVITY = 9.80665       # m/s^2

# Churchill & Chu (1975) state the horizontal-cylinder form for
# Ra <= 1e12. Beyond that the correlation is an extrapolation, so
# the caller is told rather than left to guess.
RA_HORIZONTAL_LIMIT = 1.0e12


def cp_air(T):
    """
    Isobaric specific heat of dry air [J/(kg K)], T in K.

    Horner form and no np.asarray: this is evaluated once per
    pass of the shell Newton solve, which itself sits inside the
    preheater's per-node wall solve, and plain float arithmetic
    is two orders of magnitude cheaper there than routing a 0-d
    array through numpy. Arrays still work -- every operation
    below is elementwise.
    """

    return (
        1034.09
        + T * (
            -0.2849
            + T * (
                7.8173e-4
                + T * (
                    -4.9701e-7
                    + T * 1.0777e-10
                )
            )
        )
    )


def air_film_properties(T_film):
    """
    (k, nu, Pr) of air at the film temperature, 1 atm.

    Density is ideal-gas at P_ATM: the film sits at atmospheric
    pressure by definition, it is the outside of the plant.

    T_film > 0 is not re-checked here: mu_gas and k_gas both run
    it through Sutherland's law, which raises on a non-positive
    temperature, and this is the innermost function of a nested
    solve.
    """

    # mu first: Sutherland's law is what rejects a non-positive
    # temperature, and it has to get there before the ideal-gas
    # density divides by it.
    mu = mu_gas(T_film)
    k = k_gas(T_film)
    cp = cp_air(T_film)

    rho = P_ATM / (R_SPECIFIC_AIR * T_film)

    nu = mu / rho
    Pr = mu * cp / k

    return k, nu, Pr


# ======================================================
# EXTERNAL FILM COEFFICIENTS
# ======================================================
def rayleigh_number(T_surface, T_amb, L_char):
    """
    Rayleigh number of the buoyant film on the outer surface.

    The buoyancy scale is |T_surface - T_amb|: Ra is written for
    a magnitude, and the direction of the heat flow is carried by
    the driving temperature difference where the coefficient is
    USED, not here. beta = 1/T_film is the ideal-gas expansion
    coefficient, which air at atmospheric pressure is.
    """

    # abs(), not np.abs(): correct elementwise on an array and
    # ~20x cheaper on a float.
    delta_T = abs(T_surface - T_amb)

    T_film = 0.5 * (T_surface + T_amb)

    _, nu, Pr = air_film_properties(T_film)

    alpha = nu / Pr

    return (
        GRAVITY
        * delta_T
        * L_char**3
        / (T_film * nu * alpha)
    )


def natural_convection_coefficient(
    T_surface,
    T_amb,
    L_char,
    orientation,
):
    """
    Churchill & Chu natural convection from the outer surface
    [W/(m^2 K)].

    orientation:
      "horizontal"  long horizontal cylinder (rotary kiln shell,
                    cooler casing). L_char is the OUTER DIAMETER.
      "vertical"    vertical plate/cylinder (calciner riser,
                    preheater tower). L_char is the HEIGHT.

    A surface sitting at ambient gets h -> 0 from the Ra^(1/6)
    term, which is the right limit: with no temperature
    difference there is no buoyant plume.
    """

    if L_char <= 0.0:
        raise ValueError(
            f"characteristic length must be > 0 m, got {L_char}"
        )

    T_film = 0.5 * (T_surface + T_amb)

    k, _, Pr = air_film_properties(T_film)

    Ra = rayleigh_number(T_surface, T_amb, L_char)

    if orientation == "horizontal":

        # Churchill & Chu (1975), eq. for horizontal cylinders
        Nu = (
            0.60
            + 0.387
            * Ra ** (1.0 / 6.0)
            / (
                1.0
                + (0.559 / Pr) ** (9.0 / 16.0)
            ) ** (8.0 / 27.0)
        ) ** 2

    elif orientation == "vertical":

        # Churchill & Chu (1975), eq. for vertical plates.
        # Valid over the whole Ra range, unlike the horizontal
        # form, so no limit check is applied to it.
        Nu = (
            0.825
            + 0.387
            * Ra ** (1.0 / 6.0)
            / (
                1.0
                + (0.492 / Pr) ** (9.0 / 16.0)
            ) ** (8.0 / 27.0)
        ) ** 2

    else:

        raise ValueError(
            "orientation must be 'horizontal' or 'vertical', "
            f"got {orientation!r}"
        )

    return Nu * k / L_char


def radiative_coefficient(T_surface, T_amb, emissivity):
    """
    Linearised grey-body coefficient to the surroundings
    [W/(m^2 K)].

    h_rad (T_s - T_amb) == eps sigma (T_s^4 - T_amb^4) identically,
    so this is an exact rewrite of the fourth-power law, not an
    approximation -- the same identity Faz 5 used to pull the
    in-kiln radiation into the matrix.

    The surroundings are taken at T_amb: a kiln radiates to the
    building and the sky, both of which sit at ambient to within
    the accuracy of anything else here.
    """

    return (
        emissivity
        * sigma
        * (T_surface * T_surface + T_amb * T_amb)
        * (T_surface + T_amb)
    )


# ======================================================
# LAYER STACK
# ======================================================
class WallLayer:
    """One material layer of the wall, hot face outward."""

    __slots__ = ("name", "thickness", "conductivity")

    def __init__(self, name, thickness, conductivity):

        if thickness <= 0.0:
            raise ValueError(
                f"wall layer {name!r}: thickness must be > 0 m, "
                f"got {thickness}"
            )

        if conductivity <= 0.0:
            raise ValueError(
                f"wall layer {name!r}: conductivity must be "
                f"> 0 W/(m K), got {conductivity}"
            )

        self.name = str(name)
        self.thickness = float(thickness)
        self.conductivity = float(conductivity)

    def __repr__(self):

        return (
            f"WallLayer({self.name!r}, "
            f"{self.thickness:.4g} m, "
            f"{self.conductivity:.4g} W/(m K))"
        )


class WallStack:
    """
    The series of layers between the process gas and the ambient,
    plus the radiative and geometric properties of the outer face.
    """

    __slots__ = (
        "zone",
        "layers",
        "emissivity",
        "orientation",
    )

    def __init__(self, zone, layers, emissivity, orientation):

        if not layers:
            raise ValueError(
                f"wall_stack.{zone}: needs at least one layer"
            )

        if not (0.0 < emissivity <= 1.0):
            raise ValueError(
                f"wall_stack.{zone}.shell_emissivity must be in "
                f"(0, 1], got {emissivity}"
            )

        if orientation not in ("horizontal", "vertical"):
            raise ValueError(
                f"wall_stack.{zone}.orientation must be "
                f"'horizontal' or 'vertical', got {orientation!r}"
            )

        self.zone = str(zone)
        self.layers = tuple(layers)
        self.emissivity = float(emissivity)
        self.orientation = str(orientation)

    @property
    def thickness(self):
        """Total wall thickness [m], hot face to outer skin."""

        return sum(layer.thickness for layer in self.layers)

    def geometry(self, r_inner, L_cell, L_char):
        """
        Freeze the temperature-INDEPENDENT half of the closure.

        Called once per zone construction: the conduction
        resistance and the outer area never move during a solve,
        only the external film does.
        """

        return ShellGeometry(self, r_inner, L_cell, L_char)


class ShellGeometry:
    """
    A WallStack resolved onto one zone's cell geometry.

    Holds R_cond (cylindrical, per cell), the outer radius and the
    outer area per cell. Immutable for the life of a zone.
    """

    __slots__ = (
        "stack",
        "r_inner",
        "r_outer",
        "L_cell",
        "L_char",
        "R_cond",
        "A_outer_cell",
        "A_inner_cell",
    )

    def __init__(self, stack, r_inner, L_cell, L_char):

        if r_inner <= 0.0:
            raise ValueError(
                f"wall_stack.{stack.zone}: inner radius must be "
                f"> 0 m, got {r_inner}"
            )

        if L_cell <= 0.0:
            raise ValueError(
                f"wall_stack.{stack.zone}: cell length must be "
                f"> 0 m, got {L_cell}"
            )

        # ==================================================
        # CYLINDRICAL SERIES CONDUCTION
        #
        #   R_j = ln(r_{j+1}/r_j) / (2 pi k_j L_cell)
        #
        # not t/(k A). The exact statement is that the
        # cylindrical resistance equals t/(k A L) taken at the
        # LOG-MEAN area, which lies between the inner and outer
        # areas. Every zone used to pass its INNER area, so the
        # plane form OVERSTATED the lining resistance -- for a
        # 0.35 m lining on a 2.10 m bore, by 8% -- and therefore
        # understated the loss. For the thin steel skin the two
        # agree to four digits. The point of doing it properly
        # is that the SAME routine then handles a 0.10 m
        # insulation layer on a 0.3 m duct, where the two forms
        # differ by a factor of 1.5.
        # ==================================================
        R_cond = 0.0
        r = float(r_inner)

        for layer in stack.layers:

            r_next = r + layer.thickness

            R_cond += (
                np.log(r_next / r)
                / (
                    2.0
                    * np.pi
                    * layer.conductivity
                    * L_cell
                )
            )

            r = r_next

        self.stack = stack
        self.r_inner = float(r_inner)
        self.r_outer = r
        self.L_cell = float(L_cell)
        self.L_char = float(L_char)
        self.R_cond = float(R_cond)

        self.A_outer_cell = 2.0 * np.pi * self.r_outer * L_cell
        self.A_inner_cell = 2.0 * np.pi * self.r_inner * L_cell

    def __repr__(self):

        return (
            f"ShellGeometry({self.stack.zone}, "
            f"r {self.r_inner:.3f}->{self.r_outer:.3f} m, "
            f"R_cond {self.R_cond:.4g} K/W)"
        )


# ======================================================
# SHELL TEMPERATURE AND TOTAL RESISTANCE
# ======================================================
def shell_closure(
    T_hotface,
    geometry,
    T_amb,
    T_shell_guess=None,
    max_iter=100,
    tol=1.0e-8,
):
    """
    Solve the outer surface energy balance and return the total
    hot-face-to-ambient resistance.

    Returns (R_total, T_shell, info):

      R_total  [K/W] per cell, defined so that the heat leaving
               one cell is exactly (T_hotface - T_amb)/R_total.
               Same shape as T_hotface.
      T_shell  [K] outer skin temperature, per cell.
      info     dict of the pieces, for diagnostics.

    The balance is

      G_cond (T_hf - T_s) = G_ext(T_s) (T_s - T_amb)

    with G_cond = 1/R_cond and G_ext = (h_conv + h_rad) A_outer.
    Both coefficients rise with T_s, so the right-hand side is
    strictly increasing and the left strictly decreasing: the root
    is unique.

    A FLOAT hot face is solved as a float all the way through.
    That is not a convenience: the preheater solves its wall
    temperature node by node with a root find, and this closure
    sits inside that root find, so it is evaluated some thousands
    of times per plant solve on one temperature at a time.
    Routing a single number through np.where / np.max / np.mean
    costs ~480 us a call against ~8 us for the same arithmetic in
    plain Python. The loop body below is shared between the two
    paths -- only the primitives that differ (elementwise select,
    reduction, mean) are bound per path -- so there is one
    algorithm, not two. Every property function underneath is
    bit-identical on a float and on an array element, so the two
    paths differ only in where the Newton iteration stops, which
    `tol` bounds: measured at 5e-13 relative, against a tol of
    1e-8 K.
    """

    scalar_input = isinstance(T_hotface, float)

    if scalar_input:

        T_hf = T_hotface

        if T_hf <= 0.0:
            raise ValueError("hot-face temperature must be > 0 K")

        def select(cond, a, b):
            return a if cond else b

        def is_outside(t, low, high):
            return (
                not isfinite(t)
                or t <= low
                or t >= high
            )

        def max_abs(x):
            return abs(x)

        def mean(x):
            return float(x)

        def amax(x):
            return float(x)

    else:

        T_hf = np.asarray(T_hotface, dtype=float)

        if np.any(T_hf <= 0.0):
            raise ValueError("hot-face temperature must be > 0 K")

        select = np.where

        def is_outside(t, low, high):
            return (
                ~np.isfinite(t)
                | (t <= low)
                | (t >= high)
            )

        def max_abs(x):
            return float(np.max(np.abs(x)))

        def mean(x):
            return float(np.mean(x))

        def amax(x):
            return float(np.max(x))

    G_cond = 1.0 / geometry.R_cond

    A_out = geometry.A_outer_cell
    emissivity = geometry.stack.emissivity
    orientation = geometry.stack.orientation
    L_char = geometry.L_char

    # ==================================================
    # BRACKET
    #
    # f is strictly decreasing, f(T_amb) = G_cond (T_hf - T_amb)
    # > 0 and f(T_hf) = -G_ext (T_hf - T_amb) < 0, so the root is
    # always inside [T_amb, T_hf]. A degenerate hot face sitting
    # at ambient collapses the bracket onto itself, which is the
    # right answer: no temperature difference, no loss.
    # ==================================================
    T_amb = float(T_amb)

    if scalar_input:

        lo = T_amb
        hi = max(T_hf, T_amb)

    else:

        lo = np.full(T_hf.shape, T_amb)
        hi = np.maximum(T_hf, T_amb)

    # Starting point. Without a guess the shell is placed at the
    # arithmetic mean of hot face and ambient.
    if T_shell_guess is None:

        T_s = 0.5 * (T_hf + T_amb)

    elif scalar_input:

        T_s = float(T_shell_guess)

    else:

        T_s = np.broadcast_to(
            np.asarray(T_shell_guess, dtype=float),
            T_hf.shape,
        ).astype(float)

    T_s = (
        min(max(T_s, lo), hi)
        if scalar_input
        else np.clip(T_s, lo, hi)
    )

    def residual(T_surface):

        h_conv = natural_convection_coefficient(
            T_surface,
            T_amb,
            L_char,
            orientation,
        )

        h_rad = radiative_coefficient(
            T_surface,
            T_amb,
            emissivity,
        )

        f = (
            G_cond * (T_hf - T_surface)
            - (h_conv + h_rad) * A_out * (T_surface - T_amb)
        )

        return f, h_conv, h_rad

    # ==================================================
    # SAFEGUARDED NEWTON
    #
    # Plain successive substitution on the linearised form
    # OSCILLATES here and was measured converging at a factor of
    # 0.82 per pass -- it needed more than 100 passes for 1e-8 K.
    # The reason is that G_ext carries T_s^3: an iterate 400 K
    # too hot overstates the external conductance by a factor of
    # four and throws the next one as far below the root.
    #
    # Newton on f instead, with the bracket above as a
    # safeguard -- any step that leaves it is replaced by a
    # bisection step, so the method cannot escape and cannot
    # stall. The derivative is analytic:
    #
    #   d/dT_s [ eps sigma (T_s^4 - T_amb^4) ] = 4 eps sigma T_s^3
    #   d/dT_s [ h_conv (T_s - T_amb) ]        ~ (4/3) h_conv
    #
    # the second because Churchill & Chu go as Ra^(1/3) in the
    # turbulent branch that every surface here sits in, so the
    # convective flux goes as dT^(4/3). An approximate derivative
    # only costs Newton its quadratic rate; the bracket is what
    # guarantees the answer, and in practice this converges in
    # five or six passes.
    # ==================================================
    converged = False
    iterations = 0
    delta = float("inf")

    for iterations in range(1, max_iter + 1):

        f, h_conv, h_rad = residual(T_s)

        # f > 0: the stack delivers more than the skin can shed,
        # so the root lies above the current iterate.
        above = f > 0.0

        lo = select(above, T_s, lo)
        hi = select(above, hi, T_s)

        df = -(
            G_cond
            + A_out
            * (
                4.0 * emissivity * sigma * T_s * T_s * T_s
                + (4.0 / 3.0) * h_conv
            )
        )

        T_new = T_s - f / df

        T_new = select(
            is_outside(T_new, lo, hi),
            0.5 * (lo + hi),
            T_new,
        )

        delta = max_abs(T_new - T_s)

        T_s = T_new

        if delta < tol:
            converged = True
            break

    if not converged:

        raise RuntimeError(
            f"shell temperature solve for zone "
            f"{geometry.stack.zone!r} did not converge: "
            f"last step {delta:.3e} K after {max_iter} passes"
        )

    # Recomputed at the converged T_s so R_total and T_shell are
    # consistent to machine precision rather than one pass apart.
    h_conv = natural_convection_coefficient(
        T_s,
        T_amb,
        L_char,
        orientation,
    )

    h_rad = radiative_coefficient(T_s, T_amb, emissivity)

    h_ext = h_conv + h_rad

    R_ext = 1.0 / (h_ext * A_out)

    R_total = geometry.R_cond + R_ext

    q_cell = (T_hf - T_amb) / R_total

    info = {
        "R_cond": geometry.R_cond,
        "R_ext_mean": mean(R_ext),
        "R_total_mean": mean(R_total),
        "h_conv_mean": mean(h_conv),
        "h_rad_mean": mean(h_rad),
        "h_ext_mean": mean(h_ext),
        "T_shell_mean": mean(T_s),
        "T_shell_max": amax(T_s),
        "flux_outer_mean": mean(q_cell) / A_out,
        "A_outer_cell": A_out,
        "r_outer": geometry.r_outer,
        "iterations": int(iterations),

        # Reported so the correlation's validity can be READ off
        # a run rather than assumed. Churchill & Chu state the
        # horizontal-cylinder form for Ra <= 1e12; the vertical
        # form carries no upper limit. A kiln shell at 550 K on a
        # 4.9 m outer diameter sits near 5e11, inside the range,
        # but a bigger or hotter shell would not, and this is
        # where that would show.
        "Ra_max": amax(
            rayleigh_number(T_s, T_amb, L_char)
        ),
        "Ra_limit_exceeded": bool(
            orientation == "horizontal"
            and amax(rayleigh_number(T_s, T_amb, L_char))
            > RA_HORIZONTAL_LIMIT
        ),
    }

    return R_total, T_s, info


def loss_conductance(T_shell, geometry, T_amb):
    """
    dQ/dT_hotface of the solved network [W/K], per cell.

    The loss is no longer affine in the hot-face temperature, so
    anything running a Newton solve against it needs the real
    slope rather than the secant through the origin that the old
    constant-resistance model allowed.

    The network is two resistances in series, so the DIFFERENTIAL
    conductance is

        dQ/dT_hf = 1 / (R_cond + 1/(dQ_ext/dT_shell))

    with the external leg differentiated the same way the Newton
    step inside shell_closure does it: exactly for radiation,
    and as (4/3) h_conv for the turbulent natural-convection
    branch, where the flux goes as dT^(4/3).
    """

    h_conv = natural_convection_coefficient(
        T_shell,
        T_amb,
        geometry.L_char,
        geometry.stack.orientation,
    )

    G_ext_diff = geometry.A_outer_cell * (
        4.0
        * geometry.stack.emissivity
        * sigma
        * T_shell
        * T_shell
        * T_shell
        + (4.0 / 3.0) * h_conv
    )

    return 1.0 / (geometry.R_cond + 1.0 / G_ext_diff)


def shell_temperature_from_resistance(
    T_hotface,
    R_total,
    geometry,
    T_amb,
):
    """
    Outer skin temperature implied by a resistance already solved.

    Diagnostics used to rebuild the shell temperature from a
    plane-wall ratio of its own (R_conv/R_total with a constant
    h_ext), which drifted from whatever the zones were actually
    solving. This is the one-line inverse of the same network the
    zones use: whatever flux R_total carries is dropped across the
    conduction stack, and what is left is the skin.
    """

    T_hotface = np.asarray(T_hotface, dtype=float)

    q = (T_hotface - T_amb) / R_total

    return T_hotface - q * geometry.R_cond


# ======================================================
# CONFIG
# ======================================================
#
# Layer stacks per zone. Every number is a MATERIAL or GEOMETRIC
# property of the wall, not a knob: thicknesses are standard
# linings, conductivities are hot-face values for the named
# material, emissivities are for the named surface finish.
#
# The rotary zones (burning, transition) carry a CLINKER COATING
# as their first layer. That layer is real and load-bearing on the
# result: a bare basic brick gives an effective lining resistance
# near 0.10 m^2 K/W and a shell flux around 9 kW/m^2, while
# measured kiln shells run 4-6 kW/m^2. The difference is the
# 0.05-0.20 m of sintered clinker that a burning zone always
# carries -- it is what protects the brick, and a kiln running
# without it is losing its lining. 0.10 m at 1.0 W/(m K) is the
# middle of the reported range; it is the single most uncertain
# entry in this table and is stated here rather than buried.
#
# The non-rotating zones are LAGGED: castable refractory, mineral
# wool or ceramic fibre, then a thin steel casing. That is why
# their skin runs near 370-400 K while a kiln shell runs near
# 550 K, and why they lose about a tenth of the flux per unit
# area.
#
# NOTE (Faz 3 / Faz 6 items 2-4): the calciner, preheater and
# cooler still carry rotary-cylinder GEOMETRY (D = 4.2 m,
# L = 25 m). Their stacks below are correct for what those
# vessels are made of, but the area they are applied over is the
# placeholder geometry. When those zones get their real geometry
# the r_inner and L_char passed into geometry() move with them;
# nothing in this table has to change.
# ======================================================
DEFAULT_WALL_STACKS = {

    "burning": {
        "orientation": "horizontal",
        "shell_emissivity": 0.80,       # oxidised carbon steel
        "layers": [
            ("clinker coating", 0.100, 1.00),
            ("magnesia-spinel brick", 0.225, 2.80),
            ("steel shell", 0.025, 45.0),
        ],
    },

    "transition": {
        "orientation": "horizontal",
        "shell_emissivity": 0.80,
        "layers": [
            ("clinker coating", 0.050, 1.00),
            ("alumina brick", 0.200, 2.00),
            ("steel shell", 0.025, 45.0),
        ],
    },

    "calciner": {
        "orientation": "vertical",
        "shell_emissivity": 0.85,       # painted casing
        "layers": [
            ("castable refractory", 0.150, 1.20),
            ("ceramic fibre", 0.100, 0.12),
            ("steel casing", 0.012, 45.0),
        ],
    },

    "preheater": {
        "orientation": "vertical",
        "shell_emissivity": 0.85,
        "layers": [
            ("castable refractory", 0.100, 1.10),
            ("mineral wool", 0.100, 0.12),
            ("steel casing", 0.010, 45.0),
        ],
    },

    "cooler": {
        "orientation": "horizontal",
        "shell_emissivity": 0.85,
        "layers": [
            ("castable refractory", 0.150, 1.30),
            ("mineral wool", 0.075, 0.14),
            ("steel casing", 0.012, 45.0),
        ],
    },
}


def wall_stack(cfg, zone):
    """
    Build the WallStack for one zone from a loaded config dict.

    configs/twin_cfg.yaml may override any zone under wall_stack:;
    anything it leaves out falls back to DEFAULT_WALL_STACKS, so a
    config that predates Faz 6 still builds.
    """

    if zone not in DEFAULT_WALL_STACKS:
        raise KeyError(
            f"no default wall stack for zone {zone!r}; known zones "
            f"are {sorted(DEFAULT_WALL_STACKS)}"
        )

    section = (cfg or {}).get("wall_stack", {}) or {}

    spec = dict(DEFAULT_WALL_STACKS[zone])
    spec.update(section.get(zone, {}) or {})

    layers = [
        WallLayer(name, thickness, conductivity)
        for name, thickness, conductivity in spec["layers"]
    ]

    return WallStack(
        zone=zone,
        layers=layers,
        emissivity=spec["shell_emissivity"],
        orientation=spec["orientation"],
    )
