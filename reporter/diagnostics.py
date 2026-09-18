"""
Read-only physics diagnostics for the converged twin.

This module measures; it never changes the solution. Every function
takes an already-converged Twin and reports what the solver actually
did, so that the effect of a later physics change can be attributed
to that change rather than inferred.

It exists because the 14 mass/energy balances are arithmetic
self-consistency checks: reaction heats enter the OUT side of every
balance, so a wrong reaction enthalpy closes perfectly, and nothing
anywhere bounds a temperature. The checks below are the part that
can fail when the bookkeeping is right but the physics is not.

Nothing here is a tuning target. Bounds are physical limits
(clinker liquidus, adiabatic flame temperature), not desired values.
"""

import numpy as np

from chemistry.calcination import CalcinationModel
from physics.physics import h_gas
from physics.physics import T_gas_from_h


# Solid-path zone order. Gas travels the reverse.
SOLID_ZONE_ORDER = (
    "preheater",
    "calciner",
    "transition",
    "burning",
    "cooler",
)


# The state attribute each zone uses BOTH to build its enthalpy
# array and to invert an incoming enthalpy back to a temperature.
# A handoff is only temperature-consistent when the upstream zone's
# flow equals the downstream zone's flow -- see zone_boundary_continuity.
ZONE_SOLID_FLOW_ATTR = {
    "preheater": "m_dot_s_preheater",
    "calciner": "m_dot_s_calciner",
    "transition": "m_dot_s_transition",
    "burning": "m_dot_s",
    # The cooler inverts Hsolid_cooler_in with state.m_dot_s, the
    # same scalar burning uses (pyroprocess/cooler/cooler.py:202-206),
    # so that handoff is temperature-consistent by construction.
    "cooler": "m_dot_s",
}


# Atomic masses [g/mol], for the elemental closure.
A_Ca, A_Si, A_Al, A_Fe = 40.078, 28.085, 26.982, 55.845
A_C, A_O, A_H = 12.011, 15.999, 1.008

# Molar mass [g/mol] and atom count per formula unit for every
# solid species the model tracks. Built from the atomic masses
# above rather than hardcoded fractions so the stoichiometry is
# auditable in place.
SOLID_SPECIES = {
    #                     M                          Ca Si Al Fe
    "CaCO3": (A_Ca + A_C + 3 * A_O, 1, 0, 0, 0),
    "CaO": (A_Ca + A_O, 1, 0, 0, 0),
    "SiO2": (A_Si + 2 * A_O, 0, 1, 0, 0),
    "Al2O3": (2 * A_Al + 3 * A_O, 0, 0, 2, 0),
    "Fe2O3": (2 * A_Fe + 3 * A_O, 0, 0, 0, 2),
    "C2S": (2 * (A_Ca + A_O) + A_Si + 2 * A_O, 2, 1, 0, 0),
    "C3S": (3 * (A_Ca + A_O) + A_Si + 2 * A_O, 3, 1, 0, 0),
    "C3A": (3 * (A_Ca + A_O) + 2 * A_Al + 3 * A_O, 3, 0, 2, 0),
    "C4AF": (
        4 * (A_Ca + A_O) + 2 * A_Al + 3 * A_O + 2 * A_Fe + 3 * A_O,
        4,
        0,
        2,
        2,
    ),
    # H2O and Bound_H2O carry none of the four tracked elements.
    "H2O": (2 * A_H + A_O, 0, 0, 0, 0),
    "Bound_H2O": (2 * A_H + A_O, 0, 0, 0, 0),
}

ELEMENTS = ("Ca", "Si", "Al", "Fe")
ELEMENT_MASS = {"Ca": A_Ca, "Si": A_Si, "Al": A_Al, "Fe": A_Fe}


# ======================================================
# PHYSICAL BOUNDS
#
# These are limits, not targets. Sources:
#   - clinker is fully liquid well below 1773 K; a cement kiln
#     that reaches it is making slag, not clinker
#   - the gas cannot exceed the adiabatic flame temperature of
#     its own fuel and air (computed per run, not tabulated)
#   - a kiln shell above ~670 K destroys the refractory anchors
#   - clinker leaves a real kiln at 1600-1780 K and a real
#     grate cooler at 340-480 K
#   - secondary air off a grate cooler runs 1050-1350 K
# ======================================================
# Calcination enthalpy, read from the reaction that owns it rather
# than restated here, so D11 can never drift from the chemistry.
DH_CALCINATION = CalcinationModel().deltaH

