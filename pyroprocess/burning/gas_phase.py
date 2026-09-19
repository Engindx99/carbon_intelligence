from physics.physics import cp_gas
from physics.physics import h_gas
from physics.physics import outlet_face_value
from physics.physics import T_gas_from_h


# ======================================================
# GAS INLET HANDOFF
#
# Moved from Burning.apply() (pyroprocess/burning.py);
# `self` was renamed to `burning` since these are now free
# functions taking the owning Burning instance explicitly.
#
# The kiln's inlet gas is now a mix of two streams: primary
# air (ambient T, carries the fuel, sized by
# burning.primary_air_fraction) and secondary air (preheated
# by the cooler, pyroprocess/cooler/gas_phase.py's split), so
# mixing is a plain enthalpy sum -- no new mixing formula is
# needed.
#
# The two masses sum to mass_flow.m_dot_air_kiln, NOT to
# state.m_dot_air. This comment used to say m_dot_air and was
# wrong: main.py:853-863 makes m_dot_air the PLANT total and
# m_dot_air_kiln = kiln_fraction * m_dot_air, while
# main.py:1074-1082 builds primary and secondary from
# m_dot_air_kiln. At the committed point that is 13.9204 kg/s,
# not 34.8011. physics/steady_state_mass.py:208 carried the
# same stale claim.
#
# The inversion below divides by state.m_dot_g, which is
# m_dot_air_kiln + m_dot_fuel_kiln, and that is DELIBERATE --
# see the note on the function.
# ======================================================
def resolve_gas_inlet(burning, state):

    H_secondary = getattr(
        state,
        "Hgas_cooler_secondary",
        0.0,
    )

    H_primary = (
        state.m_dot_primary_air
        * float(
            h_gas(
                burning.T_amb,
                burning.T_ref,
            )
        )
    )

    state.Hgas_burning_in = H_primary + H_secondary

    state.Tg_burning_in = gas_inlet_temperature_from_enthalpy(
        burning,
        state.Hgas_burning_in,
        state,
    )

    return state.Tg_burning_in


def gas_inlet_temperature_from_enthalpy(burning, H, state):

    # state.m_dot_g is m_dot_g_burning = m_dot_air_kiln +
    # m_dot_fuel_kiln (main.py:866-869, :1148). It looks like the
    # calciner divisor bug fixed in 5414b44 -- H carries only the
    # two AIR streams, yet the divisor also carries the fuel --
    # and it is NOT. Dividing by primary + secondary alone would
    # be a real defect:
    #
    #   heat_transfer.py:798-804 builds the zone's inlet flux as
    #   Hg_in = m_dot_g_in * h_gas(Tg_in, T_ref), with exactly
    #   this m_dot_g_in, and heat_transfer.py:201-209 confirms it
    #   is the flow crossing the inlet FACE -- the calcination CO2
    #   is added per cell as a suffix sum INSIDE the zone, not
    #   here. So this inversion and that flux are a closed round
    #   trip: Hg_in comes back out as exactly Hgas_burning_in.
    #   MEASURED: dividing by 13.9204 instead of 14.9204 raises
    #   Tg_burning_in 540.81 -> 557.94 K and FABRICATES 291 328 W
    #   at the kiln gas inlet, against a 1.0 W global tolerance.
    #
    # It is also right as physics, not merely as bookkeeping. The
    # burner stream really is 13.92 kg/s of hot air mixed with
    # 1.0 kg/s of pulverised fuel entering at ambient; carrying
    # the fuel's mass at the air's enthalpy is the statement that
    # the fuel arrives at T_ref, which it does.
    #
    # What this value is NOT is secondary air. It is the burner
    # mixture and it is always colder. BOUNDS["secondary_air"] is
    # checked against state.Tg_secondary_air instead -- see
    # pyroprocess/cooler/gas_phase.stream_temperatures.
    m_dot_g = state.m_dot_g

    if m_dot_g <= burning.eps:
        return burning.T_ref

    h_target = H / m_dot_g

    return T_gas_from_h(
        h_target,
        burning.T_ref,
        burning.T_ref,
        4000.0,
    )


# ======================================================
# GAS ENTHALPY TO NEXT ZONE
#
# Moved from Burning.gas_enthalpy_out()
# (pyroprocess/burning.py).
#
# This used to return Hg[0], the last CELL CENTRE. The gas
# leaves through the outlet FACE, which sits half a cell
# further downstream, so that was a systematic O(dz) bias
# in the handoff itself -- independent of how well the
# interior profile was resolved. It is the reconstructed
# outlet face value that the second-order flux in
# apply_gas_energy_balance() actually transports out of
# cell 0, so returning anything else would leak exactly
# that difference out of the zone energy balance.
#
# Hg is m_dot_g * h_gas(Tg) elementwise, i.e. affine in the
# reconstructed enthalpy, so the extrapolation may be taken
# on Hg directly.
# ======================================================
def gas_enthalpy_out(Hg):

    return outlet_face_value(Hg, reverse=True)


# ======================================================
# GAS PHASE ENERGY BALANCE ROW
#
# Moved from the per-cell loop inside Burning.thermal_step()
# (pyroprocess/burning.py). Builds the gas-side row of the
# 3N linear system for cell i in place, using the same
# arithmetic and operand order as the original code so the
# Picard solve is numerically unchanged.
#
# Gas direction: N-1 -> 0.
#
# `advection_correction` is the per-cell van Leer deferred
# correction from physics.second_order_upwind_correction,
# in enthalpy units (J/kg). It is zero by default, which
# leaves this row exactly first-order upwind as before. The
# matrix A is untouched by it on purpose: the correction is
# frozen at the Picard iterate and enters b only, so the
# implicit operator stays the diagonally dominant upwind
# M-matrix the Picard loop relies on, while the converged
# fixed point satisfies the second-order equation.
# ======================================================
def apply_gas_energy_balance(
    A,
    b,
    row,
    i,
    N,
    Tg_iter,
    T_ref,
    m_dot_g,
    V_cell,
    K_gs,
    K_gw,
    q_cell,
    radiation_gas_sink,
    Tg_in,
    advection_correction=0.0,
):

    Tg_i = i
    Ts_i = N + i
    Tw_i = 2 * N + i

    Cp_g_i = cp_gas(Tg_iter[i])

    Cg_i = m_dot_g * Cp_g_i

    h_i_iter = h_gas(
        Tg_iter[i],
        T_ref
    )

    h_linear_const_i = (
        h_i_iter
        - Cp_g_i * Tg_iter[i]
    )

    A[row, Tg_i] += (
        Cg_i
        + V_cell * K_gs
        + V_cell * K_gw
    )

    A[row, Ts_i] += (
        -V_cell * K_gs
    )

    A[row, Tw_i] += (
        -V_cell * K_gw
    )

    if i == N - 1:

        h_in = h_gas(
            Tg_in,
            T_ref
        )

        b[row] = (
            q_cell[i]
            - radiation_gas_sink
            + m_dot_g * h_in
            - m_dot_g * h_linear_const_i
            - m_dot_g * advection_correction
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
            -m_dot_g * Cp_g_up
        )

        b[row] = (
            q_cell[i]
            - radiation_gas_sink
            - m_dot_g * h_linear_const_i
            + m_dot_g * h_linear_const_up
            - m_dot_g * advection_correction
        )

    return row + 1
