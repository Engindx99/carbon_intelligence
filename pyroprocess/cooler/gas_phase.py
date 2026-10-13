import numpy as np

from physics.physics import cp_gas
from physics.physics import h_gas
from physics.physics import T_gas_from_h


# ======================================================
# PER-CELL COOLING AIR
#
# A grate cooler is not a duct. Each segment of the grate has
# its own undergrate fan box and blows its own fresh ambient
# air UP through the clinker bed; that air leaves through the
# hood at that segment's temperature and is taken off as
# secondary, tertiary or vent depending on where along the
# grate it sits. It does not travel the length of the cooler.
#
# Source: Svensen, Leal da Silva, Pigazo Merino, Sampath &
# Jorgensen, "A Dynamic Cooler Model for Cement Clinker
# Production", arXiv:2409.09076 (2024) -- the same DTU
# pyro-section series as the calcination kinetics this repo
# already uses (Ritschel et al., arXiv:2405.03208). Their
# cooler is 10 finite-volume segments, each with its own air
# inflow (40.89 kg/s on segment 1, 18.56 on segment 2, 16.24
# on each of 3-10); secondary air is segment 1's air at
# 1088.7 C and tertiary is segment 2's at 899.1 C.
#
# UNIFORM here, rather than their hot-end-weighted profile.
# That profile is one plant's grate design and is not measured
# for the generic reference kiln this config describes;
# uniform introduces no fitted parameter and no new config
# key. A cooler_air.grate_air_profile hook is the obvious
# extension and is deliberately not built.
#
# WHY THIS MATTERS. As one lumped counter-current stream the
# whole 2.2 kg air/kg clinker had to share one outlet
# temperature, which put C_air/C_solid at 2.91 and capped the
# air rise at 266 K -- secondary air measured 586.06 K against
# BOUNDS["secondary_air"] = (1050, 1350). The cooler was at
# ~100% counter-current effectiveness; it was not broken. The
# air simply cannot get hot when its heat-capacity rate is
# 2.9x the clinker's. Secondary air alone is 0.65 kg/kg
# clinker here and 0.771 in the source, and it is that smaller
# stream, drawn off the hot end only, that can reach the band.
# ======================================================
def cooler_air_cells(cooler, state):

    return np.full(
        cooler.N,
        float(state.m_dot_air_cooler) / cooler.N,
        dtype=float,
    )


# ======================================================
# THROUGH-BED GAS->SOLID COEFFICIENT
#
# The cell's gas row is a well-mixed balance: the air leaves at
# the cell temperature Tg and exchanges K_gs (Tg - Ts) with the
# bed. That gives the cell an effectiveness NTU / (1 + NTU).
# But the air does not mix inside the bed: it crosses it once,
# bottom to top, past clinker whose temperature is uniform
# across the cell (the bed moves along the grate, not up). That
# is a stream past an isothermal surface, effectiveness
# 1 - exp(-NTU) (Incropera & DeWitt, Fundamentals of Heat and
# Mass Transfer, sec. 11.3, C_r = 0).
#
# MEASURED on the FLS cooler scenario (Svensen et al. 2024,
# arXiv:2409.09076 sec. IV: 53.06 kg/s clinker at 1723 K, air
# 40.89 / 18.56 / 8 x 16.24 kg/s): NTU ~5.3 per cell, so the
# well-mixed row gave 0.84 where the bed gives 0.995, and
# secondary air came out 1212 K against the paper's 1362 K.
#
# The row keeps its well-mixed form and takes the coefficient
# that makes it exact: with K_eff V = C (exp(NTU) - 1),
# K_eff V / (C + K_eff V) = 1 - exp(-NTU). The same coefficient
# goes into the solid row, so whatever the gas gains the bed
# loses, to the last bit.
#
# NTU_CAP: past NTU 20 the effectiveness is 1 to 2e-9, i.e.
# under 1e-5 K on a 1500 K approach; exp() would only push the
# matrix condition up (exp(20) C ~ 1e12 already) for nothing.
# ======================================================
NTU_CAP = 20.0