# Petcoke LHV as pyroprocess/{burning,precalciner}/combustion.py fire it.
FUEL_LHV = 32.0e6

# Specific heat consumption of a modern ILC preheater/precalciner
# plant [J/kg clinker]. This is a BAND, not a target: it says what
# a plant of this configuration is built to achieve, and is used
# only to report how far the fixed fuel input sits from it.
SHC_BAND = (2900.0e3, 3300.0e3)

BOUNDS = {
    "Ts_any_zone_max": (None, 1773.0, "clinker liquidus"),
    "Tw_burning_max": (None, 1900.0, "refractory hot-face limit"),
    "shell_T": (350.0, 670.0, "kiln shell"),
    "clinker_kiln_outlet": (1600.0, 1780.0, "clinker discharge"),
    "clinker_cooler_outlet": (340.0, 480.0, "cooler discharge"),
    "secondary_air": (1050.0, 1350.0, "secondary air"),
}


def _zone_arrays(state, zone):
    return (
        np.asarray(getattr(state, f"Tg_{zone}"), dtype=float),
        np.asarray(getattr(state, f"Ts_{zone}"), dtype=float),
        np.asarray(getattr(state, f"Tw_{zone}"), dtype=float),
    )


def _solid_build_flow(twin, zone):
    """The mass flow a zone actually multiplies into the solid enthalpy
    it hands downstream, with the attribute it came from.

    Three patterns exist in the plant, in decreasing order of fidelity,
    and this must follow whichever one the zone genuinely solved on --
    reporting a flow the solver did not use would invent a mismatch
    that is not there, which is exactly the error this diagnostic is
    meant to catch in the model.

      1. `state.m_dot_s_<zone>_cells`: the zone carries a per-cell flow
         profile because mass leaves the solid as it goes. The enthalpy
         handed downstream crosses the OUTLET face, so the flow that
         built it is the profile's last entry, not its first.
      2. `zone.m_dot_s_out`: a single, correct outlet scalar. The
         preheater has always done this
         (pyroprocess/preheater/solid_phase.py:12-20).
      3. the inlet-side state scalar: no outlet notion at all. This is
         what makes a handoff temperature-inconsistent, and reading it
         here is the symptom, not the cause.
    """

    cells = getattr(twin.state, f"m_dot_s_{zone}_cells", None)

    if cells is not None:
        cells = np.asarray(cells, dtype=float)

        if cells.size:
            return (
                float(cells[-1]),
                f"state.m_dot_s_{zone}_cells[-1]",
            )

    z = _zone_object(twin, zone)

    m_out = getattr(z, "m_dot_s_out", None)

    if m_out is not None:
        return float(m_out), "zone.m_dot_s_out"

    attr = ZONE_SOLID_FLOW_ATTR[zone]

    return float(getattr(twin.state, attr)), f"state.{attr}"


def _zone_object(twin, zone):
    return {
        "preheater": twin.preheater,
        "calciner": twin.calciner,
        "transition": twin.transition,
        "burning": twin.burning,
        "cooler": twin.cooler,
    }[zone]


# ======================================================
# D1. ZONE BOUNDARY CONTINUITY
#
# Each zone builds its solid enthalpy array as
#   H = m_dot_s_<zone> * Cp_s * (Ts - T_ref)
# and inverts an incoming enthalpy with its own m_dot_s_<zone>.
# So a handoff preserves temperature only when the two zones
# carry the same flow. Where they differ -- and they must
# differ wherever CO2 or H2O leaves the solid -- the handoff
# conserves J/s exactly while scaling Kelvin by the flow ratio.
#
# No energy residual can see this, which is why it is checked
# here and not in validators/energy.py.
# ======================================================
def zone_boundary_continuity(twin):

    state = twin.state
    rows = []

    for upstream, downstream in zip(
        SOLID_ZONE_ORDER[:-1],
        SOLID_ZONE_ORDER[1:],
    ):

        H = getattr(state, f"Hsolid_{downstream}_in", None)

        if H is None:
            continue

        m_up, src_up = _solid_build_flow(twin, upstream)
        m_down = float(getattr(state, ZONE_SOLID_FLOW_ATTR[downstream]))

        cp_up = _zone_object(twin, upstream).Cp_s
        cp_down = _zone_object(twin, downstream).Cp_s
        T_ref = _zone_object(twin, downstream).T_ref

        T_up = T_ref + float(H) / (m_up * cp_up)
        T_down = T_ref + float(H) / (m_down * cp_down)

        rows.append(
            {
                "phase": "solid",
                "handoff": f"{upstream} -> {downstream}",
                "H_W": float(H),
                "m_dot_up": m_up,
                "m_dot_up_source": src_up,
                "m_dot_down": m_down,
                "ratio": m_up / m_down,
                "T_upstream_face": T_up,
                "T_downstream_in": T_down,
                "delta_T": T_down - T_up,
                "spurious_W": m_down * cp_down * (T_down - T_up),
            }
        )

    return rows


