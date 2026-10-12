"""
Energy-balance rows for a stream whose mass flow varies along the zone.

A cement kiln's bed loses mass as it goes -- calcination sends CO2 out
of the solid and into the gas, cell by cell -- so in any zone where a
reaction runs, the flow entering a cell is not the flow leaving it. A
single scalar flow can therefore be correct in at most one cell, and at
the zone outlet it is usually the INLET value, which is how a zone comes
to hand its neighbour an enthalpy that inverts to the wrong temperature.
That error conserves J/s while rescaling K, so no energy residual can
see it.

These two builders write the balance on the two flows separately. They
live here, shared, rather than being copied into each zone, because the
arithmetic is subtle in ways that would not survive being maintained
twice: T_ref stops cancelling between the flux terms, the face
corrections can no longer be pre-differenced, and the phase-change term
has to appear in both rows with opposite signs or the zone balance does
not close.

Both reduce EXACTLY to the constant-flow forms they replace when the
inlet and outlet flows are equal and the mass transfer is zero, so a
zone with no reaction is numerically unaffected by adopting them.
"""

from physics.physics import cp_gas
from physics.physics import h_gas


# ======================================================
# GAS PHASE ENERGY BALANCE ROW
#
# Builds the gas-side row of a zone's 3N linear system for
# cell i, in place. First written for the transition zone
# (Faz 1b) and shared with the calciner unchanged (Faz 1c).
#
# Gas direction: N-1 -> 0.
#
# The deferred corrections enter b only, so A stays the
# diagonally dominant upwind M-matrix. Same construction as
# pyroprocess/burning/gas_phase.py.
# ======================================================
def apply_gas_energy_balance(
    A,
    b,
    row,
    i,
    N,
    Tg_iter,
    T_ref,
    mg_out,
    mg_in,
    dm_gas,
    cp_gas_s,
    h_const_s,
    V_cell,
    K_gs,
    K_gw,
    radiation_gas_sink,
    Tg_in,
    D_in=0.0,
    D_out=0.0,
):
    """
    THE STREAM GAINS MASS. The CO2 the bed releases in this cell
    joins the gas here, so the flow leaving the cell is not the
    flow that entered it:

      mg_out (h_i + D_out) - mg_in (h_{i+1} + D_in)
        - dm_gas * h_gas(Ts_i)                 <- CO2 arriving
        + V K_gs (Tg - Ts) + V K_gw (Tg - Tw)
      = -radiation_gas_sink

    The `dm_gas * h_gas(Ts_i)` term is the same one the solid
    row subtracts, so summing the two rows over the zone leaves
    only the stream boundaries: the CO2 crosses phases without
    creating or destroying energy, at the bed temperature it
    actually left.

    Each face carries its own flow, so D_in and D_out are taken
    per face (physics.second_order_upwind_face_corrections)
    rather than pre-differenced. The gas inlet face carries no
    correction -- it is a known handoff, not a reconstruction --
    which is D[0] == 0 by construction there.

    With mg_in == mg_out and dm_gas == 0 this reduces exactly to
    the constant-flow form it replaces.
    """

    Tg_i = i
    Ts_i = N + i
    Tw_i = 2 * N + i

    Cp_g_i = cp_gas(
        Tg_iter[i]
    )

    h_i_iter = h_gas(
        Tg_iter[i],
        T_ref
    )

    h_linear_const_i = (
        h_i_iter
        - Cp_g_i * Tg_iter[i]
    )

    A[row, Tg_i] += (
        mg_out * Cp_g_i
        + V_cell * K_gs
        + V_cell * K_gw
    )

    A[row, Ts_i] += (
        -V_cell * K_gs
        - dm_gas * cp_gas_s
    )

    A[row, Tw_i] += (
        -V_cell * K_gw
    )

    b_common = (
        -radiation_gas_sink
        - mg_out * h_linear_const_i
        - mg_out * D_out
        + dm_gas * h_const_s
    )

    if i == N - 1:

        h_in = h_gas(
            Tg_in,
            T_ref
        )

        b[row] = (
            b_common
            + mg_in * h_in
            + mg_in * D_in
        )

    else:

        Tg_up_i = i + 1

        Cp_g_up = cp_gas(
            Tg_iter[i + 1]
        )

        h_up_iter = h_gas(
            Tg_iter[i + 1],
            T_ref
        )

        h_linear_const_up = (
            h_up_iter
            - Cp_g_up * Tg_iter[i + 1]
        )

        A[row, Tg_up_i] += (
            -mg_in * Cp_g_up
        )

        b[row] = (
            b_common
            + mg_in * h_linear_const_up
            + mg_in * D_in
        )

    return row + 1


