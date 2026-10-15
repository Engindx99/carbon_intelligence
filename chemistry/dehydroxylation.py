import math

import numpy as np

from chemistry.base import ReactionBase
from chemistry.phases import get_cell_solid_flow
from chemistry.phases import set_cell_solid_flow
from chemistry.composition import RAW_MEAL_COMPOSITION


class DehydroxylationModel(ReactionBase):

    def __init__(self):

        super().__init__()

        # ================= KINETICS =================
        #
        # SOURCE: Cheng, Jiu, Li, Materials 14 (2021) 1493,
        # doi:10.3390/ma14061493, Table 5 (TG-FTIR-MS on the
        # released water itself): EA = 182.71 kJ/mol,
        # log10 A = 9.44588 1/s, mechanism A2/3, i.e.
        # g(alpha) = [-ln(1 - alpha)]^(3/2) = k t.
        #
        # The twin integrates every reaction as first order
        # (reacted_mass: m (1 - exp(-k tau))). A2/3 reaches 90 %
        # at k t = 2.3026^1.5 = 3.4945, first order at 2.3026, so
        # the first-order rate with the SAME t90 is k * 0.6589:
        # that factor is folded into the prefactor below. It is
        # exact at 90 % and within a few per cent of the A2/3
        # extent above 50 %.
        #
        # WHAT WAS WRONG. The previous pair (1e3 1/s, 120 kJ/mol,
        # behind a 723-973 K window) had no source and gave
        # k = 2e-3 1/s at 1100 K: 0.6 % of the clay water left in
        # a 3 s calciner, and 1.83 of 1.87 kg/s of it reached the
        # CLINKER. Against what clay does:
        #
        #   T [K]   k [1/s]   t90
        #    800    0.0022    17 min
        #    900    0.046     50 s
        #   1000    0.52      4.4 s     (preheater bottom stage)
        #   1073    2.4       0.97 s    (flash calcination, 800 C)
        #   1173    13        0.17 s
        #
        # so the water leaves in the preheater's lower stages and
        # the calciner -- not in the kiln.
        self.prefactor = 10.0 ** 9.44588 / math.sqrt(math.log(10.0))
        self.activation_energy = 1.8271e5

        # ================= THERMODYNAMICS =================
        #
        # J per kg of WATER released, to vapour at 298.15 K: the
        # twin books the clay's oxides as separate species
        # (composition.py), so the reaction is
        #
        #   Al2Si2O5(OH)4 -> Al2O3 + 2 SiO2 + 2 H2O(g)
        #
        # with the standard enthalpies of formation of Robie and
        # Hemingway (USGS Bull. 2131, 1995): kaolinite -4119.6,
        # corundum -1675.7, quartz -910.7, H2O(g) -241.8 kJ/mol,
        # dH = +138.5 kJ/mol = 3.84 MJ per kg water. Moore's
        # clinker thermochemistry gives the same reaction at
        # +139.3 kJ/mol (cementkilns.co.uk/ckr_therm.html).
        #
        # Was 1.10e6, without a source. The metakaolin route
        # (+425 kJ/mol) would be the heat to an AMORPHOUS
        # intermediate; the twin's products are the oxides.
        self.deltaH = 3.84e6

        # kg H2O released per kg of the reacting species.
        #
        # This was 0.139, which is 2 M_H2O / M_kaolinite
        # (36.03 / 258.16): the water yield per kg of KAOLINITE.
        # The species this model actually consumes is
        # `Bound_H2O`, and chemistry/composition.py defines the
        # raw meal on an OXIDE basis -- SiO2 and Al2O3 are
        # already separate entries carrying the clay's oxides,
        # so `Bound_H2O` is the combined water itself, not the
        # hydroxyl-bearing mineral.
        #
        # Applying the kaolinite-basis ratio to a water-basis
        # species destroyed 86.1 % of the combined water: the
        # solid lost the full 0.5555 kg/s of Bound_H2O while
        # only 0.0772 kg/s reached the gas, so 0.4783 kg/s
        # (1.7 % of the feed) left the plant accounted nowhere.
        # That was the entire disagreement between the scalar
        # mass chain and the per-cell species network; with 1.0
        # the two reconcile to machine precision.
        #
        # Water released per kg of water is 1.0 by definition.
        # The reaction enthalpy is unaffected: the heat term is
        # m_reacted * deltaH on the Bound_H2O mass, which this
        # ratio never enters.
        self.product_ratio = 1.0

        # ================= TEMPERATURE =================
        #
        # NOT USED by the rate any more (reaction_rate below is
        # plain Arrhenius): the 723-973 K window was a stand-in
        # for kinetics that were too slow to switch themselves
        # off. Kept only because ReactionBase.validate_parameters
        # requires a consistent pair.
        self.T_start = 723.0
        self.T_end = 973.0


    # ======================================================
    # RATE [1/s], PLAIN ARRHENIUS
    #
    # Overrides ReactionBase.reaction_rate, which gates the
    # Arrhenius factor with temperature_window. The sourced
    # kinetics need no gate: at the preheater's top stage
    # (575 K) k is 5e-8 1/s.
    # ======================================================
    def reaction_rate(self, T):

        self.validate_parameters()

        if isinstance(T, float):
            return self.prefactor * math.exp(
                -self.activation_energy / (self.R * max(T, 1.0))
            )

        T_safe = np.maximum(np.asarray(T, dtype=float), 1.0)

        return self.prefactor * np.exp(
            -self.activation_energy / (self.R * T_safe)
        )

    # dk/dT of the rate above [1/(s K)].
    def reaction_rate_derivative(self, T):

        self.validate_parameters()

        if isinstance(T, float):
            if T <= 1.0:
                return 0.0
            return (
                self.reaction_rate(T)
                * self.activation_energy
                / (self.R * T * T)
            )

        T = np.asarray(T, dtype=float)
        T_safe = np.maximum(T, 1.0)

        return np.where(
            T > 1.0,
            self.reaction_rate(T_safe)
            * self.activation_energy
            / (self.R * T_safe * T_safe),
            0.0,
        )

    # Arrhenius alone never reaches an exact zero, so there is
    # no chord anchor: reaction_heat_slope falls to the tangent.
    def rate_vanishing_temperature(self):

        return -math.inf


    # ======================================================
    # STEADY-STATE FLOW FORM
    #
    # Same interface as DryingModel.react_flow, so the
    # preheater can march clay water out stage by stage
    # (ChemistryModel.apply_preheater). Reduces
    # flow["Bound_H2O"] in place and returns
    # (heat_sink [W], H2O released to the gas [kg/s]).
    # ======================================================
    def react_flow(self, flow, T, tau, rate=None):

        if rate is None:
            rate = float(self.reaction_rate(T))

        reacted = float(
            self.reacted_mass(float(flow["Bound_H2O"]), rate, tau)
        )

        flow["Bound_H2O"] -= reacted

        return (
            float(self.heat_sink(reacted)),
            reacted * self.product_ratio,
        )


    # ======================================================
    # APPLY (HELD-UP INVENTORY FORM)
    #
    # Advances state.materials["calciner"] by one state.dt.
    # The bound water it removes is never replenished, so over
    # a steady-state solve it drains the calciner inventory
    # and its heat (J per step, read as W) decays towards zero,
    # the same issue drying.apply() had before d9272c7. Not
    # called by ChemistryModel.apply_calciner(), which runs the
    # steady-state spatial form apply_spatial() below. Kept
    # unchanged for the inventory interface.
    # ======================================================
    def apply(self, state):

        # ======================================================
        # MATERIAL INVENTORY (CALCINER)
        # ======================================================
        mat = state.materials["calciner"]

        # ======================================================
        # REACTION RATE
        # ======================================================
        rate = self.reaction_rate(
            state.Ts_calciner
        )

        # ======================================================
        # REACTED MASS
        # ======================================================
        reacted = self.reacted_mass(
            mat.solids.Bound_H2O,
            rate,
            state.dt,
        )

        # ======================================================
        # UPDATE SOLID PHASES
        # ======================================================
        mat.solids.Bound_H2O -= reacted

        # ======================================================
        # UPDATE GAS PHASES
        # ======================================================
        mat.gases.H2O += (
            reacted
            * self.product_ratio
        )

        # ======================================================
        # REACTION HEAT
        # ======================================================
        state.Dehydroxylation_Q_sink = np.sum(
            self.heat_sink(
                reacted
            )
        )

        return state


    # ======================================================
    # STEADY-STATE SPATIAL REACTION
    #
    # Same construction as CalcinationModel.apply()
    # (chemistry/calcination.py): the calciner's Bound_H2O
    # mass flow is marched cell by cell over state.Ts_calciner,
    # each cell reacting for its residence time tau = dz/u_s,
    #
    #   m_out = m_in * exp[-k(T) * dz / u_s]
    #
    # so the released water and its heat sink are kg/s and W
    # respectively, independent of state.dt and converging
    # with the mesh instead of scaling as 1/N.
    #
    # m_dot_BoundH2O_in [kg/s]: Bound_H2O entering the calciner.
    # When None it falls back to m_dot_s_calciner times the
    # raw-meal Bound_H2O fraction, matching
    # CalcinationModel.apply()'s m_dot_CaCO3_in fallback.
    # ======================================================
    def apply_spatial(
        self,
        state,
        dz,
        u_s,
        m_dot_BoundH2O_in=None,
        commit_phases=True,
    ):

        # ==================================================
        # INPUTS
        # ==================================================

        T = np.asarray(
            state.Ts_calciner,
            dtype=float,
        )

        if T.ndim != 1:
            raise ValueError(
                "Ts_calciner must be a 1D array."
            )

        N = len(T)

        if N == 0:
            raise ValueError(
                "Calciner reaction requires at least one cell."
            )

        dz = float(dz)

        if not np.isfinite(dz) or dz <= 0.0:
            raise ValueError(
                "Calciner spatial step dz must be > 0."
            )

        u_s = float(u_s)

        if not np.isfinite(u_s) or u_s <= 0.0:
            raise ValueError(
                "Calciner solid velocity u_s must be > 0."
            )

        m_dot_s = max(
            float(state.m_dot_s_calciner),
            0.0,
        )

        # ==================================================
        # INLET Bound_H2O MASS FLOW
        # ==================================================

        if m_dot_BoundH2O_in is None:

            m_dot_BoundH2O_in = (
                m_dot_s
                * RAW_MEAL_COMPOSITION["Bound_H2O"]
                / sum(RAW_MEAL_COMPOSITION.values())
            )

        else:

            m_dot_BoundH2O_in = max(
                float(m_dot_BoundH2O_in),
                0.0,
            )

        # ==================================================
        # SPATIAL ARRAYS
        # ==================================================

        m_dot_in_cells = np.zeros(N)
        m_dot_reacted_cells = np.zeros(N)
        m_dot_out_cells = np.zeros(N)

        conversion_cells = np.zeros(N)
        reaction_heat_cells = np.zeros(N)

        # dQ/dTs per cell, for the source-term linearisation in
        # physics.variable_flow_rows.apply_solid_energy_balance.
        # Built in the same march as the heat itself so the two
        # cannot drift apart.
        reaction_heat_slope_cells = np.zeros(N)

        # ==================================================
        # INITIAL CONDITION
        #
        # Solid flows from cell 0 -> cell N-1
        # ==================================================

        m_dot_in_cells[0] = (
            m_dot_BoundH2O_in
        )

        # ==================================================
        # SPACE MARCHING
        #
        # u_s * dm/dz = -k(T) * m
        #
        # Exact cell integration:
        #
        # m_out = m_in * exp[-k*dz/u_s]
        # ==================================================

        for i in range(N):

            m_in = max(
                float(m_dot_in_cells[i]),
                0.0,
            )

            T_i = max(
                float(T[i]),
                1.0,
            )

            k_i = float(
                self.reaction_rate(T_i)
            )

            spatial_exponent = (
                k_i
                * dz
                / u_s
            )

            m_out = (
                m_in
                * np.exp(-spatial_exponent)
            )

            m_out = np.clip(
                m_out,
                0.0,
                m_in,
            )

            m_reacted = (
                m_in
                - m_out
            )

            if m_in > 1.0e-12:
                X_i = m_reacted / m_in
            else:
                X_i = 0.0

            m_dot_reacted_cells[i] = m_reacted

            m_dot_out_cells[i] = m_out

            conversion_cells[i] = np.clip(X_i, 0.0, 1.0)

            reaction_heat_cells[i] = (
                m_reacted
                * self.deltaH
            )

            reaction_heat_slope_cells[i] = (
                self.reaction_heat_slope(
                    m_in,
                    T_i,
                    float(dz / u_s),
                )
            )

            if i + 1 < N:

                m_dot_in_cells[i + 1] = m_out

        # ==================================================
        # TOTAL REACTION
        # ==================================================

        m_dot_reacted = np.sum(
            m_dot_reacted_cells
        )

        m_dot_out = max(
            float(m_dot_BoundH2O_in - m_dot_reacted),
            0.0,
        )

        m_dot_H2O_generated = (
            m_dot_reacted
            * self.product_ratio
        )

        # ==================================================
        # SOLID/GAS PHASE STATE UPDATE
        # Bound_H2O -> H2O (gas)
        # ==================================================

        calciner_solids = state.materials["calciner"].solids

        Bound_H2O_before = calciner_solids.Bound_H2O.copy()

        Bound_H2O_reacted_inventory = np.minimum(
            Bound_H2O_before * conversion_cells,
            Bound_H2O_before,
        )

        Bound_H2O_after = (
            Bound_H2O_before
            - Bound_H2O_reacted_inventory
        )

        if commit_phases:

            calciner_solids.Bound_H2O[:] = (
                Bound_H2O_after
            )

            calciner_gases = state.materials["calciner"].gases

            # Assigned, not accumulated, for the reason set out
            # at solid_flow_profile below: these arrays are
            # allocated once and never reset, so `+=` sums the
            # same steady-state inventory over every sweep.
            #
            # Unobservable today -- materials[...].gases is
            # written by three call sites and read by none after
            # GlobalState.__post_init__, which runs before any of
            # them -- but the other two writers already assign,
            # and leaving one `+=` behind only invites the same
            # confusion the material_flows twin caused.
            calciner_gases.H2O[:] = (
                Bound_H2O_reacted_inventory
                * self.product_ratio
            )

        # ==================================================
        # TOTAL DEHYDROXYLATION HEAT
        # ==================================================

        Q_dehydroxylation = np.sum(
            reaction_heat_cells
        )

        # ==================================================
        # STATE OUTPUTS
        # ==================================================

        state.Dehydroxylation_Q_sink = float(
            Q_dehydroxylation
        )

        state.Dehydroxylation_Q_sink_cells = (
            reaction_heat_cells.copy()
        )

        state.Dehydroxylation_Q_slope_cells = (
            reaction_heat_slope_cells.copy()
        )

        state.m_dot_BoundH2O_in_calciner = float(
            m_dot_BoundH2O_in
        )

        state.m_dot_BoundH2O_reacted_calciner = float(
            m_dot_reacted
        )

        state.m_dot_BoundH2O_out_calciner = float(
            m_dot_out
        )

        state.m_dot_H2O_generated_dehydroxylation = float(
            m_dot_H2O_generated
        )

        state.X_dehydroxylation = float(
            np.clip(
                m_dot_reacted / max(m_dot_BoundH2O_in, 1.0e-12),
                0.0,
                1.0,
            )
        )

        state.m_dot_BoundH2O_out_cells = (
            m_dot_out_cells.copy()
        )

        # Per-cell water handed to the gas, published for the same
        # reason calcination publishes m_dot_CaCO3_reacted_cells:
        # the calciner's solid stream loses this mass cell by cell,
        # so its energy balance needs to know where it leaves, not
        # just how much left in total.
        state.m_dot_BoundH2O_reacted_cells = (
            m_dot_reacted_cells.copy()
        )

        state.m_dot_H2O_generated_cells = (
            m_dot_reacted_cells
            * self.product_ratio
        )

        # ==================================================
        # NUMERICAL CHECKS
        # ==================================================

        if not np.all(np.isfinite(m_dot_out_cells)):
            raise FloatingPointError(
                "Non-finite Bound_H2O spatial solution."
            )

        if not np.all(np.isfinite(reaction_heat_cells)):
            raise FloatingPointError(
                "Non-finite dehydroxylation heat distribution."
            )

        if not np.isfinite(Q_dehydroxylation):
            raise FloatingPointError(
                "Non-finite total dehydroxylation heat."
            )

        return state


    # ======================================================
    # SOLID FLOW PROFILE (STEADY-STATE)
    #
    # Species mass flow [kg/s] of Bound_H2O leaving each cell
    # of a zone whose Bound_H2O flow has already been marched
    # by apply_spatial() (m_dot_BoundH2O_out_cells). The flow
    # already present at `solids` (written by
    # CalcinationModel.solid_flow_profile()) is read back per
    # cell and only its Bound_H2O entry is overwritten, so this
    # must run after that call.
    #
    # gases.H2O is ASSIGNED, not accumulated.
    #
    # It used to be `+=`, on the reading that released water
    # should join "the flow already held in gases.H2O (drying's
    # contribution, if any, from an upstream zone)". Nothing
    # ever put drying's water there -- the preheater assigns
    # its own array (ChemistryModel.apply_preheater) and no
    # zone writes another zone's -- and material_flows is built
    # once in GlobalState.__post_init__ and never reset, so the
    # `+=` had nothing to add to and simply summed this zone's
    # own flow over every sweep of the solve.
    #
    # MEASURED before the fix: material_flows["calciner"].
    # gases.H2O[0] rose by exactly 0.555592 kg/s per sweep,
    # without limit, reaching 37.21 kg/s after 69 sweeps -- 67x
    # the true flow, and a number that said how many sweeps the
    # solve took rather than anything physical.
    #
    # This is a reporting channel only: nothing reads a
    # non-preheater material_flows[...].gases array back into
    # the solve, so no temperature, flow or balance was ever
    # affected. The 14 balances use the correctly-assigned
    # scalar m_dot_H2O_generated_dehydroxylation and were right
    # throughout. What it did corrupt is the plotted calciner
    # H2O profile and the twin_harness regression snapshot, the
    # latter making a golden fixture depend on the sweep count.
    #
    # If a future upstream zone ever does contribute water to
    # this array, it must be composed explicitly here, not left
    # to residue from the previous sweep.
    #
    # inlet_flow : dict {phase: kg/s} entering cell 0
    # solids     : SolidPhases of per-cell outflows, updated
    #              in place for Bound_H2O only
    # gases      : GasPhases, H2O generated per cell [kg/s],
    #              written in place
    # ======================================================
    def solid_flow_profile(
        self,
        inlet_flow,
        m_dot_BoundH2O_out_cells,
        solids,
        gases,
    ):

        m_dot_BoundH2O_out_cells = np.asarray(
            m_dot_BoundH2O_out_cells,
            dtype=float,
        )

        BoundH2O_in = inlet_flow["Bound_H2O"]

        BoundH2O_upstream = BoundH2O_in

        for i, BoundH2O_out in enumerate(m_dot_BoundH2O_out_cells):

            BoundH2O_out = min(float(BoundH2O_out), BoundH2O_in)

            cell_flow = get_cell_solid_flow(
                solids,
                i,
            )

            cell_flow["Bound_H2O"] = BoundH2O_out

            set_cell_solid_flow(
                solids,
                i,
                cell_flow,
            )

            gases.H2O[i] = (
                max(BoundH2O_upstream - BoundH2O_out, 0.0)
                * self.product_ratio
            )

            BoundH2O_upstream = BoundH2O_out