# ======================================================
# D2. PHYSICAL PLAUSIBILITY BOUNDS
#
# The adiabatic flame temperature is computed from this run's
# own fuel heat release, gas mass flow and gas inlet enthalpy,
# so it moves with the operating point instead of being a
# tabulated number that silently goes stale.
# ======================================================
def adiabatic_flame_temperature(twin):

    state = twin.state
    T_ref = twin.burning.T_ref

    m_dot_g = float(state.m_dot_g)
    Q = float(state.Q_burning)

    h_in = float(h_gas(state.Tg_burning_in, T_ref))

    return float(
        T_gas_from_h(
            h_in + Q / m_dot_g,
            T_ref,
            T_ref,
            4000.0,
        )
    )


def burning_enthalpy_ceiling(twin):
    """Highest gas temperature the zone's own energy input allows.

    Every joule in the zone crossed its boundary as gas enthalpy,
    solid enthalpy or fuel. Putting all of it into the gas stream
    alone gives a temperature nothing inside can exceed.
    """

    state = twin.state
    T_ref = twin.burning.T_ref

    Hg_in = float(state.m_dot_g) * float(h_gas(state.Tg_burning_in, T_ref))

    Hs_in = (
        float(state.m_dot_s)
        * twin.burning.Cp_s
        * (float(state.Ts_burning_in) - T_ref)
    )

    return float(
        T_gas_from_h(
            (Hg_in + Hs_in + float(state.Q_burning))
            / float(state.m_dot_g),
            T_ref,
            T_ref,
            4000.0,
        )
    )


def plausibility_bounds(twin):

    state = twin.state
    checks = []

    def add(name, value, lo, hi, note):
        ok = True
        if lo is not None and value < lo:
            ok = False
        if hi is not None and value > hi:
            ok = False
        checks.append(
            {
                "check": name,
                "value": float(value),
                "lo": lo,
                "hi": hi,
                "note": note,
                "ok": ok,
            }
        )

    # Solid temperature anywhere in the plant.
    for zone in SOLID_ZONE_ORDER:
        _, Ts, Tw = _zone_arrays(state, zone)
        lo, hi, note = BOUNDS["Ts_any_zone_max"]
        add(f"max Ts [{zone}]", float(np.max(Ts)), lo, hi, note)

    # Wall hot face in the kiln.
    _, _, Tw_b = _zone_arrays(state, "burning")
    lo, hi, note = BOUNDS["Tw_burning_max"]
    add("max Tw [burning]", float(np.max(Tw_b)), lo, hi, note)

    # Gas against the total enthalpy that entered the zone.
    #
    # NOT the adiabatic flame temperature: in counter-current the
    # gas enters at the burner end against the hottest solid it
    # will ever meet, picks up sensible heat from it, and only
    # then receives the fuel. So exceeding the adiabatic figure
    # computed from the INLET state is legitimate regenerative
    # pickup, not a thermodynamic violation, and asserting on it
    # would fail a correct kiln.
    #
    # What cannot be exceeded is the enthalpy that crossed the
    # boundary: gas in, solid in, fuel. That is a true ceiling,
    # if a loose one. The adiabatic figure is reported next to
    # it as a reference, because a gas peak far above it means
    # the bed is returning large heat to the gas -- the flow
    # inversion -- rather than that thermodynamics broke.
    Tg_b, _, _ = _zone_arrays(state, "burning")
    T_ad = adiabatic_flame_temperature(twin)
    add(
        "max Tg [burning] vs enthalpy ceiling",
        float(np.max(Tg_b)),
        None,
        burning_enthalpy_ceiling(twin),
        f"adiabatic-from-inlet is {T_ad:.0f} K (reference, not a bound)",
    )

    # Shell temperature, from the refractory series resistance.
    R_total = getattr(state, "Burning_R_total", None)

    if R_total is not None:
        R_conv = 1.0 / (twin.burning.h_ext * twin.burning.A_wall_cell)
        T_shell = twin.burning.T_amb + (
            np.max(Tw_b) - twin.burning.T_amb
        ) * (R_conv / R_total)
        lo, hi, note = BOUNDS["shell_T"]
        add("kiln shell T (hottest cell)", float(T_shell), lo, hi, note)

    # Stream boundary temperatures.
    lo, hi, note = BOUNDS["clinker_kiln_outlet"]
    add(
        "clinker at kiln discharge",
        _solid_outlet_face(twin, "burning"),
        lo,
        hi,
        note,
    )

    lo, hi, note = BOUNDS["clinker_cooler_outlet"]
    add(
        "clinker at cooler discharge",
        _solid_outlet_face(twin, "cooler"),
        lo,
        hi,
        note,
    )

    sec = getattr(state, "Tg_burning_in", None)

    if sec is not None:
        lo, hi, note = BOUNDS["secondary_air"]
        add("gas into kiln (sec + prim air)", float(sec), lo, hi, note)

    return checks


