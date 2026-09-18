"""
Faz 5 -- rotary kiln heat transfer closure.

This module replaces three literal constants per zone (hv_gs, hv_gw,
hv_ws) and one global suppression factor (k_eff = 0.005) with closures
that depend on the state the model already solves for.

WHY THE THREE MOVE TOGETHER
---------------------------
The constants they replace were not three independent errors. In the
burning zone at its own working point (Tg 1551 K, Ts 1489 K, D_e 3.95 m,
fill 8.2%) the measured split was:

                       convection   radiation   total
    physical               48          294        343   W/(m2 K)
    hv_gs + k_eff path    700            3.7      704   W/(m2 K)

Radiation is 86% of the gas->bed path physically and was 1.0% in the
model, while the TOTAL was 2.05x too large. Raising radiation alone
would have given 700 + 294 = 994, i.e. 2.9x physical -- worse than the
starting point. Lowering hv_gs alone would have removed the only path
that was carrying the heat. Neither constant is meaningful on its own,
so they are not separable and this module supplies all of them.

WHAT IS AND IS NOT DEFENSIBLE HERE
----------------------------------
- Convection: Tscheng & Watkinson (1979) rotary kiln correlations.
  Used OUTSIDE their fitted Reynolds range -- see nusselt_gas_bed.
- Wall -> bed contact: physics.wall_bed_contact_coefficient, the
  Li et al. (2005) penetration model already in the repo.
- Surface <-> surface radiation: exact two-surface resistance network
  with an analytic view factor (the bed chord sees only the exposed
  arc, so F = 1). No fitting.
- Gas emissivity: an engineering fit, NOT a digitised chart and NOT
  the Smith/Leckner WSGG coefficient sets. Its anchor values are
  written out in gas_emissivity and pinned by tests. This is the one
  weak link in the module and it is labelled as such.
"""

import numpy as np

from physics.physics import (
    FUEL_COMPOSITION,
    bed_segment_geometry,
    cp_gas,
    k_gas,
    mu_gas,
    sigma,
    wall_bed_contact_coefficient,
)

# Ideal-gas density of the combustion products, taken as air-like.
# The radiating species change the emissivity, not the density, at
# the 1-2% level that matters here.
R_UNIVERSAL = 8.314462618      # J/(mol K)
M_GAS = 0.02896                # kg/mol
P_ATM = 101325.0               # Pa


def gas_density(T, p=P_ATM):
    """Ideal-gas density [kg/m3] of the kiln gas at T [K]."""

    T = np.asarray(T, dtype=float)

    return p * M_GAS / (R_UNIVERSAL * T)


# ======================================================
# CONVECTION -- TSCHENG & WATKINSON (1979)
#
# Two correlations measured in an electrically heated rotary
# drum, both with the gas-side hydraulic diameter D_e as the
# length scale:
#
#   Nu_gb = 0.46 Re_D^0.535 Re_w^0.104 eta^-0.341
#   Nu_gw = 1.54 Re_D^0.575 Re_w^-0.292
#
#   Re_D = rho u_g D_e / mu        axial flow
#   Re_w = rho omega D_e^2 / mu    rotation, omega = 2 pi rpm / 60
#   eta  = bed fill fraction
#
# RANGE OF VALIDITY, STATED BECAUSE WE ARE OUTSIDE IT:
# the correlations were fitted over 1600 < Re_D < 7800 and
# 20 < Re_w < 800. This kiln runs at Re_D ~ 2.5e5 and
# Re_w ~ 1.0e4, i.e. 30x and 13x above the fitted ceiling.
# Every 1D kiln model in the literature extrapolates these
# the same way, because nothing better exists without CFD --
# but it is an extrapolation, not a measurement, and the
# convective branch of this module should be read with that
# in mind. It is also the SMALL branch: radiation dominates
# above ~1200 K, so the extrapolation error is diluted where
# the heat actually moves.
# ======================================================
TW_RE_D_RANGE = (1600.0, 7800.0)
TW_RE_W_RANGE = (20.0, 800.0)


def _reynolds(T, u_g, D_e, rpm):

    T = np.asarray(T, dtype=float)

    rho = gas_density(T)
    mu = mu_gas(T)

    omega = 2.0 * np.pi * rpm / 60.0

    Re_D = rho * np.abs(u_g) * D_e / mu
    Re_w = rho * omega * D_e**2 / mu

    return Re_D, Re_w


