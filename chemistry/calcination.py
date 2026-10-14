import math

import numpy as np

from chemistry.base import ReactionBase
from chemistry.phases import copy_solid_phases
from chemistry.phases import set_cell_solid_flow
from chemistry.composition import RAW_MEAL_COMPOSITION
from physics.gas_thermo import MOLAR_MASS
from physics.gas_thermo import SPECIES


class CalcinationModel(ReactionBase):

    def __init__(self):
        super().__init__()

        # ======================================================
        # KINETICS
        # ======================================================

        # First-order decomposition of CaCO3.
        #
        # SOURCE: the open-access calciner model of Ritschel et
        # al., arXiv:2405.03208, Table A.1, reaction r1 (k0 = 1e8,
        # n = 0, EA = 175.7 kJ/mol), itself after Mastorakos et
        # al. (1999). The standard reference for cement
        # precalciner calcination is Borgwardt, AIChE J 31 (1985)
        # 103-111, which the Norcem precalciner CFD study (SIMS
        # 2017) cites for the same reaction.
        #
        # WHAT WAS WRONG. The previous pair (42.5 1/s, 150 kJ/mol)
        # was slower by ~5 orders of magnitude: t90 at 1150 K was
        # 17 325 MINUTES against the 2-10 SECONDS a real
        # precalciner achieves. The plant calcined at all only
        # because its residence times are 50-100x too long
        # (preheater 274 s per stage, calciner ~22 min), so the
        # two errors partly cancelled -- the same
        # compensating-error pattern already dismantled for
        # hv_gs x k_eff and for kinetics x residence.
        #
        # These values need no such help. Against plant practice:
        #   1073 K  t90 = 8.2 s
        #   1123 K  t90 = 3.4 s   (850 C, "a few seconds")
        #   1173 K  t90 = 1.5 s   (900 C)
        self.prefactor = 1.0e8              # 1/s
        self.activation_energy = 1.757e5    # J/mol
        self.deltaH = 1.78e6                # J/kg CaCO3

        # ======================================================
        # STOICHIOMETRY
        # CaCO3 -> CaO + CO2
        # ======================================================

        self.CaO_ratio = 56.08 / 100.09
        self.CO2_ratio = 44.01 / 100.09

        # ======================================================
        # TEMPERATURE WINDOW -- SUPERSEDED
        #
        # reaction_rate() below no longer uses this window: the
        # gate is now the thermodynamic driving force against the
        # CO2 already in the gas. The two values are kept only
        # because ReactionBase.validate_parameters() requires a
        # consistent pair, and they are deliberately left at the
        # figures the window used so the change is visible in the
        # diff rather than hidden by a renumbering.
        #
        # NOTE that rate_vanishing_temperature() is overridden
        # below for the same reason: the base class answers
        # T_start, which stops being where this reaction dies the
        # moment the window stops gating it.
        # ======================================================

        self.T_start = 1073.0               # K
        self.T_end = 1300.0                 # K

        # ======================================================
        # CO2 PARTIAL PRESSURE IN THE PROCESS GAS [atm]
        #
        # Sets where the driving force vanishes -- the calcination
        # plateau. DERIVED from this model's own converged
        # streams, not assumed: the preheater gas carries
        # 44.1 kg/s, of which ~6.6 kg/s is CO2 released by
        # calcination and ~8.0 kg/s is combustion CO2 from
        # 2.5 kg/s of petcoke, so
        #
        #   y_CO2 = (14.6/44.01) / ((29.5/28.96) + (14.6/44.01))
        #         = 0.246
        #
        # giving a plateau at equilibrium_temperature(0.25) =
        # 1087.7 K, which brackets the 1073 K the fixed window
        # asserted.
        #
        # THE CALCINER NO LONGER USES IT (15 Oct 2026). The riser
        # now has a gas species balance (calciner_inlet_species:
        # kiln gas + tertiary air + burnt fuel), and apply() rates
        # each cell against its OWN outlet gas -- that inlet plus
        # every release up to and including the cell, the cell's
        # own CO2 solved implicitly (cell_back_pressure). At the
        # twin's flows that is 0.22 atm in the first cell and 0.33
        # at the outlet, so the plateau sits at 1103 K, not the
        # 1087.7 K this constant gave.
        #
        # It stays the representative value for the two
        # counter-current kiln zones (transition, burning): their
        # gas at a cell comes from the cells DOWNSTREAM of the
        # solid march, so a local p there can only be lagged, and
        # their parcel trains (parcels.advance_train) build a
        # reactor from T alone. That is the next thing to delete.
        #
        # It matters: T_eq spans 1005 K at 0.05 atm to 1114 K at
        # 0.40 atm, and T_eq is what decides where calcination
        # can run at all.
        # ======================================================

        self.co2_partial_pressure = 0.25    # atm

        # Total pressure the calciner's local partial pressure is
        # taken at [atm]. The riser runs a few kPa below
        # atmospheric (the ID fan); that is ~5 % on p and is not
        # resolved here.
        self.total_pressure = 1.0           # atm


        # ======================================================
        # RAW MEAL COMPOSITION
        # ======================================================

        self.CaCO3_mass_fraction = (
            RAW_MEAL_COMPOSITION["CaCO3"]
            / sum(RAW_MEAL_COMPOSITION.values())
        )

        # ======================================================
        # DECOMPOSITION EQUILIBRIUM
        #
        # CaCO3(s) <-> CaO(s) + CO2(g) is reversible, and its
        # equilibrium CO2 pressure is what actually decides where
        # calcination can run. The linear T_start..T_end window
        # above is a stand-in for it.
        #
        # P_eq(T) = exp( -(dH - T*dS) / (R*T) )   [atm]
        #
        # Both anchors are checkable and neither is fitted:
        #   dH  -- this model's own deltaH, converted to a molar
        #          basis with M_CaCO3 (178.16 kJ/mol; the open
        #          calciner literature quotes 179.4).
        #   dS  -- fixed by the one textbook point on the curve,
        #          P_eq = 1 atm at 1170 K, as dS = dH / T_eq.
        #
        # Against the tabulated decomposition curve that gives,
        # over four orders of magnitude in pressure:
        #
        #     T [K]    P_eq model   tabulated   ratio
        #      873       0.00197      0.0024     0.82
        #      973       0.0245       0.028      0.88
        #     1073       0.191        0.22       0.87
        #     1173       1.048        1.04       1.01
        #     1273       4.40         3.9        1.13
        #
        # tests/test_calcination_equilibrium.py pins these.
        # ======================================================
        self.M_CaCO3 = 0.10009              # kg/mol
        self.T_equilibrium_1atm = 1170.0    # K, P_eq = 1 atm

        self.dH_molar = self.deltaH * self.M_CaCO3          # J/mol
        self.dS_molar = self.dH_molar / self.T_equilibrium_1atm

    # ======================================================
    # EQUILIBRIUM CO2 PRESSURE [atm] over CaCO3 at T [K]
    # ======================================================
    def equilibrium_pressure(self, T):

        T = float(T)

        if T <= 0.0:
            raise ValueError("equilibrium_pressure needs T > 0 K")

        return math.exp(
            -(self.dH_molar - T * self.dS_molar)
            / (self.R * T)
        )

    # ======================================================
    # EQUILIBRIUM TEMPERATURE [K] at a CO2 partial pressure
    #
    # The inverse of equilibrium_pressure: below this
    # temperature the reaction cannot proceed against the CO2
    # already in the gas, so it is the floor the meal's own
    # calcination can cool it to -- the calcination plateau.
    #
    # P_eq(T) = p  =>  T = dH / (dS - R ln p)
    # ======================================================
    def equilibrium_temperature(self, p_co2):

        p_co2 = float(p_co2)

        if not (0.0 < p_co2):
            raise ValueError(
                "equilibrium_temperature needs p_co2 > 0 atm, "
                f"got {p_co2}"
            )

        denominator = self.dS_molar - self.R * math.log(p_co2)

        if denominator <= 0.0:
            raise ValueError(
                "equilibrium_temperature: no solution for "
                f"p_co2={p_co2} atm"
            )

        return self.dH_molar / denominator

    # ======================================================
    # CO2 BACK-PRESSURE [atm] a rate is evaluated against
    #
    # p_CO2 is the cell's own CO2 partial pressure where the
    # zone carries it (the calciner, apply below); None falls
    # back to the representative co2_partial_pressure the
    # counter-current kiln zones still use.
    # ======================================================
    def back_pressure(self, p_CO2=None):

        if p_CO2 is None:
            return float(self.co2_partial_pressure)

        p = float(p_CO2)

        if not math.isfinite(p) or p < 0.0:
            raise ValueError(
                f"CalcinationModel: p_CO2 must be >= 0 atm, got {p}"
            )

        return p

    # ======================================================
    # A MIXED CELL'S OWN BACK-PRESSURE [atm]
    #
    # The cell is rated against its outlet gas, and that gas
    # holds the CO2 the cell itself releases: p depends on the
    # extent and the extent on p. With r the CaCO3 reacted,
    #
    #   g(r) = m_in (1 - exp(-k(T, p(r)) tau)) - r
    #
    # is strictly decreasing (more CO2 -> a slower rate), with
    # g(0) >= 0 and g(m_in) <= 0, so it has exactly one root.
    # Bisection finds it without a starting guess; Newton would
    # need one on a rate that switches off at T_eq.
    #
    # n_CO2_up, n_up: CO2 and total moles [mol/s] of the gas
    # reaching the cell outlet before this cell's own CO2.
    # ======================================================
    def cell_back_pressure(self, m_in, T, tau, n_CO2_up, n_up):

        P = float(self.total_pressure)
        M = MOLAR_MASS["CO2"]

        def p_of(r):
            n_c = r * self.CO2_ratio / M
            return P * (n_CO2_up + n_c) / (n_up + n_c)

        if m_in <= 0.0 or tau <= 0.0:
            return p_of(0.0)

        def g(r):
            k = float(self.reaction_rate(T, p_of(r)))
            return m_in * (-math.expm1(-k * tau)) - r

        lo, hi = 0.0, float(m_in)

        if g(lo) <= 0.0:
            return p_of(lo)

        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if g(mid) > 0.0:
                lo = mid
            else:
                hi = mid
            if hi - lo <= 1.0e-13 * m_in:
                break

        return p_of(0.5 * (lo + hi))

    # ======================================================
    # TEMPERATURE AT WHICH THIS REACTION STOPS [K]
    #
    # Overrides ReactionBase.rate_vanishing_temperature, which
    # answers T_start -- correct only while the window law gates
    # the rate. Here the gate is the CO2 back-pressure, so the
    # reaction dies at the equilibrium temperature for the CO2
    # the gas already carries, and nowhere else.
    #
    # This has to be an EXACT zero of the rate, because it is
    # the anchor of the chord in ReactionBase.reaction_heat_slope
    # and the chord is only a secant of the real Q(T) if both its
    # endpoints lie on it. It is: at T = T_eq the driving force
    # is 1 - p/P_eq(T_eq) = 0 identically, so k = 0 and Q = 0.
    # ======================================================
    def rate_vanishing_temperature(self, p_CO2=None):

        p = self.back_pressure(p_CO2)

        # A gas with no CO2 holds nothing back: the rate never
        # vanishes, and reaction_heat_slope falls to the tangent.
        if p <= 0.0:
            return -math.inf

        return self.equilibrium_temperature(p)

    # ======================================================
    # REACTION RATE [1/s]
    #
    # Overrides ReactionBase.reaction_rate to replace the linear
    # temperature_window with the thermodynamic driving force:
    #
    #   k(T) = A exp(-EA/RT) * max(0, 1 - p_CO2 / P_eq(T))
    #
    # WHY. The window ramped the rate from 0 at 1073 K to full at
    # 1300 K. Those are not properties of anything -- they are a
    # stand-in for the equilibrium the reaction actually obeys.
    # The replacement costs no new parameter (P_eq comes from
    # this reaction's own enthalpy) and gains the composition
    # dependence the window could not express: a gas leaner in
    # CO2 lets calcination start colder (1039 K at 0.10 atm) and
    # a richer one holds it off (1098 K at 0.30 atm).
    #
    # It also smooths the reaction front instead of suppressing
    # it, which is what main.Twin.run's own note asks for: the
    # front oscillation that forced the sweep budget up is a
    # step-change in rate across a cell boundary, and a driving
    # force that decays to zero as T approaches the plateau turns
    # that step into a ramp.
    #
    # Scalar fast path for the same reason the rest of the module
    # has one: the burning zone's Strang march evaluates this
    # once per cell per sweep.
    # ======================================================
    def reaction_rate(self, T, p_CO2=None):

        self.validate_parameters()

        p = self.back_pressure(p_CO2)

        if isinstance(T, float):

            T_safe = max(T, 1.0)

            arrhenius = self.prefactor * math.exp(
                -self.activation_energy / (self.R * T_safe)
            )

            driving_force = 1.0 - (
                p
                / self.equilibrium_pressure(T_safe)
            )

            if driving_force <= 0.0:
                return 0.0

            rate = arrhenius * driving_force

            if not math.isfinite(rate):
                raise FloatingPointError(
                    "CalcinationModel: reaction_rate produced NaN/Inf"
                )

            return rate

        T_safe = np.maximum(np.asarray(T, dtype=float), 1.0)

        arrhenius = self.prefactor * np.exp(
            -self.activation_energy / (self.R * T_safe)
        )

        p_eq = np.exp(
            -(self.dH_molar - T_safe * self.dS_molar)
            / (self.R * T_safe)
        )

        driving_force = np.clip(
            1.0 - p / p_eq,
            0.0,
            1.0,
        )

        rate = arrhenius * driving_force

        if np.any(~np.isfinite(rate)):
            raise FloatingPointError(
                "CalcinationModel: reaction_rate produced NaN/Inf"
            )

        return rate

    # ======================================================
    # REACTION RATE DERIVATIVE [1/(s K)]
    #
    # Overrides ReactionBase.reaction_rate_derivative, which
    # differentiates the window law this class no longer uses.
    # The two MUST move together: the solid row's diagonal
    # carries this slope against the heat the rate above
    # produced, and a slope belonging to a different rate law
    # would not cancel at the fixed point.
    #
    # With k = A e^{-EA/RT} phi, phi = max(0, 1 - p/P_eq) and
    # P_eq = exp(-(dH_m - T dS_m)/(RT)), so
    # P_eq' = P_eq dH_m/(R T^2):
    #
    #   dphi/dT = (p / P_eq) dH_m / (R T^2)
    #   dk/dT   = (A e^{-EA/RT} / (R T^2)) [ phi EA + (p/P_eq) dH_m ]
    #
    # Both bracket terms are >= 0, so dk/dT >= 0 -- the sign the
    # linearisation rests on survives the change of rate law.
    #
    # Note it is LARGER than the Arrhenius part alone near the
    # plateau: there phi -> 0 kills the first term while
    # p/P_eq -> 1 makes the second maximal. That is exactly where
    # the slope is needed.
    # ======================================================
    def reaction_rate_derivative(self, T, p_CO2=None):

        self.validate_parameters()

        p = self.back_pressure(p_CO2)

        if isinstance(T, float):

            if T <= 1.0:
                return 0.0

            p_eq = self.equilibrium_pressure(T)

            ratio = p / p_eq

            driving_force = 1.0 - ratio

            if driving_force <= 0.0:
                return 0.0

            arrhenius = self.prefactor * math.exp(
                -self.activation_energy / (self.R * T)
            )

            derivative = (
                arrhenius
                / (self.R * T * T)
                * (
                    driving_force * self.activation_energy
                    + ratio * self.dH_molar
                )
            )

            if not math.isfinite(derivative):
                raise FloatingPointError(
                    "CalcinationModel: reaction_rate_derivative "
                    "produced NaN/Inf"
                )

            return derivative

        T = np.asarray(T, dtype=float)

        T_safe = np.maximum(T, 1.0)

        p_eq = np.exp(
            -(self.dH_molar - T_safe * self.dS_molar)
            / (self.R * T_safe)
        )

        ratio = p / p_eq

        driving_force = 1.0 - ratio

        arrhenius = self.prefactor * np.exp(
            -self.activation_energy / (self.R * T_safe)
        )

        derivative = (
            arrhenius
            / (self.R * T_safe * T_safe)
            * (
                driving_force * self.activation_energy
                + ratio * self.dH_molar
            )
        )

        # Zero wherever the rate itself is pinned: past the
        # plateau the driving force is clipped at 0, and below
        # the T_safe floor the temperature is frozen.
        derivative = np.where(
            (driving_force > 0.0) & (T > 1.0),
            derivative,
            0.0,
        )

        if np.any(~np.isfinite(derivative)):
            raise FloatingPointError(
                "CalcinationModel: reaction_rate_derivative "
                "produced NaN/Inf"
            )

        return derivative

    # ======================================================
    # HEAT-TRANSFER-CONTROLLED EXTENT -- REMOVED
    #
    # limit_by_available_heat() used to sit here: a ceiling that
    # capped the reacted mass at heat_available/deltaH, so a cell
    # could not draw more heat than its stream carried.
    #
    # It was the right diagnosis and the wrong instrument. The
    # diagnosis: once k*tau is large the reaction leaves the
    # kinetic regime and becomes HEAT-TRANSFER controlled -- the
    # meal sits on the calcination plateau absorbing whatever
    # arrives. The instrument was a clamp applied after the fact,
    # and it never worked: evaluated on a uniform first-sweep
    # field every cell independently believed it held the whole
    # stream enthalpy, so a 20-cell zone claimed 20x its budget
    # and the shell closure still got a negative hot face.
    #
    # Faz 6 item 1.5 addresses the mechanism instead of the
    # symptom: dQ/dTs now sits on the solid row's diagonal
    # (physics.variable_flow_rows.apply_solid_energy_balance), so
    # near the plateau the cell is pinned at the temperature
    # where reaction heat equals supply and the plateau falls out
    # of the energy balance rather than being imposed.
    #
    # BE PRECISE ABOUT WHAT THAT DOES AND DOES NOT DO. The slope
    # is large only where k*tau ~ 1. Once a cell converts
    # everything it holds, Q saturates at m_in*deltaH and dQ/dTs
    # falls to zero -- measured at the literature rate with
    # tau = 66 s (at the representative 0.25 atm): 6.8e5 W/K
    # per kg/s at the 1088 K plateau,
    # 2.5e3 at 1100 K, 9.7 at 1110 K, and 4e-14 by 1150 K. So the
    # linearisation stabilises the NEIGHBOURHOOD of the solution,
    # which is where the converged plant sits, and offers nothing
    # from a hot start where the reaction is already complete.
    # Bounding that transient needs the extent and the cell
    # energy balance solved together, not a ceiling applied after
    # the fact.
    #
    # It was also dead code throughout: no caller ever passed
    # heat_available or heat_available_cells.
    # ======================================================

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
    gas_in=None,
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

        # dQ/dTs per cell, for the source-term linearisation in
        # physics.variable_flow_rows.apply_solid_energy_balance.
        # Built in the same march as the heat itself so the slope
        # and the value cannot drift apart.
        reaction_heat_slope_cells = np.zeros(N)

        # ==================================================
        # THE GAS EACH CELL RATES AGAINST
        #
        # gas_in [kg/s species dict]: the gas entering cell 0.
        # The riser is co-current, so the gas in cell i holds
        # gas_in plus everything cells 0..i release -- known
        # for 0..i-1 by the time the march reaches i. Each cell
        # is rated against its OWN outlet gas (a mixed cell),
        # which contains the CO2 it releases itself; that makes
        # the cell implicit in its own extent, solved below.
        #
        # None keeps the representative co2_partial_pressure.
        # ==================================================

        p_CO2_cells = np.full(N, float(self.co2_partial_pressure))

        if gas_in is not None:

            n_up = {
                s: float(gas_in.get(s, 0.0)) / MOLAR_MASS[s]
                for s in SPECIES
            }

            H2O_cells = np.asarray(
                getattr(
                    state,
                    "m_dot_H2O_generated_cells",
                    np.zeros(N),
                ),
                dtype=float,
            )

            if H2O_cells.shape != (N,):
                H2O_cells = np.zeros(N)

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

            tau_i = float(dz / u_s)

            # --------------------------------------------------
            # LOCAL CO2 BACK-PRESSURE
            # --------------------------------------------------

            if gas_in is None:

                p_i = None

            else:

                n_up["H2O"] += H2O_cells[i] / MOLAR_MASS["H2O"]

                p_i = self.cell_back_pressure(
                    m_in,
                    T_i,
                    tau_i,
                    n_up["CO2"],
                    sum(n_up.values()),
                )

                p_CO2_cells[i] = p_i

            # --------------------------------------------------
            # LOCAL KINETIC RATE
            # --------------------------------------------------

            k_i = float(
                self.reaction_rate(T_i, p_i)
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

            # Slope of that heat with respect to this cell's
            # solid temperature, at the flow entering the cell.
            # tau is dz/u_s, the same residence the exponent
            # above uses.
            reaction_heat_slope_cells[i] = (
                self.reaction_heat_slope(
                    m_in,
                    T_i,
                    tau_i,
                    p_i,
                )
            )

            if gas_in is not None:
                n_up["CO2"] += (
                    m_reacted * self.CO2_ratio / MOLAR_MASS["CO2"]
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

        state.Calcination_Q_slope_cells = (
            reaction_heat_slope_cells.copy()
        )

        # The back-pressure each cell was rated against [atm].
        state.Calciner_p_CO2_cells = p_CO2_cells.copy()

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