def _solid_outlet_face(twin, zone):
    """Outlet FACE, not the last cell centre -- the value the next
    zone actually receives."""

    _, Ts, _ = _zone_arrays(twin.state, zone)

    return float(Ts[-1] + 0.5 * (Ts[-1] - Ts[-2]))


# ======================================================
# D3. ELEMENTAL CLOSURE ON THE SOLID
#
# The 14 balances check total mass and CO2, both of which are
# built from the same scalars on either side. Nothing checks
# that Ca, Si, Al and Fe are conserved through the reaction
# network, so a stoichiometry error or an unreacted species
# counted as product passes silently.
# ======================================================
def _element_flows(solids, cell):

    out = {e: 0.0 for e in ELEMENTS}

    for name, (M, n_ca, n_si, n_al, n_fe) in SOLID_SPECIES.items():

        flow = getattr(solids, name, None)

        if flow is None:
            continue

        m = float(np.asarray(flow, dtype=float)[cell])

        for element, n in zip(ELEMENTS, (n_ca, n_si, n_al, n_fe)):

            if n:
                out[element] += m * n * ELEMENT_MASS[element] / M

    return out


def elemental_closure(twin):
    """Element flows at the raw-meal feed and at the cooler discharge."""

    state = twin.state

    # The preheater is indexed against the solid flow, so the feed
    # is its LAST cell; every other zone runs 0 -> N-1.
    feed = _element_flows(
        state.material_flows["preheater"].solids,
        -1,
    )

    product = _element_flows(
        state.material_flows["cooler"].solids,
        -1,
    )

    rows = []

    for e in ELEMENTS:

        a, b = feed[e], product[e]
        rows.append(
            {
                "element": e,
                "feed_kg_s": a,
                "product_kg_s": b,
                "residual_kg_s": b - a,
                "rel": (b - a) / a if a else float("nan"),
            }
        )

    return rows


def clinker_quality(twin):
    """What the product actually is, by species."""

    solids = twin.state.material_flows["cooler"].solids
    total = 0.0
    parts = {}

    for name in SOLID_SPECIES:

        flow = getattr(solids, name, None)

        if flow is None:
            continue

        m = float(np.asarray(flow, dtype=float)[-1])
        parts[name] = m
        total += m

    return {
        "total_kg_s": total,
        "parts": parts,
        "pct": {
            k: (100.0 * v / total if total else float("nan"))
            for k, v in parts.items()
        },
    }