def nusselt_gas_bed(T, u_g, D_e, rpm, fill_fraction):
    """Tscheng-Watkinson gas -> bed surface Nusselt number."""

    if not (0.0 < fill_fraction < 1.0):
        raise ValueError(
            f"fill_fraction must be in (0, 1), got {fill_fraction}"
        )

    Re_D, Re_w = _reynolds(T, u_g, D_e, rpm)

    return (
        0.46
        * Re_D**0.535
        * Re_w**0.104
        * fill_fraction**-0.341
    )


def prandtl_gas(T):
    """Prandtl number of the kiln gas."""

    T = np.asarray(T, dtype=float)

    return cp_gas(T) * mu_gas(T) / k_gas(T)


# ======================================================
# GAS -> EXPOSED WALL: DITTUS-BOELTER, NOT TSCHENG-WATKINSON
#
# Tscheng & Watkinson also give a gas -> wall correlation,
#
#   Nu_gw = 1.54 Re_D^0.575 Re_w^-0.292
#
# and it is NOT used here, on purpose. Its rotational exponent
# is NEGATIVE, so extrapolating Re_w 13x past the fitted
# ceiling does not merely stretch the fit, it collapses it:
# at this kiln's Re_w ~ 1.0e4 the factor Re_w^-0.292 is 0.067
# and the correlation returns h_gw ~ 2.9 W/(m2 K), about a
# third of what a plain turbulent duct would give and a
# seventeenth of its own gas -> bed value. A wall cannot
# exchange less than a duct wall in the same flow.
#
# The exposed wall IS a duct wall in fully turbulent flow at
# Re_D ~ 2.5e5, which is squarely INSIDE Dittus-Boelter's
# range (Re > 1e4, 0.6 < Pr < 160, L/D > 10). Using a
# correlation inside its validity beats extrapolating one
# 13x outside it, so:
#
#   Nu_gw = 0.023 Re_D^0.8 Pr^0.4
#
# The 0.4 exponent is the heating form (wall cooler than the
# gas), which is the burning zone's condition.
#
# Gas -> BED keeps Tscheng-Watkinson, because there no duct
# correlation applies: the bed surface is continuously renewed
# by rotation and the correlation's eta and Re_w terms are the
# only published representation of that. It is still an
# extrapolation and is still the minor branch -- radiation
# carries ~79% of the gas -> bed path at this working point.
# ======================================================
def nusselt_gas_wall(T, u_g, D_e, rpm=None):
    """Dittus-Boelter gas -> exposed wall Nusselt number."""

    Re_D, _ = _reynolds(T, u_g, D_e, rpm if rpm is not None else 1.0)

    Pr = prandtl_gas(T)

    return 0.023 * Re_D**0.8 * Pr**0.4


# ======================================================
# GAS EMISSIVITY
#
# THIS IS A FIT, NOT A CORRELATION FROM A TABLE.
#
# The published options are Hottel's charts (graphical),
# Leckner (1972) and the Smith/Shen/Friedman (1982) WSGG
# coefficient sets. None of those coefficient tables could be
# verified from a primary source while this was written, and
# writing WSGG coefficients from memory would put an
# unverifiable table at the centre of the radiation model --
# exactly the failure mode k_eff = 0.005 already was.
#
# So this is an explicit three-parameter fit,
#
#   eps_g = eps_ref * (pL / pL_ref)^n * (T_ref / T)^m
#
# anchored on the following total-emissivity values for a
# CO2 + H2O combustion gas at 1 atm (Hottel chart magnitudes,
# p_w/p_c ~ 1):
#
#     pL [atm m]   1000 K   1500 K   2000 K
#        0.1        0.16     0.11     0.075
#        1.0        0.33     0.25     0.18
#        3.0        0.44     0.34     0.26
#
# The fit reproduces all nine anchors to within 17%, and to
# within 10% over the pL and T range this kiln actually runs
# at. tests/test_kiln_closures.py pins every anchor, so if the
# fit is ever replaced by a real coefficient table the test
# states what the replacement has to reproduce.
#
# The two physical trends it must and does get right:
# emissivity RISES with path length sub-linearly (band
# saturation) and FALLS with temperature (the bands shift out
# of the Planck peak). A constant cannot do either, which is
# the structural reason k_eff had to go.
# ======================================================
EPS_G_REF = 0.25          # at pL_ref, T_ref
EPS_G_PL_REF = 1.0        # atm m
EPS_G_T_REF = 1500.0      # K
EPS_G_PL_EXP = 0.36
EPS_G_T_EXP = 0.78