# ======================================================
# SOLID PHASE ENERGY BALANCE ROW
#
# Builds the solid-side row of a zone's 3N linear system for
# cell i, in place. First written for the transition zone
# (Faz 1b) and shared with the calciner unchanged (Faz 1c).
# Takes this cell's reaction heat sink as an explicit
# parameter instead of computing it inline, so a zone with
# more than one reaction (the calciner calcines AND
# dehydroxylates) passes their sum and the row does not need
# to know which reactions its caller runs.
#
# Solid direction: 0 -> N-1.
#
# THE STREAM LOSES MASS. The reactions send gas out of the bed
# cell by cell, so the flow entering a cell is not the flow
# leaving it, and the balance is written on the two flows
# separately:
#
#   Cs_out (Ts_i + D_out - T_ref)
#     - Cs_in (Ts_{i-1} + D_in - T_ref)
#     + dm_gas * h_gas(Ts_i)                 <- CO2 leaving
#     + V K_gs (Ts - Tg) + V K_ws (Ts - Tw)
#   = radiation_solid_source - Q_reaction_cell
#
# Two things follow from the variable flow that do not arise
# with a constant one:
#
#   - T_ref no longer cancels between the two flux terms, so
#     (Cs_out - Cs_in) * T_ref appears explicitly;
#   - the face corrections cannot be pre-differenced, because
#     each face carries its own flow. D_in and D_out come from
#     physics.second_order_upwind_face_corrections.
#
# `dm_gas` is the mass this cell hands to the gas. It leaves
# at the local bed temperature carrying its GAS-phase
# enthalpy h_gas(Ts_i), and the gas row adds exactly the same
# term with the opposite sign, so the two cancel when the zone
# balance is summed and no arbitrary transfer term is needed.
# The reaction enthalpy stays on the solid at T_ref, where
# chemistry.calcination.deltaH is defined.
#
# h_gas(Ts) is nonlinear in Ts, so it is linearised at the
# current iterate the same way the gas row linearises its own
# enthalpy: h_gas(Ts) ~ cp_gas_s * Ts + h_const_s.
#
# THE REACTION SINK IS LINEARISED THE SAME WAY, for the same
# reason and by the same device -- see dQ_dTs_cell below.
#
# With Cs_in == Cs_out and dm_gas == 0 this reduces exactly to
# the constant-flow form it replaces.
#
# ------------------------------------------------------
# dQ_dTs_cell / Ts_star_cell -- SOURCE-TERM LINEARISATION
#
# Q_reaction_cell is evaluated at some iterate Ts*, and until
# Faz 6 item 1.5 that was the whole story: the sink went into
# b as a constant and contributed NOTHING to the diagonal. The
# reaction's response to temperature was then resolved by
# successive substitution between the chemistry pass and the
# thermal solve.
#
# That works only while dQ/dTs is small. Calcination at a
# literature rate crosses six orders of magnitude of k within
# one cell's temperature span, the fixed-point map's Jacobian
# passes 1 in magnitude, and the plant limit-cycles -- measured
# at a thermal residual pinned near 290 K that does not decay,
# with no damping weight able to remove it.
#
# The standard finite-volume treatment of a strongly
# temperature-dependent source is to split it about the current
# iterate and carry the slope in the matrix (Patankar,
# Numerical Heat Transfer and Fluid Flow, 1980, ch. 7: a source
# linearised as S = S_C + S_P T must have S_P <= 0):
#
#   Q(Ts) ~ Q(Ts*) + S (Ts - Ts*),   S = dQ/dTs >= 0
#
# so +S joins the diagonal and -(Q(Ts*) - S Ts*) stays in b.
# Here S_P = -S <= 0 because a hotter cell reacts faster and
# absorbs MORE heat, which is what makes the rule apply.
#
# Three consequences, and the third is the point:
#
#   - it cannot move the answer. At the fixed point Ts == Ts*
#     and the two added terms cancel identically, so this is a
#     PATH change only, exactly like the h_gas linearisation
#     above and like burning's calcination_relaxation;
#   - S >= 0 always, so the diagonal only ever grows: the
#     system is more diagonally dominant than before, never
#     less;
#   - the stiffer the chemistry, the LARGER S is, and the
#     harder the cell is pinned to the temperature at which
#     reaction heat balances supply. Stiffness becomes
#     self-damping instead of destabilising, and the
#     calcination plateau falls out of the energy balance
#     rather than being imposed by a clamp or a heat budget.
#
# Defaults of 0.0 reproduce the previous arithmetic exactly
# (x + 0.0 == x, x - 0.0 * 0.0 == x), so a caller that has not
# been taught the slope is bit-identical.
# ======================================================
def apply_solid_energy_balance(
    A,
    b,
    row,
    i,
    N,
    Cs_out,
    Cs_in,
    T_ref,
    dm_gas,
    cp_gas_s,
    h_const_s,
    V_cell,
    K_gs,
    K_ws,
    radiation_solid_source,
    Q_reaction_cell,
    Ts_in,
    D_in=0.0,
    D_out=0.0,
    dQ_dTs_cell=0.0,
    Ts_star_cell=0.0,
    C_dt_cell=0.0,
    Ts_old_cell=0.0,
    H_mass_stored_cell=0.0,
):
    # C_dt_cell / Ts_old_cell -- STORED ENERGY (dynamic solve only).
    # Implicit Euler on the bed's sensible heat: C/dt (Ts - Ts_old)
    # joins the outflow side, so +C/dt goes on the diagonal and
    # +C/dt Ts_old into b. C is the cell's solid hold-up times
    # Cp_s. The defaults of 0.0 leave the steady row unchanged.
    #
    # H_mass_stored_cell [W] -- the other half of d(M h)/dt when the
    # hold-up M itself changes over the step (the kiln's parcel
    # train): (M_new h_new - M_old h_old)/dt = C_new/dt (Ts - Ts_old)
    # + h(Ts_old) (M_new - M_old)/dt, with C_new = M_new Cp_s. The
    # second term is a constant of the step, so it goes into b on
    # the outflow side. With it the row closes on the bed's mass
    # balance in - out - CO2 = dM/dt, which no longer vanishes.

    Tg_i = i
    Ts_i = N + i
    Tw_i = 2 * N + i

    A[row, Ts_i] += (
        Cs_out
        + dm_gas * cp_gas_s
        + V_cell * K_gs
        + V_cell * K_ws
        + dQ_dTs_cell
        + C_dt_cell
    )

    A[row, Tg_i] += (
        -V_cell * K_gs
    )

    A[row, Tw_i] += (
        -V_cell * K_ws
    )

    # Constants common to both ends of the cell.
    #
    # The sink appears as its value at Ts* minus the slope
    # already moved to the diagonal, so the pair reconstructs
    # Q(Ts*) exactly when the solve returns Ts == Ts*.
    b_common = (
        radiation_solid_source
        - (Q_reaction_cell - dQ_dTs_cell * Ts_star_cell)
        - dm_gas * h_const_s
        - Cs_out * D_out
        + Cs_in * D_in
        + (Cs_out - Cs_in) * T_ref
        + C_dt_cell * Ts_old_cell
        - H_mass_stored_cell
    )

    if i == 0:
        b[row] = (
            Cs_in * Ts_in
            + b_common
        )
    else:
        Ts_up_i = N + i - 1
        A[row, Ts_up_i] += -Cs_in
        b[row] = b_common

    return row + 1
