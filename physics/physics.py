import numpy as np

ZONE_ENERGY_WEIGHTS = {
    "burning": {
        "axial": [
            0.05,
            0.10,
            0.20,
            0.35,
            0.30,
        ],
    },

    "transition": {
        "axial": [
            0.10,
            0.15,
            0.20,
            0.25,
            0.30,
        ],
    },

    "calciner": {
        "axial": [
            0.10,
            0.15,
            0.20,
            0.25,
            0.30,
        ],
    },

    "preheater": {
        "axial": [
            0.10,
            0.15,
            0.20,
            0.25,
            0.30,
        ],
    },

    "cooler": {
        "axial": [
            0.30,
            0.25,
            0.20,
            0.15,
            0.10,
        ],
    },
}


# ======================================================
# AXIAL PROFILE RESAMPLING
#
# Resample a calibrated axial profile (given at its own
# cell-center positions) onto N new cell centers via linear
# interpolation, then renormalize so the weights still sum
# to 1 (total energy is conserved regardless of N). This
# lets a profile calibrated at one mesh resolution be reused
# at a finer one without inventing new physics.
# ======================================================
def resample_axial_weights(weights, N):

    weights = np.asarray(weights, dtype=float)
    n_ref = len(weights)

    x_ref = (np.arange(n_ref) + 0.5) / n_ref
    x_new = (np.arange(N) + 0.5) / N

    resampled = np.interp(x_new, x_ref, weights)

    return resampled / np.sum(resampled)


# ======================================================
# GAS THERMODYNAMIC PROPERTIES
# ======================================================

def cp_gas(T):
    """
    Temperature-dependent representative combustion-gas Cp.

    SI units:
        T  : K
        Cp : J/(kg K)

    Temporary thermodynamic closure.
    Later this can be replaced by species-based Cp.
    """

    # Scalar fast path. This is called ~880k times per
    # steady-state solve, almost always on one temperature at a
    # time (Tg_iter[i] inside the per-cell assembly loops), and
    # np.asarray + np.maximum on a 0-d array cost ~17 us against
    # ~0.2 us for the same arithmetic in plain Python.
    #
    # np.float64 subclasses float, so array elements take this
    # path too. T*T is what numpy's ** 2 already lowers to, so
    # the result is bit-identical to the array path -- verified
    # over 30000 temperatures in [250, 3500] K.
    if isinstance(T, float):

        Cp = (
            1050.0
            + 0.18 * T
            - 3.0e-5 * (T * T)
        )

        return Cp if Cp > 1050.0 else 1050.0

    T = np.asarray(T, dtype=float)

    Cp = (
        1050.0
        + 0.18 * T
        - 3.0e-5 * T**2
    )

    return np.maximum(Cp, 1050.0)


def h_gas(T, T_ref):
    """
    Gas sensible enthalpy relative to T_ref.

    SI units:
        T     : K
        T_ref : K
        h     : J/kg
    """

    # Scalar fast path -- see cp_gas. The cubic term keeps ** 3
    # rather than T*T*T: repeated multiplication is NOT
    # bit-identical to the array path here (~1 ulp), whereas
    # T*T for the square and ** 3 for the cube reproduce it
    # exactly -- verified over 30000 temperatures in
    # [250, 3500] K.
    if isinstance(T, float):

        return (
            1050.0 * (T - T_ref)
            + 0.09 * (T * T - T_ref**2)
            - 1.0e-5 * (T**3 - T_ref**3)
        )

    T = np.asarray(T, dtype=float)

    h = (
        1050.0 * (T - T_ref)
        + 0.09 * (T**2 - T_ref**2)
        - 1.0e-5 * (T**3 - T_ref**3)
    )

    return h