# ======================================================
# D4. BURNING MECHANISM SPLIT
#
# Published by pyroprocess/burning/heat_transfer.py. This is
# the direct measurement of the convection/radiation ratio,
# which is the quantity any change to hv_gs or k_eff has to
# move. Without it the split can only be inferred.
# ======================================================
def burning_mechanism_split(state):

    def arr(name):
        v = getattr(state, name, None)
        return None if v is None else np.asarray(v, dtype=float)

    conv = {
        "gas->solid": arr("Burning_Qgs_conv_cells"),
        "gas->wall": arr("Burning_Qgw_conv_cells"),
        "solid->wall": arr("Burning_Qws_conv_cells"),
    }

    rad = {
        "gas->solid": arr("Burning_Qgs_rad_cells"),
        "gas->wall": arr("Burning_Qgw_rad_cells"),
        "solid->wall": arr("Burning_Qws_rad_cells"),
    }

    if conv["gas->solid"] is None:
        return None

    rows = []

    for pair in conv:

        c = float(np.sum(conv[pair]))
        r = float(np.sum(rad[pair]))
        tot = c + r

        rows.append(
            {
                "pair": pair,
                "convection_W": c,
                "radiation_W": r,
                "total_W": tot,
                "radiation_pct": (
                    100.0 * abs(r) / (abs(c) + abs(r))
                    if (abs(c) + abs(r))
                    else float("nan")
                ),
            }
        )

    return {
        "rows": rows,
        "fuel_W": float(np.sum(arr("Burning_q_fuel_cells"))),
        "reaction_W": float(np.sum(arr("Burning_q_reaction_cells"))),
        "wall_loss_W": float(np.sum(arr("Burning_Qloss_cells"))),
        # Net heat INTO the solid per cell: what it gains from the
        # gas minus what it loses to the wall. Qws is signed
        # solid -> wall, so it subtracts.
        "sign_flip_cell": _sign_flip_cell(
            (conv["gas->solid"] + rad["gas->solid"])
            - (conv["solid->wall"] + rad["solid->wall"])
        ),
    }


def _sign_flip_cell(q):
    """First cell at which the solid stops receiving net heat."""

    for i, v in enumerate(q):
        if v < 0.0:
            return i

    return None


# ======================================================
# D10. SOLID MASS FLOW: SCALAR CHAIN vs SPECIES NETWORK
#
# The model carries the solid mass flow twice:
#
#   1. state.m_dot_s_<zone>, a single scalar per zone, built
#      by main._update_steady_state_mass_flow by subtracting
#      generated CO2/H2O. The thermal solvers use this one.
#   2. material_flows[<zone>].solids, a per-cell species
#      vector advanced by the chemistry. The reactions use
#      this one.
#
# Nothing reconciles them, and they disagree. That matters
# because the scalar is a single number for a stream whose
# mass changes along the zone, so it can only ever equal the
# inlet or the outlet, never both -- which is the mechanism
# behind the D1 handoff mismatch.
# ======================================================
def solid_mass_flow_consistency(twin):

    state = twin.state
    rows = []

    for zone in SOLID_ZONE_ORDER:

        solids = state.material_flows[zone].solids

        per_cell = None

        for name in SOLID_SPECIES:

            flow = getattr(solids, name, None)

            if flow is None:
                continue

            v = np.asarray(flow, dtype=float)
            per_cell = v.copy() if per_cell is None else per_cell + v

        scalar = float(getattr(state, ZONE_SOLID_FLOW_ATTR[zone]))

        # The preheater is indexed against the solid flow.
        first, last = (
            (per_cell[-1], per_cell[0])
            if zone == "preheater"
            else (per_cell[0], per_cell[-1])
        )

        rows.append(
            {
                "zone": zone,
                "species_in": float(first),
                "species_out": float(last),
                "scalar": scalar,
                "scalar_minus_species_in": scalar - float(first),
                "scalar_minus_species_out": scalar - float(last),
            }
        )

    return rows


