from physics.physics import gas_mass_balance
from physics.physics import gas_axial_velocity
from physics.physics import FUEL_COMPOSITION
from physics.gas_thermo import air_for_wet_O2


# ======================================================
# BURNER GAS FLOW
#
# Moved from Burning.apply() (pyroprocess/burning.py).
# Resolves the combustion gas mass flow and axial velocity
# from the fuel/air (O2) inputs. Logic is unchanged; `self`
# was renamed to `burning` since this is now a free
# function taking the owning Burning instance explicitly.
# ======================================================
def kiln_air(burning, fuel_rate_total, O2):
    """(m_dot_fuel_kiln, m_dot_air_kiln, m_dot_air_total) [kg/s].

    The ONE definition of the kiln burner's fuel and air, used by
    main._update_steady_state_mass_flow (which sizes the cooler's
    secondary air from it) and by resolve_gas_flow below (which
    sizes the kiln gas). Two copies of this rule drifted apart once
    already: when the kiln air stopped being kiln_fraction of the
    plant air, this file kept the old rule and the burning zone ran
    on 31.26 kg/s of gas while the cooler delivered 26.40.

    The plant air is sized from the TOTAL fuel against the dry
    stack O2 (gas_mass_balance): the stack is shared. The kiln
    takes the air its flame needs for fuel.kiln_O2_wet [vol %,
    wet]; without that key it takes kiln_fraction of the plant
    air, the old rule.
    """

    kiln_fraction = burning.kiln_fuel_fraction

    m_dot_fuel_kiln = kiln_fraction * fuel_rate_total

    m_dot_air_total = (
        gas_mass_balance(
            fuel_rate_total=fuel_rate_total,
            O2=O2,
            eps=burning.eps,
        )
        - fuel_rate_total
    )

    if burning.kiln_O2_wet is not None:
        m_dot_air_kiln = air_for_wet_O2(
            m_dot_fuel_kiln,
            0.01 * float(burning.kiln_O2_wet),
            FUEL_COMPOSITION,
        )
    else:
        m_dot_air_kiln = kiln_fraction * m_dot_air_total

    return m_dot_fuel_kiln, m_dot_air_kiln, m_dot_air_total


def resolve_gas_flow(burning, state, inputs):

    fuel_rate_total = inputs.get("Fuel_rate_total", 0.0)
    O2 = inputs.get("O2", 3.5)

    m_dot_fuel_kiln, m_dot_air_kiln, _ = kiln_air(
        burning, fuel_rate_total, O2
    )

    m_dot_g = m_dot_air_kiln + m_dot_fuel_kiln

    state.m_dot_g = float(m_dot_g)

    rho_g = getattr(
        burning,
        "rho_g_avg",
        None,
    )

    if rho_g is None:
        rho_g = burning.rho_g

    u_g = gas_axial_velocity(
        m_dot_g=state.m_dot_g,
        rho_g=rho_g,
        A_cross=burning.A_cross,
        eps=burning.eps,
    )

    state.u_g = u_g

    return u_g