def T_gas_from_h(h_target, T_ref, T_min, T_max):
    """
    Invert h_gas: solve h_gas(T, T_ref) = h_target for T,
    restricted to [T_min, T_max].

    SI units:
        h_target : J/kg
        T_*      : K

    h_gas is a cubic whose derivative is exactly cp_gas
    (1050 + 0.18*T - 3e-5*T^2, strictly positive over any
    physical range here), so h_gas is strictly increasing, the
    root is unique, and Newton on cp_gas converges
    quadratically -- typically 4 evaluations.

    The bracket is carried along and a Newton step that would
    leave it degrades to a bisection step, so convergence is
    never worse than the plain bisection this replaces.

    Out-of-range targets return the corresponding bound, which
    is what a bisection on [T_min, T_max] collapses to.

    This replaces three separate 100-step bisections (burning,
    transition and calciner gas inlets). Those spent half their
    work below double precision: halving [200, 4000] K 100
    times passes the resolution of a double at ~52 steps.
    """

    T_low = float(T_min)
    T_high = float(T_max)

    if h_target <= h_gas(T_low, T_ref):
        return T_low

    if h_target >= h_gas(T_high, T_ref):
        return T_high

    T = 0.5 * (T_low + T_high)

    for _ in range(60):

        if T_high - T_low <= 1.0e-12 * T_high:
            break

        residual = h_gas(T, T_ref) - h_target

        if residual < 0.0:
            T_low = T
        elif residual > 0.0:
            T_high = T
        else:
            return T

        cp = cp_gas(T)

        T_newton = (
            T - residual / cp
            if cp > 0.0
            else 0.5 * (T_low + T_high)
        )

        if not (T_low < T_newton < T_high):
            T_newton = 0.5 * (T_low + T_high)

        if T_newton == T:
            break

        T = T_newton

    return T


# ======================================================
# GAS TRANSPORT PROPERTIES (SUTHERLAND'S LAW)
#
#   mu(T) = mu_0 (T/T_0)^1.5 (T_0 + S_mu) / (T + S_mu)
#   k(T)  = k_0  (T/T_0)^1.5 (T_0 + S_k)  / (T + S_k)
#
# Air constants (White, Viscous Fluid Flow; as tabulated in
# the COMSOL CFD Module guide): mu_0 = 1.716e-5 Pa s,
# k_0 = 0.0241 W/(m K), T_0 = 273 K, S_mu = 111 K,
# S_k = 194 K.
#
# Against tabulated air data (Incropera, Table A.4) the
# deviation is within 2 % for 300-1000 K but grows with T:
# at 1500 K mu is ~5 % and k ~14 % low. Burning-zone gas
# runs well above 1000 K, so this closure under-predicts k_g
# there.
#
# The kiln gas is represented by air, the same representative-
# gas closure cp_gas() uses. Where high-T accuracy or CO2/H2O
# fractions matter, a species-based closure should replace it.
# ======================================================
SUTHERLAND_AIR = {
    "mu_0": 1.716e-5,   # Pa s
    "k_0": 0.0241,      # W/(m K)
    "T_0": 273.0,       # K
    "S_mu": 111.0,      # K
    "S_k": 194.0,       # K
}


def _sutherland(T, ref_value, T_0, S):

    T = np.asarray(T, dtype=float)

    if np.any(T <= 0.0):
        raise ValueError("Sutherland's law needs T > 0 K")

    value = ref_value * (T / T_0) ** 1.5 * (T_0 + S) / (T + S)

    return float(value) if value.ndim == 0 else value


def mu_gas(T):
    """Dynamic viscosity of the representative gas [Pa s], T in K."""

    c = SUTHERLAND_AIR

    return _sutherland(T, c["mu_0"], c["T_0"], c["S_mu"])


def k_gas(T):
    """Thermal conductivity of the representative gas [W/(m K)], T in K."""

    c = SUTHERLAND_AIR

    return _sutherland(T, c["k_0"], c["T_0"], c["S_k"])