def through_bed_hv_gs(cooler, m_air_cells, Tg, V_cell, a_gs):

    a_gs = np.broadcast_to(np.asarray(a_gs, dtype=float), (cooler.N,))
    V_cell = np.broadcast_to(np.asarray(V_cell, dtype=float), (cooler.N,))

    C = np.asarray(m_air_cells, dtype=float) * np.asarray(
        cp_gas(np.asarray(Tg, dtype=float)),
        dtype=float,
    )

    KV = cooler.hv_gs * a_gs * V_cell

    # No air through a cell: no stream to rate, the bed sees
    # the plain film coefficient.
    has_air = C > 0.0

    NTU = np.where(has_air, KV / np.where(has_air, C, 1.0), 0.0)

    KV_eff = np.where(
        has_air,
        C * np.expm1(np.minimum(NTU, NTU_CAP)),
        KV,
    )

    return KV_eff / (a_gs * V_cell)


# ======================================================
# GAS PHASE ENERGY BALANCE ROWS
#
# Moved from the gas block inside Cooler.thermal_step()
# (pyroprocess/cooler.py). Logic is unchanged; `self` was
# renamed to `cooler` since this is now a free function
# taking the owning Cooler instance explicitly.
#
# CROSS-FLOW. Each cell's gas is its own stream: it enters
# from the undergrate fan box at the ambient inlet condition,
# crosses the bed once, and leaves through the hood at that
# cell's temperature. There is NO axial gas transport, so
# there is no upstream cell, no sweep direction and no inlet
# cell. Cell i's row is simply
#
#   m_air[i] * (h(Tg_i) - h(Tg_in)) + Q_gs,i + Q_gw,i = 0
#
# The gas-to-gas block of A is therefore DIAGONAL. The rows
# keep their couplings to the solid and wall unknowns through
# K_gs and K_gw; only the gas-to-gas coupling disappears.
# Every gas cell is now anchored directly to the inlet
# condition instead of through a chain of N, which makes the
# block strictly more diagonally dominant than the upwind
# operator it replaces.
#
# WHAT LEAVES WITH THE ADVECTION, and why that is not a loss
# of accuracy. The counter-current form needed a van Leer
# deferred correction (physics.second_order_upwind_correction)
# matched to an outlet-FACE reconstruction, because
# first-order upwind smeared the steep axial gradient the
# recuperator was made of. Both were a matched pair: the
# reconstruction is exactly what made the telescoped row sum
# equal m_dot_g*(h_face - h_in). With no axial flux there is
# nothing to reconstruct and nothing to smear, and the row sum
#
#   sum_i m_air[i]*h(Tg_i) - m_total*h(Tg_in)
#       + V_cell*sum(q_gs + q_gw) = 0
#
# is an identity rather than the consequence of a matched
# pair. That is `gas_gap` in heat_transfer.py's residual
# decomposition, and it should become structurally exact.
#
# WHAT STAYS. The convective term is still written in
# ENTHALPY, and h_gas is still cubic in T, so each cell still
# carries the first-order Taylor expansion of h_gas about the
# frozen Picard iterate,
#
#   h_lin(T) = Cp_g * T + h_linear_const
#
# which is EXACT at the fixed point. It is the linearisation,
# not the advection, that makes this non-linear. What did
# disappear is the UPSTREAM cell's linearisation: the inlet
# enthalpy is now a known constant, identical in every cell.
#
# The solid still flows 0 -> N-1 (solid_phase.py, unchanged
# and still genuinely axial, with its own reconstruction).
# ======================================================
def apply_gas_energy_balance(
    A,
    b,
    row,
    N,
    Tg_in,
    Tg_iter,
    Ts_iter,
    Tw_iter,
    T_ref,
    m_air_cells,
    V_cell,
    K_gs,
    K_gw,
    q_gs,
    q_gw,
):

    # Per-cell bed volumes and coefficients (Cooler.bed_geometry);
    # a scalar is taken as the same value in every cell.
    V_cell = np.broadcast_to(np.asarray(V_cell, dtype=float), (N,))
    K_gs = np.broadcast_to(np.asarray(K_gs, dtype=float), (N,))
    K_gw = np.broadcast_to(np.asarray(K_gw, dtype=float), (N,))

    # The inlet stream is the same ambient condition for every
    # fan box, so this is one constant, not a per-cell lookup.
    h_in = float(
        h_gas(
            Tg_in,
            T_ref,
        )
    )

    for i in range(N):

        gas_i = i
        solid_i = N + i
        wall_i = 2 * N + i

        # ----------------------------------------------
        # m_air[i] (h_g,i - h_in)
        #
        # + Q_gs
        # + Q_gw
        # = 0
        #
        # h_gas is cubic in T, so it cannot enter the
        # linear system directly. Each node carries a
        # first-order Taylor expansion of h_gas about the
        # frozen Picard iterate,
        #
        #   h_lin(T) = Cp_g * T + h_linear_const
        #
        # which is EXACT at the fixed point, where
        # T == Tg_iter and h_lin collapses back onto
        # h_gas. The linearization slope therefore sets the
        # convergence rate, not the converged answer.
        #
        # Summed over the cells these do NOT telescope --
        # there is no chain to telescope along. They add
        # directly to
        #
        #   sum_i m_air[i]*h(Tg_i) - m_total*h(Tg_in)
        #
        # which is exactly the Hg_out - Hg_in that
        # heat_transfer.py books, with no reconstruction in
        # between. Tg_i IS the outlet state of cell i's
        # stream, not a cell average on the way somewhere.
        # ----------------------------------------------

        m_air_i = float(m_air_cells[i])

        Cp_g_i = float(
            cp_gas(Tg_iter[i])
        )

        Cg_i = m_air_i * Cp_g_i

        h_linear_const_i = (
            float(
                h_gas(
                    Tg_iter[i],
                    T_ref,
                )
            )
            - Cp_g_i * Tg_iter[i]
        )

        A[row, gas_i] += (
            Cg_i
            + V_cell[i] * K_gs[i]
            + V_cell[i] * K_gw[i]
        )

        A[row, solid_i] += (
            -V_cell[i] * K_gs[i]
        )

        A[row, wall_i] += (
            -V_cell[i] * K_gw[i]
        )

        # Radiation part is already contained in
        # heat_transfer(). Freeze nonlinear radiation
        # contribution at current Picard iteration.

        q_rad_gs = (
            q_gs[i]
            - K_gs[i] * (
                Tg_iter[i]
                - Ts_iter[i]
            )
        )

        q_rad_gw = (
            q_gw[i]
            - K_gw[i] * (
                Tg_iter[i]
                - Tw_iter[i]
            )
        )

        # Every cell is an inlet cell now: its upstream
        # enthalpy is the known fan-box stream, a constant
        # flux rather than a coupling to a neighbour. The
        # i == N-1 / else branch the counter-current form
        # needed has no meaning here, and neither does
        # A[row, gas_up] -- there is no gas_up.
        b[row] = (
            -V_cell[i] * (
                q_rad_gs
                + q_rad_gw
            )
            - m_air_i * h_linear_const_i
            + m_air_i * h_in
        )

        row += 1

    return row


