import numpy as np

from physics.physics import bed_motion_from_continuity
from physics.physics import outlet_face_value


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

    # ======================================================
    # The transit time and the bed fill are one unknown, not
    # two: the correlation gives tau from the fill fraction and
    # mass continuity gives the fill fraction back from tau.
    # bed_motion_from_continuity solves that pair in closed form.
    #
    # This used to pass burning.fill_fraction, read from
    # operational.kiln_load, which the config sets to 1.0 -- a
    # capacity-utilisation figure standing in for a bed fill
    # fraction, i.e. a completely full kiln. That made the
    # transit time 5.4 min against the ~an-hour the same
    # correlation gives once the bed is consistent with the feed
    # rate, and every residence-time-driven reaction rate was
    # scaled by it.
    # ======================================================

    tau, u_s, bed_fill_fraction = bed_motion_from_continuity(
        L=burning.L,
        D=burning.D,
        slope_deg=burning.slope_deg,
        rpm=rpm,
        m_dot_s=state.m_dot_s,
        rho_bulk=burning.rho_s,
        A_cross=burning.A_cross,
        eps=burning.eps,
    )

    state.rpm = rpm
    state.residence_time = tau
    state.u_s = u_s
    state.solid_velocity = u_s
    state.bed_fill_fraction = bed_fill_fraction

    return u_s


# ======================================================
# SOLID INLET HANDOFF
#
# Moved from Burning.apply() (pyroprocess/burning.py).
# Logic is unchanged.
# ======================================================
def resolve_solid_inlet(burning, state):

    state.Hsolid_burning_in = state.Hsolid_transition_out

    # The INLET flow, not state.m_dot_s -- that is the clinker,
    # and the bed is heavier here by the CO2 it has yet to
    # release. The transition built this enthalpy on the flow it
    # discharged, so the inversion has to use the same one or the
    # handoff conserves J/s while rescaling K.
    m_dot_s_in = float(
        getattr(
            state,
            "m_dot_s_burning_in",
            state.m_dot_s,
        )
    )

    state.Ts_burning_in = (
        burning.T_ref
        + state.Hsolid_burning_in
        / (m_dot_s_in * burning.Cp_s)
    )

    return state.Ts_burning_in


# ======================================================
# SOLID ENTHALPY TO NEXT ZONE
#
# Moved from Burning.solid_enthalpy_out()
# (pyroprocess/burning.py).
#
# This used to return Hs[-1], the last CELL CENTRE, while
# the clinker actually discharges through the outlet FACE
# half a cell further on -- a systematic O(dz) bias in the
# kiln's single most important handoff, since this value
# becomes state.Hsolid_cooler_in. It is also the flux the
# second-order scheme in apply_solid_energy_balance()
# transports out of the last cell, so it must be the value
# handed off or the difference leaks.
#
# Hs is m_dot_s * Cp_s * (Ts - T_ref) elementwise, i.e.
# affine in Ts, so the extrapolation may be taken on Hs
# directly.
# ======================================================
def solid_enthalpy_out(Hs):

    return outlet_face_value(Hs, reverse=False)


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
#
# `reaction_q_cell_i` is the clinkering enthalpy consumed in
# this cell [W]. The reactions run in the bed, so the heat
# leaves the solid, exactly as calcination does on the solid
# rows of the transition zone and the calciner. It was
# previously subtracted from the gas row instead, which left
# the bed temperature unaffected by its own reactions.
# Like the radiation and advection terms it enters b only.
#
# `advection_correction` is the per-cell van Leer deferred
# correction from physics.second_order_upwind_correction,
# in temperature units (K) -- the solid flux
# Cs * (Ts - T_ref) is affine in Ts, so the reconstruction
# is done on Ts directly. It is zero by default, which
# leaves this row exactly first-order upwind as before, and
# it enters b only so that A stays the diagonally dominant
# upwind M-matrix. See the gas-side note in gas_phase.py.
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
    reaction_q_cell_i,
    Ts_in,
    advection_correction=0.0,
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
            - reaction_q_cell_i
            - Cs * advection_correction
        )

    else:

        Ts_up_i = N + i - 1

        A[row, Ts_up_i] += (
            -Cs
        )

        b[row] = (
            radiation_solid_source
            - reaction_q_cell_i
            - Cs * advection_correction
        )

    return row + 1
