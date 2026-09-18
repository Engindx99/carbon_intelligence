import numpy as np

from chemistry.base import ReactionBase
from chemistry.phases import get_cell_solid_flow
from chemistry.phases import set_cell_solid_flow
from chemistry.composition import RAW_MEAL_COMPOSITION


class DehydroxylationModel(ReactionBase):

    def __init__(self):

        super().__init__()

        # ================= KINETICS =================
        self.prefactor = 1.0e3
        self.activation_energy = 1.20e5

        # ================= THERMODYNAMICS =================
        self.deltaH = 1.10e6

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
        self.T_start = 723.0
        self.T_end = 973.0


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

            calciner_gases.H2O[:] += (
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
    # must run after that call. Released water joins the gas
    # flow already held in `gases.H2O` (drying's contribution,
    # if any, from an upstream zone).
    #
    # inlet_flow : dict {phase: kg/s} entering cell 0
    # solids     : SolidPhases of per-cell outflows, updated
    #              in place for Bound_H2O only
    # gases      : GasPhases, H2O generated per cell [kg/s]
    #              is added to in place
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

            gases.H2O[i] += (
                max(BoundH2O_upstream - BoundH2O_out, 0.0)
                * self.product_ratio
            )

            BoundH2O_upstream = BoundH2O_out