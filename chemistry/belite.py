import numpy as np

from chemistry.base import ReactionBase


class BeliteModel(ReactionBase):

    def __init__(self):

        super().__init__()

        # ================= KINETICS =================
        self.prefactor = 1.0e3
        self.activation_energy = 2.0e5

        # ================= THERMODYNAMICS =================
        self.deltaH = 5.0e5

        # ================= STOICHIOMETRY =================

        self.CaO_required = 112.16 / 60.08

        self.C2S_produced = 172.24 / 60.08

        # ================= TEMPERATURE =================
        self.T_start = 1123.0
        self.T_end = 1473.0


    # ======================================================
    # APPLY (HELD-UP INVENTORY FORM)
    #
    # Advances state.materials["burning"] by one state.dt.
    # Its reacted mass is kg per time step, so its heat is J
    # per step rather than W, and it scales with dt; it is no
    # longer called by ChemistryModel.apply_burning(), which
    # runs the steady-state flow form react_flow() below.
    # Kept unchanged for the inventory interface.
    # ======================================================
    def apply(self, state):

        # ======================================================
        # MATERIAL INVENTORY (BURNING)
        # ======================================================
        mat = state.materials["burning"]

        # ======================================================
        # REACTION RATE
        # ======================================================
        rate = self.reaction_rate(
            state.Ts_burning
        )

        # ======================================================
        # LIMITING REACTANT (SiO2 BASIS)
        # ======================================================
        available = np.minimum(
            mat.solids.SiO2,
            mat.solids.CaO / self.CaO_required,
        )

        # ======================================================
        # REACTED MASS
        # ======================================================
        reacted = self.reacted_mass(
            available,
            rate,
            state.dt,
        )

        # ======================================================
        # UPDATE SOLID PHASES
        # ======================================================
        mat.solids.SiO2 -= reacted

        mat.solids.CaO -= (
            reacted
            * self.CaO_required
        )

        mat.solids.C2S += (
            reacted
            * self.C2S_produced
        )

        # ======================================================
        # REACTION HEAT
        # ======================================================
        state.Belite_Q_sink = np.sum(
            self.heat_sink(
                reacted,
            )
        )

        return state


    # ======================================================
    # REACT FLOW (STEADY-STATE, ONE CELL)
    #
    # Species flows `flow` [kg/s] pass through a cell at solid
    # temperature T [K] for a residence time tau [s]. The same
    # first-order kinetics as apply() are integrated exactly
    # over that exposure time,
    #
    #   reacted = available * (1 - exp(-k(T) * tau))   [kg/s]
    #
    # so the heat returned is kg/s * J/kg = W. `flow` is
    # updated in place; stoichiometry is identical to apply().
    #
    # `rate` [1/s] may be passed in when the caller already
    # evaluated reaction_rate(T) for this cell, since it is
    # constant over the sub-steps of one cell.
    # ======================================================
    def react_flow(self, flow, T, tau, rate=None):

        if rate is None:
            rate = float(self.reaction_rate(T))

        available = min(
            flow["SiO2"],
            flow["CaO"] / self.CaO_required,
        )

        reacted = float(
            self.reacted_mass(available, rate, tau)
        )

        flow["SiO2"] -= reacted
        flow["CaO"] -= reacted * self.CaO_required
        flow["C2S"] += reacted * self.C2S_produced

        return float(self.heat_sink(reacted))
