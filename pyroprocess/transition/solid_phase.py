# ======================================================
# SOLID INLET TEMPERATURE FROM ENTHALPY
#
# Moved from Transition.solid_inlet_temperature_from_enthalpy()
# (pyroprocess/transition.py). Logic is unchanged; `self`
# was renamed to `transition` since this is now a free
# function taking the owning Transition instance explicitly.
# ======================================================
def solid_inlet_temperature_from_enthalpy(transition, H, state):

    return (
        H
        / (
            state.m_dot_s_transition
            * transition.Cp_s
            + transition.eps
        )
        + transition.T_ref
    )


# ======================================================
# SOLID ENTHALPY TO NEXT ZONE
#
# Moved from Transition.solid_enthalpy_out()
# (pyroprocess/transition.py). Logic is unchanged.
# ======================================================
def solid_enthalpy_out(Hs):

    return Hs[-1]


# ======================================================
# SOLID PHASE ENERGY BALANCE ROW
#
# Moved from the per-cell loop inside Transition.thermal_step()
# (pyroprocess/transition.py). Builds the solid-side row of the
# 3N linear system for cell i in place, using the same
# arithmetic and operand order as the original code so the
# Picard solve is numerically unchanged. Takes the calcination
# heat sink for this cell as an explicit parameter instead of
# computing it inline.
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
    Q_calcination_cell,
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
            - Q_calcination_cell
        )
    else:
        Ts_up_i = N + i - 1
        A[row, Ts_up_i] += -Cs
        b[row] = (
            radiation_solid_source
            - Q_calcination_cell
        )

    return row + 1
