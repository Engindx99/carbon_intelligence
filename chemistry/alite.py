import numpy as np

from chemistry.base import ReactionBase


class AliteModel(ReactionBase):

    def __init__(self):

        super().__init__()

        # ================= KINETICS =================
        self.prefactor = 1.0e3
        self.activation_energy = 2.2e5

        # ================= THERMODYNAMICS =================
        #
        # CaO + Ca2SiO4 -> Ca3SiO5
        #
        # From standard enthalpies of formation at 298.15 K
        # [kJ/mol]: CaO -635.09, beta-C2S -2307.50,
        # C3S -2927.80.
        #
        #   dH = -2927.80 - ((-635.09) + (-2307.50))
        #      = +14.79 kJ/mol
        #
        # Alite is the one clinker phase that really is
        # endothermic, so this was the least wrong of the four:
        # the SIGN was right and only the magnitude was off, by
        # about 7x.
        #
        # BASIS: per kg C2S, the limiting reactant (see
        # chemistry/base.py heat_sink()).
        #
        #   +14.79 kJ/mol / 0.17224 kg/mol = +8.587e4 J/kg C2S
        #   ( equivalently +64.8 kJ/kg C3S produced )
        #
        # NOT tuned. The audit's finding was that C3S is frozen
        # by CaO starvation, not by kinetics, so adjusting the
        # prefactor or activation energy here would be fitting a
        # symptom. Those are left exactly as they were.
        self.deltaH = 8.587e4

        # ================= STOICHIOMETRY =================

        self.CaO_required = 56.08 / 172.24

        self.C3S_produced = 228.32 / 172.24

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
        available = np.minimum(
            mat.solids.C2S,
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
        mat.solids.C2S -= reacted

        mat.solids.CaO -= (
            reacted
            * self.CaO_required
        )

        mat.solids.C3S += (
            reacted
            * self.C3S_produced
        )

        # ======================================================
        # REACTION HEAT
        # ======================================================
        state.Alite_Q_sink = np.sum(
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
            flow["C2S"],
            flow["CaO"] / self.CaO_required,
        )

        reacted = float(
            self.reacted_mass(available, rate, tau)
        )

        flow["C2S"] -= reacted
        flow["CaO"] -= reacted * self.CaO_required
        flow["C3S"] += reacted * self.C3S_produced

        return float(self.heat_sink(reacted))