# ======================================================
# WHICH STREAM EACH CELL'S AIR JOINS
#
# There is no single gas outlet face any more. Each cell's
# air leaves vertically through the hood at Tg[i], so the
# cooler has N outlets and the question is which take-off
# each one feeds. Hot end first, in the order a plant is
# plumbed: the kiln hood sits over the clinker-inlet end and
# takes secondary air off the hottest grate, the tertiary
# duct taps immediately downstream, and whatever is left
# vents. The source does the same -- secondary is its segment
# 1 and tertiary its segment 2.
#
# The masses are NOT decided here. main.py:1074-1097 sets
# them from combustion stoichiometry (secondary is the kiln's
# air less its primary share, tertiary IS the calciner's
# combustion air) and leaves vent as the slack. This function
# only says where along the grate each of those masses is
# drawn from.
#
# FRACTIONAL BOUNDARIES, not whole cells. A stream's mass
# will not land on a cell edge -- secondary is 5.94 cells
# wide at the committed point -- and rounding to whole cells
# would make the reported temperature jump by a whole cell's
# worth whenever the fuel rate moved, which is a
# discretisation artifact and not physics.
#
# THREE PROPERTIES, EACH LOAD-BEARING:
#
#  1. vent is the RESIDUAL, m - w_sec - w_ter, not computed
#     independently. That makes w_sec[i] + w_ter[i] +
#     w_vent[i] == m[i] exact in floating point for every
#     cell, with no sensitivity to summation order, which in
#     turn makes H_sec + H_ter + H_vent == Hgas_cooler_out an
#     identity. Four places depend on that identity:
#     main.py:315-323 recovers primary air by SUBTRACTING
#     secondary from Hgas_burning_in; main.py:347 and
#     diagnostics.py:1117 put vent on the OUT side; and
#     diagnostics.py:1136-1140 repeats the subtraction in
#     D12. Vent is already the algebraic slack upstream, so
#     this is the same modelling choice, not a new one.
#
#  2. The boundaries are CLIPPED, so the function stays total
#     even on an infeasible split. main.py:1099 raises first,
#     but cooler.apply must not be able to emit negative mass
#     regardless.
#
#  3. min/max on cumulative mass, never int(m_sec/m). No
#     floor, no ceil, no epsilon, no branch on whether a
#     boundary lands exactly on a cell edge. The degenerate
#     cases -- a zero-mass stream, a boundary on an edge --
#     fall out as zero weights with no special-casing.
# ======================================================
def stream_masses(cooler, state):

    m_air = cooler_air_cells(cooler, state)

    edges = np.concatenate(([0.0], np.cumsum(m_air)))

    total = float(edges[-1])

    lo_sec = 0.0
    hi_sec = min(max(float(state.m_dot_secondary_air), 0.0), total)

    hi_ter = min(
        max(hi_sec + float(state.m_dot_tertiary_air), hi_sec),
        total,
    )

    def overlap(lo, hi):
        return np.maximum(
            0.0,
            np.minimum(edges[1:], hi) - np.maximum(edges[:-1], lo),
        )

    w_secondary = overlap(lo_sec, hi_sec)
    w_tertiary = overlap(hi_sec, hi_ter)

    # The residual, for the reason in note 1 above.
    w_vent = m_air - w_secondary - w_tertiary

    return w_secondary, w_tertiary, w_vent