# Outside these the fit is extrapolating a fit; clipped rather
# than refused because the cold end of the plant legitimately
# sits below the anchor range and the answer there is "almost
# transparent", which the clip gives.
EPS_G_RANGE = (0.02, 0.70)


def gas_emissivity(T, pL):
    """Total emissivity of the radiating gas. T [K], pL [atm m]."""

    T = np.asarray(T, dtype=float)
    pL = np.asarray(pL, dtype=float)

    if np.any(T <= 0.0):
        raise ValueError("gas_emissivity needs T > 0 K")

    if np.any(pL < 0.0):
        raise ValueError("gas_emissivity needs pL >= 0 atm m")

    eps = (
        EPS_G_REF
        * (np.maximum(pL, 1e-12) / EPS_G_PL_REF) ** EPS_G_PL_EXP
        * (EPS_G_T_REF / T) ** EPS_G_T_EXP
    )

    lo, hi = EPS_G_RANGE

    return np.clip(eps, lo, hi)


# ======================================================
# MEAN BEAM LENGTH
#
# L_m = 3.6 V / A for an arbitrary enclosure. For the kiln
# gas space, per unit axial length,
#
#   V = (1 - eta) A_cross
#   A = exposed arc + bed chord = P_gas
#
# and 4 (1-eta) A_cross / P_gas is exactly the D_e that
# bed_segment_geometry already returns, so
#
#   L_m = 0.9 D_e
#
# No new geometry, no new parameter.
# ======================================================
MEAN_BEAM_FACTOR = 0.9


def mean_beam_length(D_e):
    """Mean beam length [m] of the kiln gas space."""

    return MEAN_BEAM_FACTOR * D_e


# ======================================================
# RADIATING PARTIAL PRESSURE
#
# Only CO2 and H2O radiate in this gas; N2, O2 and Ar are
# transparent. SO2 radiates but is < 0.5 vol% here and is
# ignored.
#
# The model does not carry a per-cell species vector, so the
# radiating fraction is assembled from what it does carry:
# the fuel's own combustion products (fuel composition is
# fixed in physics.gas_mass_balance) plus the CO2 the bed
# releases into that cell's gas. Mole fractions are taken
# against an air-like mean molar mass, which is accurate to
# a few percent for a gas that is ~70% N2 by mass.
# ======================================================
M_CO2 = 0.04401       # kg/mol
M_H2O = 0.018015      # kg/mol


# Molar masses of the fuel elements that end up in radiating
# species. M_C and M_H match physics.gas_mass_balance.
M_C = 0.012011        # kg/mol
M_H = 0.001008        # kg/mol


def fuel_combustion_products(m_dot_fuel):
    """
    CO2 and H2O produced by burning m_dot_fuel [kg/s], from the SAME
    fuel composition physics.gas_mass_balance uses to size the air.

    Complete combustion: every fuel carbon becomes CO2, every two
    fuel hydrogens become one H2O. Returns (m_dot_CO2, m_dot_H2O)
    in kg/s. The SO2 is left out -- it radiates, but at < 0.5 vol%
    here it is below the accuracy of the emissivity fit anyway.
    """

    m_dot_fuel = np.asarray(m_dot_fuel, dtype=float)

    if np.any(m_dot_fuel < 0.0):
        raise ValueError("m_dot_fuel must be >= 0 kg/s")

    m_CO2 = m_dot_fuel * FUEL_COMPOSITION["C"] / M_C * M_CO2
    m_H2O = m_dot_fuel * FUEL_COMPOSITION["H"] / (2.0 * M_H) * M_H2O

    return m_CO2, m_H2O


