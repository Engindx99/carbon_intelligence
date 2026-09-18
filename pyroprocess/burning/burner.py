from physics.physics import gas_mass_balance
from physics.physics import gas_axial_velocity


# ======================================================
# BURNER GAS FLOW
#
# Moved from Burning.apply() (pyroprocess/burning.py).
# Resolves the combustion gas mass flow and axial velocity
# from the fuel/air (O2) inputs. Logic is unchanged; `self`
# was renamed to `burning` since this is now a free
# function taking the owning Burning instance explicitly.
# ======================================================
def resolve_gas_flow(burning, state, inputs):

    fuel_rate_total = inputs.get("Fuel_rate_total", 0.0)
    O2 = inputs.get("O2", 3.5)

    # The stoichiometric solve is a PLANT-level one: the dry O2
    # target is measured at the stack, which both firings share.
    # The kiln burner then carries its own fuel plus the same
    # share of the air, so its excess-air level matches the
    # plant's. Sizing the kiln on the total fuel, as this did,
    # gave the kiln every kg of the plant's combustion air.
    kiln_fraction = burning.kiln_fuel_fraction

    m_dot_air_total = (
        gas_mass_balance(
            fuel_rate_total=fuel_rate_total,
            O2=O2,
            eps=burning.eps,
        )
        - fuel_rate_total
    )

    m_dot_g = kiln_fraction * (
        m_dot_air_total
        + fuel_rate_total
    )

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
