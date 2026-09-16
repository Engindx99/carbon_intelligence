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

    T = np.asarray(T, dtype=float)

    h = (
        1050.0 * (T - T_ref)
        + 0.09 * (T**2 - T_ref**2)
        - 1.0e-5 * (T**3 - T_ref**3)
    )

    return h


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

def radiation(T1, T2, zone, area=1.0):
    """ Stefan–Boltzmann radiation model with zone-dependent tuning."""
    

    cfg = ZONE_RAD_CONFIG[zone]

    eps = cfg["eps"]
    k_eff = cfg["k_eff"]
    

    q_rad = k_eff * eps * sigma * area * (T1**4 - T2**4)


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
    
