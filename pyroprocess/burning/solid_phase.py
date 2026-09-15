import numpy as np

from physics.physics import residence_time
from physics.physics import solid_axial_velocity


# ======================================================
# SOLID MOTION & MASS FLOW
#
# Moved from Burning.apply() (pyroprocess/burning.py).
# Logic is unchanged; `self` was renamed to `burning`
# since these are now free functions taking the owning
# Burning instance explicitly.
# ======================================================
def resolve_solid_motion(burning, state, inputs):

    rpm = np.clip(
        inputs.get("rpm", burning.rpm_default),
        burning.rpm_min,
        burning.rpm_max,
    )

    tau = residence_time(
        L=burning.L,
        D=burning.D,
        slope_deg=burning.slope_deg,
        fill_fraction=burning.fill_fraction,
        rpm=rpm,
        eps=burning.eps,
    )

    u_s = solid_axial_velocity(
        L=burning.L,
        D=burning.D,
        slope_deg=burning.slope_deg,
        fill_fraction=burning.fill_fraction,
        rpm=rpm,
        eps=burning.eps,
    )

    state.rpm = rpm
    state.residence_time = tau
    state.u_s = u_s
    state.solid_velocity = u_s

    return u_s


# ======================================================
# SOLID INLET HANDOFF
#
# Moved from Burning.apply() (pyroprocess/burning.py).
# Logic is unchanged.
# ======================================================
def resolve_solid_inlet(burning, state):

    state.Hsolid_burning_in = state.Hsolid_transition_out

    state.Ts_burning_in = (
        burning.T_ref
        + state.Hsolid_burning_in
        / (state.m_dot_s * burning.Cp_s)
    )

    return state.Ts_burning_in


# ======================================================
# SOLID ENTHALPY TO NEXT ZONE
#
# Moved from Burning.solid_enthalpy_out()
# (pyroprocess/burning.py). Logic is unchanged.
# ======================================================
def solid_enthalpy_out(Hs):

    return Hs[-1]


# ======================================================
# SOLID PHASE ENERGY BALANCE ROW
#
# Moved from the per-cell loop inside Burning.thermal_step()
# (pyroprocess/burning.py). Builds the solid-side row of the
# 3N linear system for cell i in place, using the same
# arithmetic and operand order as the original code so the
# Picard solve is numerically unchanged.
#
# Solid direction: 0 -> N-1.
# ======================================================
def apply_solid_energy_balance(
    A,
    b,
    row,
    i,
    N,
    Cs,
    V_cell,
    K_gs,
    K_ws,
    radiation_solid_source,
    Ts_in,
):

    Tg_i = i
    Ts_i = N + i
    Tw_i = 2 * N + i

    A[row, Ts_i] += (
        Cs
        + V_cell * K_gs
        + V_cell * K_ws
    )

    A[row, Tg_i] += (
        -V_cell * K_gs
    )

    A[row, Tw_i] += (
        -V_cell * K_ws
    )

    if i == 0:

        b[row] = (
            Cs * Ts_in
            + radiation_solid_source
        )

    else:

        Ts_up_i = N + i - 1

        A[row, Ts_up_i] += (
            -Cs
        )

        b[row] = (
            radiation_solid_source
        )

    return row + 1
