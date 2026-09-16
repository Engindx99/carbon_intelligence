import numpy as np

from chemistry.base import ReactionBase


class C4AFModel(ReactionBase):

    def __init__(self):

        super().__init__()

        # ================= KINETICS =================
        self.prefactor = 1.0e3
        self.activation_energy = 2.2e5

        # ================= THERMODYNAMICS =================
        self.deltaH = 3.5e5

        # ================= STOICHIOMETRY =================
        # per kg Al2O3 reacted

        self.CaO_required = (
            (4.0 * 56.08)
            / 101.96
        )

        self.Fe2O3_required = (
            159.69
            / 101.96
        )

        self.C4AF_produced = (
            485.97
            / 101.96
        )

        # ================= TEMPERATURE =================
        self.T_start = 1373.0
        self.T_end = 1723.0


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
        # LIMITING REACTANT
        # ======================================================
        available = np.minimum.reduce([
            mat.solids.Al2O3,
            mat.solids.CaO / self.CaO_required,
            mat.solids.Fe2O3 / self.Fe2O3_required,
        ])

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
        mat.solids.Al2O3 -= reacted

        mat.solids.CaO -= (
            reacted
            * self.CaO_required
        )

        mat.solids.Fe2O3 -= (
            reacted
            * self.Fe2O3_required
        )

        mat.solids.C4AF += (
            reacted
            * self.C4AF_produced
        )

        # ======================================================
        # REACTION HEAT
        # ======================================================
        state.C4AF_Q_sink = np.sum(
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
            flow["Al2O3"],
            flow["CaO"] / self.CaO_required,
            flow["Fe2O3"] / self.Fe2O3_required,
        )

        reacted = float(
            self.reacted_mass(available, rate, tau)
        )

        flow["Al2O3"] -= reacted
        flow["CaO"] -= reacted * self.CaO_required
        flow["Fe2O3"] -= reacted * self.Fe2O3_required
        flow["C4AF"] += reacted * self.C4AF_produced

        return float(self.heat_sink(reacted))