# ======================================================
# D8. NTU PER ZONE
#
# NTU = K_gs * V_total / C_min, with C from the stream the
# zone actually carries. It is the single number that says
# how hard a zone is pulling the two streams together, and it
# is what makes the transition/burning comparison legible.
#
# hv_gs and a_gs are read off each zone object, i.e. the same
# attributes the zone's own solver multiplies together -- not
# recomputed from config.
# ======================================================
def zone_ntu(twin):

    state = twin.state
    rows = []

    for zone in SOLID_ZONE_ORDER:

        z = _zone_object(twin, zone)

        hv_gs = getattr(z, "hv_gs", None)

        # Burning derives its areas per thermal_step from the bed
        # geometry and keeps no a_gs attribute, so the published
        # values are the only correct source for it. Every other
        # zone still freezes a_gs in __init__.
        if zone == "burning":
            a_gs = getattr(state, "Burning_a_gs", None)
            a_ws = getattr(state, "Burning_a_ws", None)
            a_gw = getattr(state, "Burning_a_gw", None)
        else:
            a_gs = getattr(z, "a_gs", None)
            a_ws = getattr(z, "a_ws", None)
            a_gw = getattr(z, "a_gw", None)

        if hv_gs is None or a_gs is None:
            continue

        a_gs = float(a_gs)

        V_total = float(z.V_cell) * int(z.N)
        UA = float(hv_gs) * a_gs * V_total

        m_s = float(getattr(state, ZONE_SOLID_FLOW_ATTR[zone]))
        C_s = m_s * float(z.Cp_s)

        rows.append(
            {
                "zone": zone,
                "L_m": float(z.L),
                "a_gs": a_gs,
                "hv_gs": float(hv_gs),
                "UA_kW_K": UA / 1e3,
                "C_solid_kW_K": C_s / 1e3,
                "NTU_solid": UA / C_s if C_s else float("nan"),
                "wall_area_identity": (
                    (float(a_ws) + float(a_gw)) * float(z.D) / 4.0
                    if (a_ws is not None and a_gw is not None)
                    else float("nan")
                ),
            }
        )

    return rows


# ======================================================
# D9. PICARD CONVERGENCE
# ======================================================
def picard_convergence(state):

    if not hasattr(state, "Burning_picard_error"):
        return None

    return {
        "converged": state.Burning_picard_converged,
        "error": state.Burning_picard_error,
        "tol": state.Burning_picard_tol,
        "iterations_to_tol": state.Burning_picard_iterations_to_tol,
        "max_iter": state.Burning_picard_max_iter,
    }


# ======================================================
# D11. THERMAL DEMAND vs FUEL SUPPLY
#
# Every other diagnostic here asks whether the plant is
# self-consistent. This one asks a question no balance can:
# whether the fuel rate is the right SIZE for the meal being
# fed. It is an input, fixed in the config, while a real kiln
# modulates it against burning-zone temperature and free lime
# -- so nothing in the model can push back on a wrong value,
# and a surplus has nowhere to go except temperature.
#
# The two figures are deliberately independent:
#
#   demand  - what the feed's chemistry must absorb, from the
#             raw meal composition alone. Does not look at the
#             fuel, the temperatures, or any closure.
#   supply  - the fuel's heat release.
#
# A gap between them is not an imbalance -- the balances all
# close, because the surplus leaves as sensible heat and wall
# loss. It is a sizing error, and it reads as temperature.
#
# "Potential clinker" is what the feed would yield at complete
# calcination, NOT the model's clinker stream: the latter still
# carries uncalcined CaCO3, so dividing by it would flatter the
# specific consumption by counting raw meal as product.
# ======================================================
def thermal_demand_vs_supply(twin):

    state = twin.state
    mf = twin.mass_flow

    feed = _solid_feed_species(twin)

    CaCO3_feed = float(feed.get("CaCO3", 0.0))

    M_CaCO3 = SOLID_SPECIES["CaCO3"][0]
    M_CO2 = A_C + 2 * A_O

    CO2_full = CaCO3_feed * M_CO2 / M_CaCO3

    H2O_free = float(
        getattr(state, "m_dot_H2O_evaporated_preheater", 0.0)
    )
    H2O_bound = float(feed.get("Bound_H2O", 0.0))

    meal = float(mf.m_dot_s_preheater)

    clinker_potential = meal - CO2_full - H2O_free - H2O_bound

    if clinker_potential <= 0.0:
        return None

    # Chemistry the feed REQUIRES, independent of how hot the
    # model happens to run.
    demand_full = (
        CaCO3_feed * DH_CALCINATION
        + float(getattr(state, "Dehydroxylation_Q_sink", 0.0))
        + float(getattr(state, "Drying_Q_sink", 0.0))
        + float(getattr(state, "Burning_Q_sink", 0.0))
    )

    # Chemistry the model ACTUALLY runs.
    demand_modelled = (
        float(getattr(state, "Calcination_Q_sink", 0.0))
        + float(getattr(state, "Calcination_Q_transition", 0.0))
        + float(getattr(state, "Dehydroxylation_Q_sink", 0.0))
        + float(getattr(state, "Drying_Q_sink", 0.0))
        + float(getattr(state, "Burning_Q_sink", 0.0))
    )

    supply = float(mf.m_dot_fuel) * FUEL_LHV

    shc = supply / clinker_potential

    return {
        "meal": meal,
        "clinker_potential": clinker_potential,
        "meal_to_clinker": meal / clinker_potential,
        "fuel": float(mf.m_dot_fuel),
        "supply_W": supply,
        "shc_J_per_kg": shc,
        "shc_band": SHC_BAND,
        "demand_modelled_W": demand_modelled,
        "demand_full_W": demand_full,
        "missing_sink_W": demand_full - demand_modelled,
        "fuel_at_band_mid": (
            clinker_potential
            * (SHC_BAND[0] + SHC_BAND[1])
            / 2.0
            / FUEL_LHV
        ),
    }


