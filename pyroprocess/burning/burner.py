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

    m_dot_g = gas_mass_balance(
        fuel_rate_total=fuel_rate_total,
        O2=O2,
        eps=burning.eps,
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