def radiating_partial_pressure(
    m_dot_CO2,
    m_dot_H2O,
    m_dot_gas_total,
):
    """Sum of the CO2 and H2O partial pressures [atm] at 1 atm total."""

    m_dot_CO2 = np.asarray(m_dot_CO2, dtype=float)
    m_dot_H2O = np.asarray(m_dot_H2O, dtype=float)
    m_dot_gas_total = np.asarray(m_dot_gas_total, dtype=float)

    if np.any(m_dot_gas_total <= 0.0):
        raise ValueError("m_dot_gas_total must be > 0 kg/s")

    n_CO2 = m_dot_CO2 / M_CO2
    n_H2O = m_dot_H2O / M_H2O

    # The NON-radiating remainder is what gets the air-like molar
    # mass; the radiating species are moled with their own. Dividing
    # the whole stream by M_GAS instead would understate a CO2-rich
    # gas by the ratio M_GAS / M_CO2 = 0.66, which matters most
    # exactly where it should not: in the calcining zones, where the
    # bed is pouring CO2 into the gas.
    m_inert = np.maximum(
        m_dot_gas_total - m_dot_CO2 - m_dot_H2O,
        0.0,
    )

    n_total = n_CO2 + n_H2O + m_inert / M_GAS

    return np.clip(
        (n_CO2 + n_H2O) / np.maximum(n_total, 1e-30),
        0.0,
        1.0,
    )


# ======================================================
# RADIATION EXCHANGE
#
# Three exchanges, each returned as a LINEARISED coefficient
# h_rad [W/(m2 K)] so that it can go into the matrix rather
# than into the right-hand side:
#
#   h_rad = eps_eff * sigma * (T1 + T2) * (T1^2 + T2^2)
#
# and q = h_rad (T1 - T2) is then algebraically identical to
# eps_eff sigma (T1^4 - T2^4). Frozen at the Picard iterate
# this is exact at the fixed point, keeps A an M-matrix
# (h_rad >= 0 always), and makes the strongest coupling in
# the kiln implicit instead of explicit. That last point is
# not cosmetic: radiation is now ~80x larger than it was, and
# an explicit source of that size oscillates.
#
# The three pairs:
#
# 1. gas <-> bed surface, and 2. gas <-> exposed wall
#    grey gas against a grey surface,
#      eps_eff = eps_s eps_g / (eps_g + eps_s - eps_g eps_s)
#    symmetric, and -> eps_g as eps_s -> 1.
#
# 3. bed surface <-> exposed wall THROUGH the gas
#    This pair is surface-to-surface. Gas emissivity has no
#    meaning in it -- the old code applied the same eps to all
#    three pairs, which is what made the wall pair wrong in
#    kind and not only in size. The right form is the
#    two-surface resistance network
#
#      eps_eff = 1 / (1/eps_b + (A_b/A_w)(1/eps_w - 1))
#
#    with the view factor F_bw = 1 EXACTLY: every ray leaving
#    the bed chord into the gas space terminates on the
#    exposed arc, because the chord and the arc together close
#    the cross-section. No numerical view factor is needed.
#    The exchange is attenuated by the gas in between,
#    tau_g = 1 - eps_g.
#
# The COVERED wall carries no radiation at all: it is in
# contact with the bed, and that path is the Li et al.
# penetration coefficient instead.
# ======================================================


def _h_rad(eps_eff, T1, T2):

    T1 = np.asarray(T1, dtype=float)
    T2 = np.asarray(T2, dtype=float)

    return eps_eff * sigma * (T1 + T2) * (T1**2 + T2**2)


def grey_gas_surface_emissivity(eps_gas, eps_surface):
    """Effective emissivity of a grey gas against a grey surface."""

    return (
        eps_surface * eps_gas
        / (eps_gas + eps_surface - eps_gas * eps_surface)
    )


def two_surface_emissivity(eps_1, eps_2, area_ratio):
    """Two-surface enclosure, F = 1, area_ratio = A_1 / A_2."""

    return 1.0 / (
        1.0 / eps_1
        + area_ratio * (1.0 / eps_2 - 1.0)
    )


