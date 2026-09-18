import numpy as np

from chemistry.base import ReactionBase
from chemistry.phases import copy_solid_phases
from chemistry.phases import set_cell_solid_flow
from chemistry.composition import RAW_MEAL_COMPOSITION


class CalcinationModel(ReactionBase):

    def __init__(self):
        super().__init__()

        # ======================================================
        # KINETICS
        # ======================================================

        self.prefactor = 42.5             # 1/s
        self.activation_energy = 1.5e5      # J/mol
        self.deltaH = 1.78e6                # J/kg CaCO3

        # ======================================================
        # STOICHIOMETRY
        # CaCO3 -> CaO + CO2
        # ======================================================

        self.CaO_ratio = 56.08 / 100.09
        self.CO2_ratio = 44.01 / 100.09

        # ======================================================
        # TEMPERATURE WINDOW
        # ======================================================

        self.T_start = 1073.0               # K
        self.T_end = 1300.0                 # K

        # ======================================================
        # RAW MEAL COMPOSITION
        # ======================================================

        self.CaCO3_mass_fraction = (
            RAW_MEAL_COMPOSITION["CaCO3"] / 100000.0
        )

    # ======================================================
    # STEADY-STATE FLOW FORM
    #
    # Same interface as belite/alite/c3a/c4af.react_flow(), so
    # calcination can join the burning zone's Strang march
    # instead of being a separate pass. It was absent there
    # entirely: 9.18 kg/s of CaCO3 crossed the kiln with in ==
    # out exactly and was counted as clinker, while the 16.3 MW
    # its calcination should have drawn -- half the kiln's fuel
    # -- was missing from the solid's energy balance.
    #
    # THIS ONE CHANGES THE STREAM MASS. CO2 leaves the bed, so
    # unlike the four clinkering reactions the caller cannot
    # treat the solid flow as constant across the zone; the
    # released mass is returned so the caller can build its
    # per-cell flow profile from it.
    #
    # Returns (heat_sink [W], CO2_released [kg/s]).
    # ======================================================
    def react_flow(self, flow, T, tau, rate=None):

        if rate is None:
            rate = float(self.reaction_rate(T))

        available = float(flow["CaCO3"])

        reacted = float(
            self.reacted_mass(available, rate, tau)
        )

        flow["CaCO3"] -= reacted
        flow["CaO"] += reacted * self.CaO_ratio

        # The CO2 does NOT go into flow[]: it is no longer part
        # of the solid stream. The caller books it into the gas.
        return (
            float(self.heat_sink(reacted)),
            reacted * self.CO2_ratio,
        )

    # ======================================================
    # STEADY-STATE SPATIAL REACTION
    # ======================================================

    def apply(
    self,
    state,
    dz,
    u_s,
    m_dot_CaCO3_in=None,
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
        # INLET CaCO3 MASS FLOW
        # ==================================================

        if m_dot_CaCO3_in is None:

            # ILC / Calciner:
            # CaCO3 comes from raw-meal composition.
            m_dot_CaCO3_in = (
                m_dot_s
                * self.CaCO3_mass_fraction
            )

        else:

            # Downstream zone:
            # CaCO3 comes from the previous zone.
            m_dot_CaCO3_in = max(
                float(m_dot_CaCO3_in),
                0.0,
            )

        # ==================================================
        # SPATIAL ARRAYS
        # ==================================================

        m_dot_CaCO3_in_cells = np.zeros(N)
        m_dot_CaCO3_reacted_cells = np.zeros(N)
        m_dot_CaCO3_out_cells = np.zeros(N)

        reaction_rate_cells = np.zeros(N)
        reaction_heat_cells = np.zeros(N)
        conversion_cells = np.zeros(N)

        # ==================================================
        # INITIAL CONDITION
        #
        # Solid flows from cell 0 -> cell N-1
        # ==================================================

        m_dot_CaCO3_in_cells[0] = (
            m_dot_CaCO3_in
        )

        # ==================================================
        # SPACE MARCHING
        #
        # u_s * dm/dz = -k(T) * m
        #
        # dm/dz = -(k/u_s) * m
        #
        # Exact cell integration:
        #
        # m_out = m_in * exp[-k*dz/u_s]
        # ==================================================

        for i in range(N):

            m_in = max(
                float(m_dot_CaCO3_in_cells[i]),
                0.0,
            )

            T_i = max(
                float(T[i]),
                1.0,
            )

            # --------------------------------------------------
            # LOCAL KINETIC RATE
            # --------------------------------------------------

            k_i = float(
                self.reaction_rate(T_i)
            )

            reaction_rate_cells[i] = k_i

            # --------------------------------------------------
            # SPATIAL REACTION EXPONENT
            # --------------------------------------------------

            spatial_exponent = (
                k_i
                * dz
                / u_s
            )

            # --------------------------------------------------
            # OUTLET CaCO3 FLOW
            # --------------------------------------------------

            m_out = (
                m_in
                * np.exp(-spatial_exponent)
            )

            m_out = np.clip(
                m_out,
                0.0,
                m_in,
            )

            # --------------------------------------------------
            # REACTED CaCO3 FLOW
            # --------------------------------------------------

            m_reacted = (
                m_in
                - m_out
            )

            # --------------------------------------------------
            # LOCAL CONVERSION
            # --------------------------------------------------

            if m_in > 1.0e-12:
                X_i = (
                    m_reacted
                    / m_in
                )
            else:
                X_i = 0.0

            X_i = np.clip(
                X_i,
                0.0,
                1.0,
            )

            # --------------------------------------------------
            # STORE CELL RESULTS
            # --------------------------------------------------

            m_dot_CaCO3_reacted_cells[i] = (
                m_reacted
            )

            m_dot_CaCO3_out_cells[i] = (
                m_out
            )

            conversion_cells[i] = X_i

            reaction_heat_cells[i] = (
                m_reacted
                * self.deltaH
            )

            # --------------------------------------------------
            # NEXT CELL
            # --------------------------------------------------

            if i + 1 < N:

                m_dot_CaCO3_in_cells[i + 1] = (
                    m_out
                )

        # ==================================================
        # TOTAL REACTION
        # ==================================================

        m_dot_CaCO3_reacted = np.sum(
            m_dot_CaCO3_reacted_cells
        )

        m_dot_CaCO3_out = (
            m_dot_CaCO3_in
            - m_dot_CaCO3_reacted
        )

        m_dot_CaCO3_out = max(
            float(m_dot_CaCO3_out),
            0.0,
        )

        # ==================================================
        # PRODUCTS
        # ==================================================

        m_dot_CaO_generated = (
            m_dot_CaCO3_reacted
            * self.CaO_ratio
        )

        m_dot_CO2_generated = (
            m_dot_CaCO3_reacted
            * self.CO2_ratio
        )
        
        # ==================================================
        # SOLID PHASE STATE UPDATE
        # CaCO3 -> CaO
        # ==================================================

        calciner_solids = state.materials["calciner"].solids

        # ==================================================
        # PHASE INVENTORY DIAGNOSTIC
        # ==================================================

        print("\n========== CALCINER PHASE INVENTORY ==========")
        print(
            "CaCO3_before =",
            np.sum(calciner_solids.CaCO3),
        )
        print(
            "CaO_before   =",
            np.sum(calciner_solids.CaO),
        )
        print(
            "CaCO3_in_flow =",
            m_dot_CaCO3_in,
        )
        print(
            "CaCO3_reacted_flow =",
            m_dot_CaCO3_reacted,
        )
        
        # ==================================================
        # OVERALL CONVERSION
        # ==================================================

        X_total = (
            m_dot_CaCO3_reacted
            / max(
                m_dot_CaCO3_in,
                1.0e-12,
            )
        )

        X_total = np.clip(
            X_total,
            0.0,
            1.0,
        )

        CaCO3_before = (
            calciner_solids.CaCO3.copy()
        )

        CaO_before = (
            calciner_solids.CaO.copy()
        )

        print("\n========== CALCINER PHASE INVENTORY ==========")
        print(
            "CaCO3_before =",
            np.sum(CaCO3_before),
        )
        print(
            "CaO_before   =",
            np.sum(CaO_before),
        )
        print(
            "CaCO3_in_flow =",
            m_dot_CaCO3_in,
        )
        print(
            "CaCO3_reacted_flow =",
            m_dot_CaCO3_reacted,
        )
        print(
            "X_total =",
            X_total,
        )

        # --------------------------------------------------
        # Cell-wise conversion from spatial kinetics
        # --------------------------------------------------

        CaCO3_reacted_fraction = (
            conversion_cells.copy()
        )

        CaCO3_reacted_inventory = (
            CaCO3_before
            * CaCO3_reacted_fraction
        )

        CaCO3_reacted_inventory = np.minimum(
            CaCO3_reacted_inventory,
            CaCO3_before,
        )

        # --------------------------------------------------
        # CaCO3 consumption
        # --------------------------------------------------

        CaCO3_after = (
            CaCO3_before
            - CaCO3_reacted_inventory
        )

        # --------------------------------------------------
        # CaO generation
        # --------------------------------------------------

        CaO_generated_inventory = (
            CaCO3_reacted_inventory
            * self.CaO_ratio
        )

        CaO_after = (
            CaO_before
            + CaO_generated_inventory
        )

        # --------------------------------------------------
        # COMMIT PHASE INVENTORY
        # --------------------------------------------------

        if commit_phases:

            calciner_solids.CaCO3[:] = (
                CaCO3_after
            )

            calciner_solids.CaO[:] = (
                CaO_after
            )

            # ==============================================
            # CO2 GENERATION (GAS PHASE)
            #
            # Zone-local inventory only: this array holds the
            # CO2 generated by this zone's own reaction. It is
            # not transferred to/from neighboring zones.
            # ==============================================

            calciner_gases = state.materials["calciner"].gases

            calciner_gases.CO2[:] = (
                CaCO3_reacted_inventory
                * self.CO2_ratio
            )

        # ==================================================
        # TOTAL CALCINATION HEAT
        # ==================================================

        Q_calcination = np.sum(
            reaction_heat_cells
        )

        # ==================================================
        # OVERALL CONVERSION
        # ==================================================

        X_total = (
            m_dot_CaCO3_reacted
            / max(
                m_dot_CaCO3_in,
                1.0e-12,
            )
        )

        X_total = np.clip(
            X_total,
            0.0,
            1.0,
        )
        
        # ==================================================
        # SOLID PHASE BALANCE DIAGNOSTIC
        # ==================================================

        CaCO3_reacted_from_state = (
            np.sum(CaCO3_before)
            - np.sum(CaCO3_after)
        )

        CaO_generated_from_state = (
            np.sum(CaO_after)
            - np.sum(CaO_before)
        )

        state.CaCO3_material_reacted = float(
            CaCO3_reacted_from_state
        )

        state.CaO_material_generated = float(
            CaO_generated_from_state
        )

        state.CaCO3_material_balance_error = float(
            CaCO3_reacted_from_state
            - np.sum(CaCO3_reacted_inventory)
        )

        state.CaO_stoichiometric_error = float(
            CaO_generated_from_state
            - CaCO3_reacted_from_state * self.CaO_ratio
        )
        
        
        # ==================================================
        # SOLID PHASE HANDOFF
        # Calciner -> Transition
        # ==================================================

        if commit_phases:

            copy_solid_phases(
                state.materials["calciner"].solids,
                state.materials["transition"].solids,
            )


        # ==================================================
        # STATE OUTPUTS
        # ==================================================

        state.Calcination_Q_sink = float(
            Q_calcination
        )

        state.Calciner_Q_sink = float(
            Q_calcination
        )

        state.X_CaCO3_calciner = float(
            X_total
        )

        state.X_calcination = float(
            X_total
        )

        # ==================================================
        # MASS FLOWS
        # ==================================================

        state.m_dot_CaCO3_in_calciner = float(
            m_dot_CaCO3_in
        )

        state.m_dot_CaCO3_reacted_calciner = float(
            m_dot_CaCO3_reacted
        )

        state.m_dot_CaCO3_out_calciner = float(
            m_dot_CaCO3_out
        )

        state.m_dot_CaO_generated_calciner = float(
            m_dot_CaO_generated
        )

        state.m_dot_CO2_generated_calciner = float(
            m_dot_CO2_generated
        )

        # ==================================================
        # CELL RESULTS
        # ==================================================

        state.X_CaCO3_cells = (
            conversion_cells.copy()
        )

        state.reaction_rate_CaCO3_cells = (
            reaction_rate_cells.copy()
        )

        state.m_dot_CaCO3_in_cells = (
            m_dot_CaCO3_in_cells.copy()
        )

        state.m_dot_CaCO3_reacted_cells = (
            m_dot_CaCO3_reacted_cells.copy()
        )

        state.m_dot_CaCO3_out_cells = (
            m_dot_CaCO3_out_cells.copy()
        )

        state.Calcination_Q_cells = (
            reaction_heat_cells.copy()
        )

        # ==================================================
        # STEADY-STATE MASS BALANCE
        # ==================================================

        state.CaCO3_steady_state_balance = float(
            m_dot_CaCO3_in
            - m_dot_CaCO3_reacted
            - m_dot_CaCO3_out
        )

        # ==================================================
        # NUMERICAL CHECKS
        # ==================================================

        if not np.all(
            np.isfinite(
                m_dot_CaCO3_out_cells
            )
        ):
            raise FloatingPointError(
                "Non-finite CaCO3 spatial solution."
            )

        if not np.all(
            np.isfinite(
                reaction_heat_cells
            )
        ):
            raise FloatingPointError(
                "Non-finite calcination heat distribution."
            )

        if not np.isfinite(Q_calcination):
            raise FloatingPointError(
                "Non-finite total calcination heat."
            )

        return state

    # ======================================================
    # SOLID FLOW PROFILE (STEADY-STATE)
    #
    # Species mass flows [kg/s] leaving each cell of a zone
    # whose CaCO3 flow has already been marched by the
    # kinetics above (m_dot_CaCO3_out_cells). Every kg/s of
    # CaCO3 that has reacted up to and including cell i is
    # converted CUMULATIVELY -- CaO gains CaO_ratio of it and
    # CO2_ratio leaves the solid -- so the profile is the
    # flow-consistent counterpart of the kinetic march and,
    # unlike the per-cell inventory update in apply(), does
    # not depend on how finely the zone is divided.
    #
    # All other species pass through unchanged. The solid
    # flow sum therefore drops by exactly the CO2 released,
    # matching physics/steady_state_mass.py.
    #
    # inlet_flow : dict {phase: kg/s} entering cell 0
    # solids     : SolidPhases of per-cell outflows, filled
    #              in place
    # gases      : GasPhases, CO2 generated per cell [kg/s]
    # ======================================================
    def solid_flow_profile(
        self,
        inlet_flow,
        m_dot_CaCO3_out_cells,
        solids,
        gases,
    ):

        m_dot_CaCO3_out_cells = np.asarray(
            m_dot_CaCO3_out_cells,
            dtype=float,
        )

        CaCO3_in = inlet_flow["CaCO3"]

        CaCO3_upstream = CaCO3_in

        for i, CaCO3_out in enumerate(m_dot_CaCO3_out_cells):

            # The kinetic march starts from the same inlet
            # flow, so this can differ from CaCO3_in only by
            # rounding; never let it create CaCO3.
            CaCO3_out = min(float(CaCO3_out), CaCO3_in)

            reacted_cumulative = CaCO3_in - CaCO3_out

            cell_flow = dict(inlet_flow)

            cell_flow["CaCO3"] = CaCO3_out

            cell_flow["CaO"] = (
                inlet_flow["CaO"]
                + reacted_cumulative * self.CaO_ratio
            )

            set_cell_solid_flow(
                solids,
                i,
                cell_flow,
            )

            gases.CO2[i] = (
                max(CaCO3_upstream - CaCO3_out, 0.0)
                * self.CO2_ratio
            )

            CaCO3_upstream = CaCO3_out
