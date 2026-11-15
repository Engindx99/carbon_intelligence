import math

import numpy as np

from chemistry.base import ReactionBase


class BeliteModel(ReactionBase):

    def __init__(self):

        super().__init__()

        # ================= KINETICS =================
        #
        # MEASURED, not anchored (15 Nov 2026). Alonso, Fernandez &
        # Abanades, "Kinetic Study of Belite Formation in Cement Raw
        # Meals Used in the Calcium Looping CO2 Capture Process",
        # Ind. Eng. Chem. Res. 58 (2019) 5445-5454,
        # doi 10.1021/acs.iecr.9b00813 (open copy: zenodo 3528177).
        #
        # CaO + SiO2 -> C2S after calcination follows the Jander &
        # Hoffmann 3D-diffusion law (their eq 6)
        #
        #   [1 - (1 - X)^(1/3)]^2 = k t,   k = k0 exp(-Ea / R T)
        #
        # with X the molar share of the meal's calcium that has
        # gone into belite. That is what the paper MEASURES: its
        # eq 3, X_B = 1 - X_carb/X_max, is the fraction of the
        # calcium lost to carbonation, i.e. Ca in belite per Ca.
        # (Its nomenclature line reads "mol belite/mol Ca", a
        # factor 2 off; the reported X up to 0.6 on a Ca/Si ~3.2
        # meal, whose silica caps the Ca share at ~0.62, fixes the
        # Ca basis.) Table 2, raw meal RM1 (a natural marl):
        # k0 = 6.61e10 1/s, Ea = 325 kJ/mol. Ea is fixed at the
        # value Weisweiler & Osen measured for CaO/SiO2 at
        # 1000-1400 C; the paper fits 328 kJ/mol free at 815-920 C,
        # so one Ea spans the whole kiln. RM2 (limestone + marl
        # mix) gives 4.35e10 and MR (the marl alone) 5.13e10: the
        # prefactor carries the meal's Ca-Si aggregation.
        #
        # VALIDITY. Fitted at 815-920 C for X up to 0.6, Sauter
        # diameter 6 um. Used OUTSIDE that range: the transition
        # bed reaches ~1350-1600 K, where k is 100-1000x its
        # 1163 K value. The single Ea is what Weisweiler & Osen
        # measured over 1000-1400 C, which is the support for the
        # extrapolation; above ~1400 C belite meets the melt and
        # this solid-state law is no longer the mechanism (by
        # then the silica is spent in this model). For a diffusion law k goes as 1/r^2, so a
        # coarser plant meal reacts more slowly; that is NOT
        # corrected here (no plant PSD is in the model).
        # The direct CaCO3 + SiO2 path (their eq 5, 7.09e3 1/s,
        # 195 kJ/mol) is left out: the paper names the CaO path
        # "the most important reaction for the formation of belite
        # in raw meals".
        #
        # WHAT THIS REPLACES. A first-order law with Mastorakos'
        # 240 kJ/mol and a prefactor anchored to 99 % in 600 s at
        # 1473 K. At the transition zone's 1088 K it formed ~0.7 %
        # in 900 s against ~50 % here, so all belite -- and its
        # 25.6 MW of heat -- landed in ONE burning-zone cell near
        # 1364 K. CEMCAP D3.2 Fig. 3.4 (the VDZ reference kiln) has
        # ~30 % of the silica combined at the kiln inlet and the
        # free SiO2 gone by ~40 % of the kiln length.
        self.prefactor = 6.61e10           # 1/s, Jander k0
        self.activation_energy = 3.25e5    # J/mol

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
        # No onset step: the measured Arrhenius law carries the
        # temperature dependence on its own (at 923 K, k is
        # ~2e-8 1/s). The base class's window is made inactive
        # above 1 K.
        self.T_start = 0.0
        self.T_end = 1.0e-9

        # Molar masses [kg/mol] for the calcium and silicon count
        # that defines the Jander conversion.
        self._M = {
            "CaO": 0.05608, "CaCO3": 0.10009, "SiO2": 0.06008,
            "C2S": 0.17224, "C3S": 0.22832, "C3A": 0.27020,
            "C4AF": 0.48596,
        }
        self._CA_PER = {
            "CaO": 1, "CaCO3": 1, "C2S": 2, "C3S": 3, "C3A": 3,
            "C4AF": 4,
        }


    # ======================================================
    # JANDER CONVERSION FROM THE COMPOSITION
    #
    # X is not carried as a separate state: it is read off the
    # species the stream already carries, so the steady march, a
    # parcel and a handoff all agree on it.
    #
    #   X = 2 n(Si in C2S + C3S) / n(Ca, all forms)
    #
    # Alite (C2S + CaO -> C3S) keeps the silicon combined, so it
    # does not move X backwards.
    # ======================================================
    def _calcium_moles(self, flow):
        return sum(
            flow.get(sp, 0.0) / self._M[sp] * n
            for sp, n in self._CA_PER.items()
        )

    def _conversion(self, flow, n_Ca):
        n_Si_comb = (
            flow.get("C2S", 0.0) / self._M["C2S"]
            + flow.get("C3S", 0.0) / self._M["C3S"]
        )
        return min(max(2.0 * n_Si_comb / n_Ca, 0.0), 1.0)

    @staticmethod
    def _g(X):
        return (1.0 - (1.0 - X) ** (1.0 / 3.0)) ** 2

    @staticmethod
    def _g_inverse(G):
        root = math.sqrt(G)
        if root >= 1.0:
            return 1.0
        return 1.0 - (1.0 - root) ** 3

    def jander_reacted(self, flow, rate, tau):
        """SiO2 [same units as flow] that reacts in `tau` [s] at
        Jander rate coefficient `rate` [1/s], exactly integrated,
        capped by the SiO2 and CaO present."""

        available = min(
            flow.get("SiO2", 0.0),
            flow.get("CaO", 0.0) / self.CaO_required,
        )

        if available <= 0.0 or rate <= 0.0 or tau <= 0.0:
            return 0.0

        n_Ca = self._calcium_moles(flow)
        if n_Ca <= 0.0:
            return 0.0

        X0 = self._conversion(flow, n_Ca)
        X1 = self._g_inverse(self._g(X0) + rate * tau)

        reacted = (X1 - X0) * n_Ca / 2.0 * self._M["SiO2"]

        return min(max(reacted, 0.0), available)

    def substep_rate(self, flow, rate, length):
        """First-order-equivalent rate [1/s] of the SiO2 that reacts
        over `length`, for ChemistryModel's Strang substep count:
        -ln(1 - f)/length with f the share of the available SiO2
        taken. Capped at f = 1 - 1e-6 so a cell that exhausts its
        silica still gets a finite (~700 substep) bound."""

        available = min(
            flow.get("SiO2", 0.0),
            flow.get("CaO", 0.0) / self.CaO_required,
        )
        if available <= 0.0 or length <= 0.0:
            return 0.0

        f = self.jander_reacted(flow, rate, length) / available
        f = min(f, 1.0 - 1.0e-6)

        return -math.log(1.0 - f) / length


    # ======================================================
    # APPLY (HELD-UP INVENTORY FORM)
    #
    # Advances state.materials["burning"] by one state.dt, cell by
    # cell, with the same Jander law as react_flow(). Its reacted
    # mass is kg per time step, so its heat is J per step. Not
    # called by ChemistryModel.apply_burning() (which runs the flow
    # form); kept so the inventory interface has ONE kinetic law.
    # ======================================================
    def apply(self, state):

        mat = state.materials["burning"]
        solids = mat.solids

        T_cells = np.atleast_1d(np.asarray(state.Ts_burning, dtype=float))
        names = [sp for sp in self._M if hasattr(solids, sp)]

        # Work on arrays and write them back, so a scalar
        # inventory is updated too (an in-place index on a
        # temporary would drop the change).
        arrays = {
            sp: np.atleast_1d(np.asarray(getattr(solids, sp), dtype=float)).copy()
            for sp in ("SiO2", "CaO", "C2S")
        }

        Q = 0.0

        for i, T in enumerate(T_cells):

            cell = {
                sp: float(np.atleast_1d(getattr(solids, sp))[i])
                for sp in names
            }
            for sp in arrays:
                cell[sp] = float(arrays[sp][i])

            reacted = self.jander_reacted(
                cell, float(self.reaction_rate(float(T))), state.dt
            )

            arrays["SiO2"][i] -= reacted
            arrays["CaO"][i] -= reacted * self.CaO_required
            arrays["C2S"][i] += reacted * self.C2S_produced

            Q += float(self.heat_sink(reacted))

        for sp, arr in arrays.items():
            old = getattr(solids, sp)
            setattr(solids, sp, arr if np.ndim(old) else float(arr[0]))

        state.Belite_Q_sink = Q

        return state


    # ======================================================
    # REACT FLOW (STEADY-STATE, ONE CELL OR ONE PARCEL)
    #
    # Species flows `flow` [kg/s] (or parcel masses [kg]) pass a
    # cell at solid temperature T [K] for `tau` [s]. The Jander law
    # is integrated EXACTLY over tau from the conversion the
    # stream already carries (jander_reacted), so the result does
    # not depend on how tau is split -- except through the CaO
    # the competing reactions take in between, which is what the
    # Strang substeps in ChemistryModel.react_burning bound.
    #
    # `rate` [1/s] is the Jander coefficient k(T); it may be passed
    # in when the caller already evaluated reaction_rate(T).
    # ======================================================
    def react_flow(self, flow, T, tau, rate=None):

        if rate is None:
            rate = float(self.reaction_rate(T))

        reacted = self.jander_reacted(flow, rate, tau)

        flow["SiO2"] -= reacted
        flow["CaO"] -= reacted * self.CaO_required
        flow["C2S"] += reacted * self.C2S_produced

        return float(self.heat_sink(reacted))
