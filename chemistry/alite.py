import numpy as np

from chemistry.base import ReactionBase
from chemistry.base import anchored_prefactor
from chemistry.composition import RAW_MEAL_COMPOSITION


def lime_budget(meal=RAW_MEAL_COMPOSITION):
    """(CaO left for alite, clinker mass) from a raw meal, in the
    meal's units: all CaCO3 calcined, Fe2O3 taken by C4AF, the
    rest of the Al2O3 by C3A, all SiO2 by belite."""

    CaO = meal["CaCO3"] * 56.08 / 100.09
    clinker = CaO + meal["SiO2"] + meal["Al2O3"] + meal["Fe2O3"]

    Al2O3_c4af = meal["Fe2O3"] * 101.96 / 159.69

    CaO_free = (
        CaO
        - meal["Fe2O3"] * 4.0 * 56.08 / 159.69
        - (meal["Al2O3"] - Al2O3_c4af) * 3.0 * 56.08 / 101.96
        - meal["SiO2"] * 2.0 * 56.08 / 60.08
    )

    return CaO_free, clinker


class AliteModel(ReactionBase):

    def __init__(self):

        super().__init__()

        # ================= KINETICS =================
        #
        # Mastorakos (1999) activation energy; prefactor from the
        # anchor in chemistry/base.py, set below with the window.
        self.activation_energy = 4.20e5

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
        # The kinetics were left untouched by that audit, which
        # found C3S frozen by CaO starvation. Starvation is gone
        # once calcination finishes upstream, and they are now
        # anchored (KINETICS above, TEMPERATURE below).
        self.deltaH = 8.587e4

        # ================= STOICHIOMETRY =================

        self.CaO_required = 56.08 / 172.24

        self.C3S_produced = 228.32 / 172.24

        # ================= TEMPERATURE =================
        #
        # Alite "only begins to form when liquid is formed", and
        # the liquid appears over 1300-1425 C. The window is that
        # liquid's share of its full amount, linear from 1573 K
        # to 1698 K: the reaction runs in the melt and scales
        # with it.
        self.T_start = 1573.0
        self.T_end = 1698.0

        # Free lime 1.25 % of clinker after 900 s at 1723 K, past
        # the window. With this plant's meal (lime_budget: per
        # 100 t, 60.90 t clinker) belite, C3A and C4AF leave
        # 8.98 t CaO, and CaO is alite's limiting reactant, so
        # 1.25 % of clinker is 91.5 % of it reacted.
        CaO_free, clinker = lime_budget()

        self.prefactor = anchored_prefactor(
            self.activation_energy,
            T_anchor=1723.0,
            t_anchor=900.0,
            conversion=1.0 - 0.0125 * clinker / CaO_free,
        )


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
