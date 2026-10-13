import numpy as np

from chemistry.base import ReactionBase
from chemistry.base import anchored_prefactor


class BeliteModel(ReactionBase):

    def __init__(self):

        super().__init__()

        # ================= KINETICS =================
        #
        # Mastorakos (1999) activation energy, prefactor from the
        # anchor in chemistry/base.py: 99 % in 600 s at 1473 K,
        # "complete below 1300 C". Was k0 1e3, Ea 200 kJ/mol with
        # a 1123-1473 K window, which finished belite only near
        # 1900 K and released its heat where the bed was hottest:
        # the kiln then settled on a 2900 K self-heated branch
        # (13 Oct 2026).
        self.activation_energy = 2.40e5

        # ================= THERMODYNAMICS =================
        #
        # 2 CaO + SiO2 -> beta-Ca2SiO4
        #
        # From standard enthalpies of formation at 298.15 K
        # [kJ/mol]: CaO -635.09, SiO2 (alpha-quartz) -910.70,
        # beta-C2S -2307.50.
        #
        #   dH = -2307.50 - (2(-635.09) + (-910.70))
        #      = -126.62 kJ/mol
        #
        # BELITE FORMATION IS EXOTHERMIC. It was coded here as
        # +5.0e5, an endothermic sink, and that single sign was
        # 82% of the plant's total reaction-enthalpy error --
        # hidden because the raw constants invited comparison
        # with alite's 6.0e5 as though the two shared a basis.
        # They do not.
        #
        # BASIS. heat_sink() multiplies this by `reacted`, which
        # is the LIMITING REACTANT mass (chemistry/base.py), and
        # this reaction is written per kg of SiO2. So the value
        # below is per kg SiO2, NOT per kg C2S:
        #
        #   -126.62 kJ/mol / 0.06008 kg/mol = -2.1075e6 J/kg SiO2
        #   ( equivalently -735.1 kJ/kg C2S produced )
        #
        # Sign convention: deltaH is a SINK, so exothermic is
        # negative. Nothing downstream clamps it.
        #
        # Cross-check on the method: the same table and the same
        # arithmetic reproduce calcination at 1781 kJ/kg CaCO3,
        # against the 1.78e6 J/kg that chemistry/calcination.py
        # already carried from an independent source.
        self.deltaH = -2.1075e6

        # ================= STOICHIOMETRY =================

        self.CaO_required = 112.16 / 60.08

        self.C2S_produced = 172.24 / 60.08

        # ================= TEMPERATURE =================
        #
        # Onset only: belite starts forming at 650-900 C. A 1 K
        # step at 923 K (650 C), the Arrhenius factor shapes the
        # rest.
        self.T_start = 923.0
        self.T_end = 924.0

        self.prefactor = anchored_prefactor(
            self.activation_energy,
            T_anchor=1473.0,
            t_anchor=600.0,
            conversion=0.99,
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