# ======================================================
# SECOND-ORDER ADVECTION CORRECTION (van Leer TVD)
#
# Every zone discretises axial transport in conservative
# flux form and takes each face value as the UPSTREAM CELL
# CENTRE:
#
#   m_dot * (phi_face_out - phi_face_in) = sources
#   phi_face := phi[upstream cell]
#
# That is first-order upwind. Its truncation error is
# O(dz) and, worse, that error acts as a numerical
# DIFFUSION which smears exactly the steep axial gradients
# the cold end of the kiln is made of. The N=10/20/40 grid
# study measured the resulting observed order at ~0.83.
#
# This helper upgrades the face value to a limited linear
# reconstruction (MUSCL, kappa = -1):
#
#   phi_face = phi_U + 0.5 * psi(r) * (phi_U - phi_UU)
#   r        = (phi_D - phi_U) / (phi_U - phi_UU)
#
# with U the upstream cell, UU the cell upstream of U and D
# the downstream cell. psi is the van Leer limiter, written
# here in its equivalent harmonic form
#
#   0.5 * psi(r) * b = a * b / (a + b)   for a * b > 0
#                    = 0                 otherwise
#
# (a = phi_D - phi_U, b = phi_U - phi_UU). That form needs
# no division guard: a and b share a sign wherever the
# branch is taken, so a + b cannot be zero there. van Leer
# is TVD, so the reconstruction creates no new extremum --
# it cannot introduce an unphysical temperature over- or
# undershoot -- and wherever the profile is not smooth
# (a * b <= 0) it degrades continuously back to the current
# first-order scheme.
#
# APPLICATION. The correction is returned PER CELL and is
# meant to be applied by DEFERRED CORRECTION: the caller
# leaves its matrix exactly as it is -- still the
# first-order upwind operator, still diagonally dominant --
# and subtracts (flux capacity) * correction[i] from b[i].
# The anti-diffusive part is therefore frozen at the Picard
# iterate, and at the fixed point, where the iterate equals
# the solution, the converged answer satisfies the full
# second-order equation. Keeping the implicit operator
# first-order is deliberate: moving the reconstruction into
# A introduces a POSITIVE off-diagonal and destroys the
# M-matrix property the existing Picard loop relies on.
#
# CONSERVATION. An interior face contributes +D to one cell
# and -D to its neighbour, so the corrections telescope and
# the scheme stays exactly conservative cell to cell. The
# inlet face carries no correction (its value is the known
# handoff stream, not a reconstruction), so
#
#   sum(corrections) == outlet face correction
#
# which is precisely the amount by which the zone's outlet
# flux changes. The caller MUST therefore feed the same
# reconstructed outlet value into its handoff, or that
# difference leaks out of the energy balance.
# outlet_face_value() below returns it, and is defined to
# agree with the last entry of this function bit for bit.
#
# ORIENTATION. `reverse=False` means the stream enters at
# index 0 and leaves at index N-1 (the solid phase in every
# zone). `reverse=True` means it enters at N-1 and leaves
# at 0 (the gas phase in burning, transition and cooler).
#
# The quantity reconstructed must be the one the flux is
# linear in: gas enthalpy h for the gas phase (h is cubic
# in T, so reconstructing T would not be conservative), and
# temperature for the solid phase, whose flux
# m_dot_s * Cp_s * (Ts - T_ref) is affine in Ts.
# ======================================================
def second_order_upwind_correction(phi, phi_in, reverse=False):

    phi = np.asarray(phi, dtype=float)

    N = phi.size

    # Two cells are the minimum needed to form an upstream
    # gradient; below that the scheme stays first-order.
    if N < 2:
        return np.zeros(N)

    if reverse:
        phi = phi[::-1]

    # --------------------------------------------------
    # INTERIOR FACES
    #
    # Face f (1 .. N-1) separates cell f-1 (upstream) from
    # cell f (downstream).
    # --------------------------------------------------

    a = phi[1:] - phi[:-1]

    b = np.empty(N - 1)

    # The first interior face has no cell upstream of its
    # upstream cell -- the inlet FACE sits there instead,
    # half a cell further up. Its one-sided gradient is
    # therefore (phi[0] - phi_in) / (dz/2), i.e. twice the
    # per-cell difference, which keeps the reconstruction
    # second-order right at the inlet rather than dropping
    # to first order on the face where the incoming stream
    # is still steepest.
    b[0] = 2.0 * (phi[0] - phi_in)

    b[1:] = phi[1:-1] - phi[:-2]

    ab = a * b

    D = np.zeros(N + 1)

    np.divide(
        ab,
        a + b,
        out=D[1:N],
        where=ab > 0.0,
    )

    # --------------------------------------------------
    # OUTLET FACE
    #
    # Nothing lies downstream, so there is no ratio to
    # limit against; the standard second-order outflow
    # condition is a plain linear extrapolation of the last
    # cell-centre gradient onto the boundary face, half a
    # cell away. This is the term that removes the
    # half-cell bias in the zone handoff enthalpies.
    # --------------------------------------------------

    D[N] = 0.5 * (phi[N - 1] - phi[N - 2])

    # Cell i gains its outflow face correction and loses
    # its inflow face correction.
    correction = D[1:] - D[:-1]

    if reverse:
        correction = correction[::-1]

    return correction