def _solid_feed_species(twin):
    """Raw-meal species flows as fed.

    Same source and same index as elemental_closure()'s feed side:
    the preheater is indexed against the solid flow, so the meal
    enters at its LAST cell.
    """

    solids = twin.state.material_flows["preheater"].solids

    feed = {}

    for sp in SOLID_SPECIES:
        arr = getattr(solids, sp, None)

        if arr is None:
            continue

        arr = np.asarray(arr, dtype=float)

        if arr.size:
            feed[sp] = float(arr[-1])

    return feed


# ======================================================
# REPORT
# ======================================================
def report(twin):

    out = []
    w = out.append

    w("\n================ PHYSICS DIAGNOSTICS (read-only) ================")

    # ---------- D1 ----------
    w("\n-- D1  zone boundary continuity (solid) --")
    w(
        f"           {'handoff':24s} {'m_up':>9s} {'m_down':>9s} {'ratio':>8s} "
        f"{'T_up_face':>10s} {'T_down_in':>10s} {'dT':>9s}   upstream flow from"
    )

    for r in zone_boundary_continuity(twin):
        flag = "MISMATCH" if abs(r["ratio"] - 1.0) > 1e-9 else "        "
        w(
            f"  {flag} {r['handoff']:24s} {r['m_dot_up']:9.4f} "
            f"{r['m_dot_down']:9.4f} {r['ratio']:8.5f} "
            f"{r['T_upstream_face']:10.2f} {r['T_downstream_in']:10.2f} "
            f"{r['delta_T']:+9.2f}   {r['m_dot_up_source']}"
        )

    w(
        "  A ratio != 1 scales Kelvin while conserving J/s, so no"
        " energy residual can detect it."
    )

    # ---------- D10 ----------
    w("\n-- D10  solid mass flow: scalar chain vs species network --")
    w(
        f"  {'zone':12s} {'species in':>11s} {'species out':>12s} "
        f"{'scalar':>9s} {'scalar-in':>10s} {'scalar-out':>11s}"
    )

    for r in solid_mass_flow_consistency(twin):
        w(
            f"  {r['zone']:12s} {r['species_in']:11.4f} "
            f"{r['species_out']:12.4f} {r['scalar']:9.4f} "
            f"{r['scalar_minus_species_in']:+10.4f} "
            f"{r['scalar_minus_species_out']:+11.4f}"
        )

    w(
        "  One scalar cannot equal both ends of a stream that loses"
        " mass; that is the D1 mechanism."
    )

    # ---------- D2 ----------
    w("\n-- D2  physical plausibility bounds --")

    for c in plausibility_bounds(twin):
        lo = "  -  " if c["lo"] is None else f"{c['lo']:.0f}"
        hi = "  -  " if c["hi"] is None else f"{c['hi']:.0f}"
        verdict = "ok" if c["ok"] else "VIOLATED"
        w(
            f"  [{verdict:>8s}] "
            f"{c['check']:34s} {c['value']:9.1f} K  "
            f"(bound {lo} .. {hi}, {c['note']})"
        )

    # ---------- D3 ----------
    w("\n-- D3  elemental closure, raw meal -> clinker --")
    w(f"  {'element':8s} {'feed kg/s':>11s} {'product kg/s':>13s} {'rel':>11s}")

    for r in elemental_closure(twin):
        w(
            f"  {r['element']:8s} {r['feed_kg_s']:11.5f} "
            f"{r['product_kg_s']:13.5f} {r['rel']:+11.3e}"
        )

    q = clinker_quality(twin)
    w(f"\n  product stream {q['total_kg_s']:.4f} kg/s:")

    for k, v in sorted(q["pct"].items(), key=lambda kv: -kv[1]):
        if v > 0.01:
            w(f"    {k:12s} {q['parts'][k]:8.4f} kg/s  {v:6.2f} %")

    # ---------- D4 ----------
    w("\n-- D4  burning mechanism split --")
    split = burning_mechanism_split(twin.state)

    if split is None:
        w("  (not published)")
    else:
        w(
            f"  {'pair':14s} {'convection MW':>15s} {'radiation MW':>14s} "
            f"{'radiation %':>13s}"
        )
        for r in split["rows"]:
            w(
                f"  {r['pair']:14s} {r['convection_W']/1e6:15.3f} "
                f"{r['radiation_W']/1e6:14.4f} {r['radiation_pct']:13.2f}"
            )

        w(
            f"\n  fuel {split['fuel_W']/1e6:.3f} MW | "
            f"reaction sink {split['reaction_W']/1e6:.3f} MW | "
            f"wall loss {split['wall_loss_W']/1e6:.3f} MW"
        )

        cell = split["sign_flip_cell"]
        w(
            "  net convective heat to the solid turns negative at cell "
            + (str(cell) if cell is not None else "never")
        )

    # ---------- D8 ----------
    w("\n-- D8  NTU per zone --")
    w(
        f"  {'zone':12s} {'L m':>6s} {'a_gs':>8s} {'hv_gs':>7s} "
        f"{'UA kW/K':>9s} {'NTU':>7s} {'(a_ws+a_gw)D/4':>15s}"
    )

    for r in zone_ntu(twin):
        w(
            f"  {r['zone']:12s} {r['L_m']:6.1f} {r['a_gs']:8.4f} "
            f"{r['hv_gs']:7.1f} {r['UA_kW_K']:9.1f} {r['NTU_solid']:7.2f} "
            f"{r['wall_area_identity']:15.4f}"
        )

    w("  last column must be 1.0000; anything else double-counts wall area.")

    # ---------- D9 ----------
    w("\n-- D9  burning Picard convergence (last call) --")
    p = picard_convergence(twin.state)

    if p is None:
        w("  (not published)")
    else:
        w(
            f"  converged={p['converged']}  error={p['error']:.3e}  "
            f"tol={p['tol']:.0e}  reached tol at iteration="
            f"{p['iterations_to_tol']}  of max_iter={p['max_iter']}"
        )
        w("  (the loop has no break: it always runs max_iter passes)")

    # ---------- D11 ----------
    w("\n-- D11  thermal demand vs fuel supply --")
    t = thermal_demand_vs_supply(twin)

    if t is None:
        w("  (not available)")
    else:
        w(
            f"  raw meal fed            {t['meal']:9.3f} kg/s"
        )
        w(
            f"  potential clinker       {t['clinker_potential']:9.3f} kg/s"
            f"   ({t['clinker_potential'] * 86.4:.0f} t/d,"
            f" meal/clinker {t['meal_to_clinker']:.3f})"
        )
        w(
            f"  fuel supplied           {t['fuel']:9.3f} kg/s"
            f"   -> {t['supply_W'] / 1e6:6.2f} MW"
        )

        lo, hi = t["shc_band"]
        shc = t["shc_J_per_kg"]
        verdict = "OVER-FIRED" if shc > hi else (
            "under-fired" if shc < lo else "ok"
        )

        w(
            f"  [{verdict:>10s}] specific heat consumption "
            f"{shc / 1e3:7.0f} kJ/kg clinker"
            f"   (modern ILC {lo / 1e3:.0f}-{hi / 1e3:.0f})"
        )
        w(
            f"               fuel at band midpoint would be "
            f"{t['fuel_at_band_mid']:.3f} kg/s"
            f"  ({t['fuel'] / t['fuel_at_band_mid']:.2f}x)"
        )
        w(
            f"  chemistry demand, as modelled   "
            f"{t['demand_modelled_W'] / 1e6:6.2f} MW"
        )
        w(
            f"  chemistry demand, full calcination "
            f"{t['demand_full_W'] / 1e6:6.2f} MW"
        )
        w(
            f"  MISSING SINK                    "
            f"{t['missing_sink_W'] / 1e6:6.2f} MW"
        )
        w(
            "  Fuel is a fixed config input, so nothing in the model can"
            " reject a surplus."
        )
        w(
            "  Heat the chemistry does not absorb leaves as temperature,"
            " wall loss and exhaust."
        )

    w("\n================================================================\n")

    return "\n".join(out)
