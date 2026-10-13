import numpy as np

from physics.physics import rotary_bed_motion
from physics.physics import outlet_face_value
from physics.physics import T_solid_from_h


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
    # Sullivan's transit correlation (physics.rotary_bed_motion)
    # gives tau from the geometry and the motion; the bed fill
    # fraction then follows from mass continuity. It is an
    # OUTPUT here, not an input -- the correlation has no
    # fill-fraction term.
    #
    # This used to pass burning.fill_fraction, read from
    # operational.kiln_load, which the config sets to 1.0 -- a
    # capacity-utilisation figure standing in for a bed fill
    # fraction, i.e. a completely full kiln. That was replaced
    # by a continuity closure, and the closure has now been
    # replaced in turn by the correlation the closure was
    # standing in for.
    #
    # NOTE ON L. tau scales with L and u_s = L/tau does not, so
    # passing the burning zone's length rather than the whole
    # tube's changes nothing about the velocity the zones share.
    # state.residence_time is therefore the BURNING ZONE's
    # transit; the tube's is kiln.length / u_s.
    # ======================================================

    tau, u_s, bed_fill_fraction = rotary_bed_motion(
        L=burning.L,
        D=burning.D,
        slope_deg=burning.slope_deg,
        rpm=rpm,
        repose_deg=burning.repose_deg,
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

    state.Ts_burning_in = T_solid_from_h(
        state.Hsolid_burning_in / m_dot_s_in,
        burning.T_ref,
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
# The scheme reconstructs the solid in enthalpy (h_solid), so
# the extrapolation is taken on Hs directly.
# ======================================================
def solid_enthalpy_out(Hs):

    return outlet_face_value(Hs, reverse=False)