# ======================================================
# RECONSTRUCTED OUTLET FACE VALUE
#
# The boundary value matching second_order_upwind_correction
# above. Zones hand off to the next unit with the value at
# their outlet FACE, but the solution array only holds cell
# CENTRES, and the last centre sits half a cell short of
# that face -- a systematic O(dz) bias in exactly the
# handoff quantities the grid study found worst converged.
#
# Returns the linear extrapolation used as the outlet flux
# by the correction above, so the zone's internal energy
# balance and its handoff stay consistent to the last bit.
#
# Since the argument may be any quantity affine in the
# reconstructed one (gas ENTHALPY per unit mass or the
# enthalpy FLOW m_dot * h, solid TEMPERATURE or the flow
# m_dot_s * Cp_s * (Ts - T_ref)), the extrapolation may be
# taken directly on whichever of those the caller holds.
# ======================================================
def outlet_face_value(phi, reverse=False):

    phi = np.asarray(phi, dtype=float)

    if phi.size < 2:
        return float(phi[-1]) if phi.size else 0.0

    if reverse:
        return float(phi[0] + 0.5 * (phi[0] - phi[1]))

    return float(phi[-1] + 0.5 * (phi[-1] - phi[-2]))


def gas_mass_balance(
    fuel_rate_total,
    O2,
    eps=1e-12,
):
    # ======================================================
    # REPRESENTATIVE PETCOKE COMPOSITION
    # [mass fraction]
    # ======================================================
    fuel_composition = {
        "C": 0.88,
        "H": 0.04,
        "O": 0.02,
        "S": 0.06,
    }

    # ======================================================
    # MOLAR MASSES [kg/mol]
    # ======================================================
    M_C = 0.012011
    M_H = 0.001008
    M_O = 0.015999
    M_S = 0.03206
    M_O2 = 0.031998

    # Dry air oxygen mass fraction
    Y_O2_air = 0.232

    # ======================================================
    # FUEL MASS FRACTIONS
    # ======================================================
    w_C = fuel_composition["C"]
    w_H = fuel_composition["H"]
    w_O = fuel_composition["O"]
    w_S = fuel_composition["S"]

    # ======================================================
    # STOICHIOMETRIC O2 [mol/kg fuel]
    # ======================================================
    n_O2_st = (
        w_C / M_C
        + 0.25 * w_H / M_H
        + w_S / M_S
        - 0.5 * w_O / M_O
    )

    # ======================================================
    # STOICHIOMETRIC O2 [kg/kg fuel]
    # ======================================================
    m_O2_st = n_O2_st * M_O2

    # ======================================================
    # STOICHIOMETRIC AIR [kg/kg fuel]
    # ======================================================
    m_air_st = m_O2_st / Y_O2_air

    # ======================================================
    # DRY FLUE-GAS O2 TARGET
    # O2 = vol% dry O2
    # ======================================================
    O2_dry_target = O2 / 100.0

    # ======================================================
    # PRODUCT MOLES [mol/kg fuel]
    # ======================================================
    n_CO2 = w_C / M_C
    n_SO2 = w_S / M_S

    # ======================================================
    # DRY FLUE-GAS O2 FRACTION
    # ======================================================
    def dry_O2_fraction(lam):

        n_O2_excess = (lam - 1.0) * n_O2_st

        n_N2 = lam * n_O2_st * (79.0 / 21.0)

        n_dry = (
            n_CO2
            + n_SO2
            + n_O2_excess
            + n_N2
        )

        return n_O2_excess / (n_dry + eps)

    # ======================================================
    # SOLVE λ FROM DRY FLUE-GAS O2
    # ======================================================
    lam_low = 1.0
    lam_high = 3.0

    for _ in range(60):

        lam_mid = 0.5 * (lam_low + lam_high)

        if dry_O2_fraction(lam_mid) < O2_dry_target:
            lam_low = lam_mid
        else:
            lam_high = lam_mid

    lam = 0.5 * (lam_low + lam_high)

    # ======================================================
    # ACTUAL AIR FLOW
    # ======================================================
    m_air_per_kg_fuel = lam * m_air_st

    m_dot_air = (
        fuel_rate_total
        * m_air_per_kg_fuel
    )

    # ======================================================
    # TOTAL GAS MASS FLOW
    # ======================================================
    m_dot_g = (
        m_dot_air
        + fuel_rate_total
    )

    return m_dot_g