# ======================================================
# THE WHOLE CLOSURE, PER CELL
# ======================================================
def kiln_transfer_coefficients(
    Tg,
    Ts,
    Tw,
    D,
    fill_fraction,
    rpm,
    m_dot_gas,
    p_rad,
    eps_bed,
    eps_wall,
    bed_conductivity,
    bed_density,
    bed_cp,
    particle_diameter,
    contact_chi,
):
    """
    Volumetric transfer coefficients K [W/(m3 K)] for one zone.

    Returns a dict carrying both the totals the solver needs and the
    per-mechanism pieces D4 reports, so the diagnostic reads the same
    numbers the matrix was built from rather than recomputing them.
    """

    Tg = np.asarray(Tg, dtype=float)
    Ts = np.asarray(Ts, dtype=float)
    Tw = np.asarray(Tw, dtype=float)

    (
        theta,
        a_gs,
        a_ws,
        a_gw,
        D_e,
    ) = bed_segment_geometry(D, fill_fraction)

    # --------------------------------------------------
    # LOCAL AXIAL GAS VELOCITY
    #
    # Derived here, per cell, from the mass flow and the ideal-gas
    # density at the LOCAL gas temperature, over the free flow area
    # (1 - eta) A_cross.
    #
    # The zones used to hand in a single u_g taken off state, and
    # the transition zone took the BURNING zone's value because
    # that is what state.u_g happened to hold -- a different flow
    # through a different temperature field. Gas density varies by
    # a factor of three down a kiln, so a single velocity is not a
    # small approximation; it is the wrong number in most cells.
    # --------------------------------------------------
    A_cross = np.pi * D**2 / 4.0
    A_gas = (1.0 - fill_fraction) * A_cross

    u_g = np.asarray(m_dot_gas, dtype=float) / (gas_density(Tg) * A_gas)

    # --------------------------------------------------
    # CONVECTION -- evaluated at the gas temperature
    # --------------------------------------------------
    kg = k_gas(Tg)

    h_conv_gs = (
        nusselt_gas_bed(Tg, u_g, D_e, rpm, fill_fraction)
        * kg
        / D_e
    )

    h_conv_gw = (
        nusselt_gas_wall(Tg, u_g, D_e, rpm)
        * kg
        / D_e
    )

    # --------------------------------------------------
    # RADIATION
    # --------------------------------------------------
    L_m = mean_beam_length(D_e)

    eps_g = gas_emissivity(Tg, p_rad * L_m)

    h_rad_gs = _h_rad(
        grey_gas_surface_emissivity(eps_g, eps_bed),
        Tg,
        Ts,
    )

    h_rad_gw = _h_rad(
        grey_gas_surface_emissivity(eps_g, eps_wall),
        Tg,
        Tw,
    )

    # Bed <-> exposed wall, seen through the gas.
    tau_g = 1.0 - eps_g

    h_rad_sw = tau_g * _h_rad(
        two_surface_emissivity(eps_bed, eps_wall, a_gs / a_gw),
        Ts,
        Tw,
    )

    # --------------------------------------------------
    # COVERED WALL -> BED CONTACT
    #
    # Geometry and rotation only, so it is a scalar: it does
    # not move with the cell temperatures. k_gas in the gap is
    # taken at the wall temperature, which does, so the gap
    # resistance is per-cell and the coefficient comes back as
    # an array anyway.
    # --------------------------------------------------
    h_cont = np.array(
        [
            wall_bed_contact_coefficient(
                theta=theta,
                rpm=rpm,
                k_b=bed_conductivity,
                rho_b=bed_density,
                cp_b=bed_cp,
                d_p=particle_diameter,
                k_g=float(k_g_cell),
                chi=contact_chi,
            )
            for k_g_cell in np.atleast_1d(k_gas(Tw))
        ],
        dtype=float,
    )

    # --------------------------------------------------
    # VOLUMETRIC TOTALS
    #
    # The solid <-> wall path carries TWO areas: contact over
    # the covered arc a_ws, radiation across the bed surface
    # a_gs. They are summed into one K because the solver has
    # a single wall node.
    # --------------------------------------------------
    K_gs = (h_conv_gs + h_rad_gs) * a_gs
    K_gw = (h_conv_gw + h_rad_gw) * a_gw
    K_ws = h_cont * a_ws + h_rad_sw * a_gs

    return {
        "theta": theta,
        "a_gs": a_gs,
        "a_ws": a_ws,
        "a_gw": a_gw,
        "D_e": D_e,
        "L_m": L_m,
        "eps_gas": eps_g,
        "h_conv_gs": h_conv_gs,
        "h_rad_gs": h_rad_gs,
        "h_conv_gw": h_conv_gw,
        "h_rad_gw": h_rad_gw,
        "h_cont_ws": h_cont,
        "h_rad_sw": h_rad_sw,
        "K_gs": K_gs,
        "K_gw": K_gw,
        "K_ws": K_ws,
        # Split volumetric conductances, for D4. They sum to the
        # totals above by construction.
        "K_gs_conv": h_conv_gs * a_gs,
        "K_gs_rad": h_rad_gs * a_gs,
        "K_gw_conv": h_conv_gw * a_gw,
        "K_gw_rad": h_rad_gw * a_gw,
        "K_ws_cont": h_cont * a_ws,
        "K_ws_rad": h_rad_sw * a_gs,
        "u_g": u_g,
    }