# ======================================================
# GAS ENTHALPY SPLIT (secondary / tertiary / vent)
#
# Each stream is the mass-weighted sum of the cell outlet
# enthalpies it draws from. h_gas is evaluated ONCE over the
# whole profile and reused for all three, so the three sums
# are taken over the same numbers -- which is what makes the
# identity in note 1 above hold to the last bit rather than
# to a rounding order.
# ======================================================
def gas_enthalpy_split(cooler, Tg, state):

    h_cells = np.asarray(
        h_gas(
            np.asarray(Tg, dtype=float),
            cooler.T_ref,
        ),
        dtype=float,
    )

    w_secondary, w_tertiary, w_vent = stream_masses(cooler, state)

    return (
        float(np.dot(w_secondary, h_cells)),
        float(np.dot(w_tertiary, h_cells)),
        float(np.dot(w_vent, h_cells)),
    )


# ======================================================
# GAS ENTHALPY LEAVING THE COOLER
#
# Defined as the SUM of the three streams rather than as an
# independent cell sum, so the two cannot drift apart by a
# rounding order. heat_transfer.py books this same value as
# Hg_out, through this same function, for the same reason.
#
# Kept as a function with its original signature because
# cooler.py:278 and Cooler.gas_enthalpy_out are public
# interface; only what it computes changed.
# ======================================================
def gas_enthalpy_out(cooler, Tg, state):

    return sum(
        gas_enthalpy_split(
            cooler,
            Tg,
            state,
        )
    )


# ======================================================
# STREAM TEMPERATURES
#
# The cooler publishes its three air streams as ENTHALPY
# flows and nothing anywhere published their temperatures --
# downstream zones invert what they receive, mixed with
# whatever else they receive. That left
# BOUNDS["secondary_air"], which is a bound on secondary air
# ALONE, with no secondary air temperature to be checked
# against, so D2 was checking it against state.Tg_burning_in
# instead: the BURNER MIXTURE of secondary air, ambient
# primary air and the fuel's mass.
#
# MEASURED, at the committed operating point, what that
# substitution costs:
#
#   true secondary   D2 reads   verdict vs (1050, 1350)
#      586.06 K       540.81 K    fail
#     1050.00 K       933.92 K    fail   <- the band's own floor
#     1150.00 K      1018.90 K    fail
#     1350.00 K      1189.05 K    pass
#
# The check could not be satisfied at the floor of its own
# band however well the cooler worked. It is mis-aimed by
# 116-161 K.
#
# Each stream is inverted on the mass IT carries, so this
# stays correct when the streams stop sharing one
# temperature. Reporting only: nothing consumes these.
# ======================================================
def stream_temperatures(
    cooler,
    H_secondary,
    H_tertiary,
    H_vent,
    state,
):

    def invert(H, m_dot):

        if m_dot <= cooler.eps:
            return cooler.T_ref

        return T_gas_from_h(
            H / m_dot,
            cooler.T_ref,
            cooler.T_ref,
            4000.0,
        )

    return (
        invert(H_secondary, state.m_dot_secondary_air),
        invert(H_tertiary, state.m_dot_tertiary_air),
        invert(H_vent, state.m_dot_vent_air),
    )