def residence_time(L, D, slope_deg, fill_fraction, rpm, eps):

    theta = np.deg2rad(slope_deg)

    tau = (
        1.77
        * L
        / (
            D
            * rpm
            * np.tan(theta)
            * (fill_fraction + eps)
        )
    )

    return tau


def solid_axial_velocity(L, D, slope_deg, fill_fraction, rpm, eps):

    tau = residence_time(
        L,
        D,
        slope_deg,
        fill_fraction,
        rpm,
        eps,
    )

    return L / (tau + eps)


def gas_axial_velocity(m_dot_g, rho_g, A_cross, eps):

    return m_dot_g / (rho_g * A_cross + eps)

# ======================================================
# COMBUSTION
# ======================================================
def combustion_efficiency(O2, O2_opt, O2_sigma2):

    return np.exp(
        -((O2 - O2_opt) ** 2) / O2_sigma2
    )
    
def fuel_heat_release(
    fuel_rate_total,     # kg/s
    O2,
    O2_opt,
    O2_sigma2,
    LHV,
    inputs,
    eps,
):

    # ======================================================
    # PETCOKE-ONLY FUEL MODEL
    # ======================================================

    Q_petcoke = (
        fuel_rate_total
        * LHV["petcoke"]
    )

    # ======================================================
    # COMBUSTION EFFICIENCY
    # ======================================================

    eta = combustion_efficiency(
        O2,
        O2_opt,
        O2_sigma2,
    )

    # ======================================================
    # TOTAL HEAT RELEASE
    # ======================================================

    Q_burning = (
        eta
        * Q_petcoke
    )

    return Q_petcoke, Q_burning


def combustion_axial_distribution(
    Q_total,
    weights,
):
    """
    Toplam yanma ısısının eksenel ağırlıklara göre dağıtılması.

    Q_total : toplam yanma ısısı [W]
    weights : hücre ağırlıkları [-]

    Returns
    -------
    q_cell : hücre başına yanma ısısı [W]
    """

    weights = np.asarray(weights, dtype=float)

    if len(weights) == 0:
        raise ValueError("Combustion weights cannot be empty.")

    if np.any(weights < 0.0):
        raise ValueError("Combustion weights must be non-negative.")

    weight_sum = np.sum(weights)

    if weight_sum <= 0.0:
        raise ValueError("Combustion weights must have a positive sum.")

    weights = weights / weight_sum

    q_cell = Q_total * weights

    return q_cell

# ======================================================
# HEAT TRANSFER
# ======================================================

"""
k_eff is an effective radiation scaling factor representing
unresolved radiative effects, including view factors,
participating media, gas absorption, flame radiation,
and other complex heat transfer mechanisms.
"""

ZONE_RAD_CONFIG = {

    "burning": {
        "eps":0.92,
        "k_eff":0.005,
    },

    "transition":{
        "eps":0.88,
        "k_eff":0.005,
    },

    "calciner":{
        "eps":0.82,
        "k_eff":0.005,
    },

    "preheater":{
        "eps":0.70,
        "k_eff":0.005,
    },

    "cooler":{
        "eps":0.55,
        "k_eff":0.005,
    },
}

ZONE_HT_CONFIG = {
    "burning": {
        "hv_gs": 700.0,
        "hv_gw": 180.0,
        "hv_ws": 220.0,
    },
    "transition": {
        "hv_gs": 450.0,
        "hv_gw": 150.0,
        "hv_ws": 180.0,
    },
    "calciner": {
        "hv_gs": 350.0,
        "hv_gw": 120.0,
        "hv_ws": 150.0,
    },
    "preheater": {
        "hv_gs": 220.0,
        "hv_gw": 90.0,
        "hv_ws": 110.0,
    },
    "cooler": {
        "hv_gs": 180.0,
        "hv_gw": 70.0,
        "hv_ws": 90.0,
    },
}


sigma = 5.670374419e-8


# ======================================================
# PER-ZONE RADIATION COEFFICIENT
#
# k_eff * eps * sigma is fixed per zone, but radiation() was
# re-reading ZONE_RAD_CONFIG and redoing the product on every
# one of its ~516k calls per steady-state solve. Precomputed
# here with the same left-to-right grouping the inline
# expression used, so the product is bit-identical.
# ======================================================
ZONE_RAD_COEFF = {
    _zone: _cfg["k_eff"] * _cfg["eps"] * sigma
    for _zone, _cfg in ZONE_RAD_CONFIG.items()
}


def radiation(T1, T2, zone, area=1.0):
    """ Stefan–Boltzmann radiation model with zone-dependent tuning."""
    

    q_rad = ZONE_RAD_COEFF[zone] * area * (T1**4 - T2**4)


    return q_rad


def heat_transfer(Tg, Ts, Tw, hv_gs, hv_gw, hv_ws, a_gs, a_gw, a_ws, zone=None):

    # ======================================================
    # CONVECTION
    # ======================================================

    q_gs_conv = hv_gs * a_gs * (Tg - Ts)
    q_gw_conv = hv_gw * a_gw * (Tg - Tw)
    q_ws_conv = hv_ws * a_ws * (Ts - Tw)

    # ======================================================
    # RADIATION (STEFAN–BOLTZMANN)
    # ======================================================
    q_gs_rad = radiation(Tg, Ts, zone, area=a_gs)
    q_gw_rad = radiation(Tg, Tw, zone, area=a_gw)
    q_ws_rad = radiation(Ts, Tw, zone, area=a_ws)

    # ======================================================
    # TOTAL HEAT TRANSFER
    # ======================================================
    q_gs = q_gs_conv + q_gs_rad
    q_gw = q_gw_conv + q_gw_rad
    q_ws = q_ws_conv + q_ws_rad

    

    return q_gs, q_gw, q_ws

    
def wall_losses(
    Tw,
    h_ext,
    A_wall_cell,
    V_cell,
    T_amb,
    A_wall_total,
    N,
    refractory_thickness,
    refractory_conductivity,
    eps,
    insulation_factor=0.27,   # default calibration
    debug=True,
):
    """
    Wall heat loss through the refractory/convection network.

    debug=True (default) also returns the wall_debug dict, so
    every existing caller is unaffected. debug=False returns
    None in its place and skips building it: the dict costs two
    np.mean, one np.max and ~14 float() calls per invocation,
    which is pure overhead on the iterative wall-temperature
    solves that call this millions of times per steady-state
    run and discard the dict. The returned q_loss and wall_loss
    are identical either way.
    """

    # ======================================================
    # THERMAL RESISTANCE NETWORK
    # ======================================================
    R_ref, R_conv, R_total = wall_thermal_resistance(
        refractory_thickness=refractory_thickness,
        refractory_conductivity=refractory_conductivity,
        h_ext=h_ext,
        A_wall_cell=A_wall_cell,
    )

    # ======================================================
    # HEAT LOSS (cell-wise)
    # ======================================================
    wall_loss_cells = (Tw - T_amb) / (R_total + eps)

    # ======================================================
    # TOTAL HEAT LOSS
    # ======================================================
    wall_loss_raw = np.sum(wall_loss_cells)

    # ======================================================
    # APPLY INSULATION FACTOR
    # ======================================================
    # insulation_factor is a scalar calibration constant -- the
    # debug dict below already assumed that via float(...) -- so
    # the clamp is done in plain Python. np.clip on a scalar
    # routes through the array-function machinery and dominated
    # this function's cost in the iterative wall solves.
    insulation_factor = min(
        max(float(insulation_factor), 0.1),
        1.0,
    )

    wall_loss = insulation_factor * wall_loss_raw

    # ======================================================
    # VOLUMETRIC LOSS
    # ======================================================
    q_loss = insulation_factor * wall_loss_cells / (V_cell + eps)

    # ======================================================
    # DEBUG
    # ======================================================
    if not debug:
        return q_loss, wall_loss, None

    wall_debug = {
        "R_ref": float(R_ref),
        "R_conv": float(R_conv),
        "R_total": float(R_total),

        "insulation_factor": float(insulation_factor),

        "q_loss_mean": float(np.mean(q_loss)),
        "q_loss_max": float(np.max(q_loss)),

        "wall_loss_mean": float(np.mean(wall_loss_cells)),
        "wall_loss_total_raw": float(wall_loss_raw),
        "wall_loss_total": float(wall_loss),

        "A_wall": float(A_wall_total),
        "A_wall_cell": float(A_wall_cell),
        "V_cell": float(V_cell),
        "N": int(N),
    }

    return q_loss, wall_loss, wall_debug

# ======================================================
# GEOMETRY
# ======================================================
def kiln_geometry(D, L, N):

    # Cross-sectional area (m²)
    A_cross = np.pi * D**2 / 4.0

    # Total kiln volume (m³)
    V_total = A_cross * L

    # Computational cell volume (m³)
    V_cell = V_total / N

    return (
        A_cross,
        V_total,
        V_cell,
    )
# ======================================================
# WALL GEOMETRY
# ======================================================
def wall_geometry(
    D,
    L,
    N,
    V_cell,
    refractory_thickness=0.05,
):

    # Kiln inner perimeter (m)
    wall_perimeter = np.pi * D

    # Total inner wall area (m²)
    A_wall_total = wall_perimeter * L

    # Wall area per computational cell (m²)
    A_wall_cell = A_wall_total / N

    # Gas-wall interfacial area density (m²/m³)
    a_gw = A_wall_cell / V_cell

    # Refractory wall volume (m³)
    V_wall = A_wall_total * refractory_thickness

    return (
        wall_perimeter,
        A_wall_total,
        A_wall_cell,
        a_gw,
        V_wall,
    )
    
# ======================================================
# INTERFACIAL AREAS
# ======================================================
def interfacial_areas(
    D,
    epsilon_bed,
    k_interfacial=1.0,
):

    # Gas-solid interfacial area density (m²/m³)
    a_gs_base = (
        6.0
        * (1.0 - epsilon_bed)
        / D
    )

    a_gs = k_interfacial * a_gs_base

    # Wall-solid interfacial area density (m²/m³)
    a_ws = 0.6 * a_gs

    return (
        a_gs,
        a_ws,
    )

# ======================================================
# BED FILL FRACTION FROM HOLDUP
#
# Steady-state mass continuity of the solid stream through
# a cross-section: m_dot_s = rho_bulk * u_s * A_bed, with
# A_bed = fill_fraction * A_cross. A fill fraction outside
# [0, 1) means the inputs are physically inconsistent, so
# it is rejected rather than clamped.
# ======================================================
def fill_fraction_from_holdup(
    m_dot_s,     # kg/s
    rho_bulk,    # kg/m³
    u_s,         # m/s
    A_cross,     # m²
):

    if m_dot_s < 0.0:
        raise ValueError(f"m_dot_s must be >= 0 kg/s, got {m_dot_s}")

    if rho_bulk <= 0.0 or u_s <= 0.0 or A_cross <= 0.0:
        raise ValueError(
            "rho_bulk, u_s and A_cross must be > 0, got "
            f"rho_bulk={rho_bulk}, u_s={u_s}, A_cross={A_cross}"
        )

    fill_fraction = m_dot_s / (rho_bulk * u_s * A_cross)

    if fill_fraction >= 1.0:
        raise ValueError(
            f"solid holdup exceeds the kiln cross-section: "
            f"fill_fraction={fill_fraction}"
        )

    return fill_fraction

# ======================================================
# BED SEGMENT GEOMETRY
#
# Rotary-kiln bed as a circular segment of the cross-section
# (flat bed surface, D = inner diameter). theta is the central
# angle the bed subtends:
#
#   fill_fraction = (theta - sin theta) / (2 pi)
#
# Area densities per unit kiln volume (m²/m³), A = pi D² / 4:
#
#   a_gs = D sin(theta/2) / A          bed surface (chord)
#   a_ws = (theta D / 2) / A           wall covered by the bed
#   a_gw = ((2 pi - theta) D / 2) / A  wall exposed to the gas
#
# a_ws + a_gw = 4 / D: the wall area is split, never created.
# D_e = 4 A_gas / P_gas is the hydraulic diameter of the gas
# passage (exposed arc + bed chord).
# ======================================================
def bed_segment_geometry(
    D,               # m
    fill_fraction,   # -
    tol=1e-14,
):

    if D <= 0.0:
        raise ValueError(f"D must be > 0 m, got {D}")

    if not (0.0 <= fill_fraction < 1.0):
        raise ValueError(
            f"fill_fraction must be in [0, 1), got {fill_fraction}"
        )

    # theta - sin(theta) is monotonic on [0, 2 pi]
    # (derivative 1 - cos(theta) >= 0), so bisection is exact
    # to tol and cannot pick a wrong root.
    target = 2.0 * np.pi * fill_fraction

    lo = 0.0
    hi = 2.0 * np.pi

    while hi - lo > tol:

        mid = 0.5 * (lo + hi)

        if mid - np.sin(mid) < target:
            lo = mid
        else:
            hi = mid

    theta = 0.5 * (lo + hi)

    A_cross = np.pi * D**2 / 4.0

    chord = D * np.sin(0.5 * theta)
    arc_covered = 0.5 * theta * D
    arc_exposed = 0.5 * (2.0 * np.pi - theta) * D

    a_gs = chord / A_cross
    a_ws = arc_covered / A_cross
    a_gw = arc_exposed / A_cross

    A_gas = (1.0 - fill_fraction) * A_cross
    P_gas = arc_exposed + chord

    D_e = 4.0 * A_gas / P_gas

    return (
        theta,
        a_gs,
        a_ws,
        a_gw,
        D_e,
    )

# ======================================================
# COVERED WALL -> BED CONTACT HEAT TRANSFER
#
# Extended penetration theory (Li et al., Chem. Eng. Technol.
# 2005): a bed element touches the covered wall for the
# contact time t_c = theta / omega, during which heat
# penetrates the bed as into a semi-infinite solid. Averaged
# over t_c this gives
#
#   h_pen = 2 sqrt(k_b rho_b cp_b / (pi t_c))
#
# in series with the gas gap between the wall and the first
# particle layer, chi d_p / k_g:
#
#   h_ws = 1 / (chi d_p / k_g + 1 / h_pen),  0.096 < chi < 0.198
#
# chi outside its fitted range is rejected, not clamped.
# ======================================================
CONTACT_GAP_CHI_RANGE = (0.096, 0.198)


def wall_bed_contact_coefficient(
    theta,     # rad, bed central angle (bed_segment_geometry)
    rpm,       # 1/min
    k_b,       # W/(m K), effective bed conductivity
    rho_b,     # kg/m³, bed bulk density
    cp_b,      # J/(kg K)
    d_p,       # m, particle diameter
    k_g,       # W/(m K), gas conductivity in the gap
    chi,       # -, gas gap thickness / d_p
):

    if theta <= 0.0 or rpm <= 0.0:
        raise ValueError(
            f"theta and rpm must be > 0, got theta={theta}, rpm={rpm}"
        )

    if min(k_b, rho_b, cp_b, d_p, k_g) <= 0.0:
        raise ValueError("k_b, rho_b, cp_b, d_p and k_g must be > 0")

    chi_min, chi_max = CONTACT_GAP_CHI_RANGE

    if not (chi_min <= chi <= chi_max):
        raise ValueError(
            f"chi must be in [{chi_min}, {chi_max}], got {chi}"
        )

    omega = 2.0 * np.pi * rpm / 60.0    # rad/s

    t_contact = theta / omega           # s

    h_pen = 2.0 * np.sqrt(
        k_b * rho_b * cp_b / (np.pi * t_contact)
    )

    R_gap = chi * d_p / k_g

    return 1.0 / (R_gap + 1.0 / h_pen)

# ======================================================
# WALL THERMAL RESISTANCE
# ======================================================
def wall_thermal_resistance(
    refractory_thickness,
    refractory_conductivity,
    h_ext,
    A_wall_cell,
):

    # Refractory conduction resistance (K/W)
    R_ref = (
        refractory_thickness
        / (
            refractory_conductivity
            * A_wall_cell
        )
    )

    # External convection resistance (K/W)
    R_conv = (
        1.0
        / (
            h_ext
            * A_wall_cell
        )
    )

    # Total thermal resistance (K/W)
    R_total = R_ref + R_conv

    return (
        R_ref,
        R_conv,
        R_total,
    )
    
