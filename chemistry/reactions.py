import math

import numpy as np

from chemistry.drying import DryingModel
from chemistry.dehydroxylation import DehydroxylationModel
from chemistry.calcination import CalcinationModel

from chemistry.belite import BeliteModel
from chemistry.alite import AliteModel
from chemistry.c3a import C3AModel
from chemistry.c4af import C4AFModel

from chemistry.phases import get_cell_solid_flow
from chemistry.phases import raw_meal_solid_flow
from chemistry.phases import set_cell_solid_flow


class ChemistryModel:

    # Largest k*h allowed per Strang sub-step in the burning
    # flow march; see apply_burning().
    _MAX_RATE_SUBSTEP = 0.02

    def __init__(self):

        self.drying = DryingModel()

        self.dehydroxylation = (
            DehydroxylationModel()
        )

        self.calcination = (
            CalcinationModel()
        )

        self.belite = BeliteModel()

        self.alite = AliteModel()

        self.c3a = C3AModel()

        self.c4af = C4AFModel()


    # ======================================================
    # PREHEATER CHEMISTRY
    # ======================================================

    # ------------------------------------------------------
    # Steady-state drying on species mass FLOWS [kg/s].
    #
    # Fresh raw meal (state.m_dot_s_preheater, moisture
    # included) enters cyclone stage 5 (index N-1); the solid
    # then passes stage 4 -> ... -> stage 1 (index 0), which
    # hands it to the calciner. In each stage the free
    # moisture is exposed to that stage's solid temperature
    # for the stage residence time
    #
    #   tau = solid_holdup_mass / m_dot_s,in     [s]
    #
    # where solid_holdup_mass [kg] is the solid held up in one
    # stage (supplied by the preheater from its own geometry).
    #
    # The evaporated water LEAVES the solid stream and joins
    # the gas stream; per-stage amounts are written to
    # state.material_flows["preheater"].gases.H2O and their
    # total to state.m_dot_H2O_evaporated_preheater, which the
    # preheater stage balances and the plant mass model use.
    #
    # Stage temperatures are those of the previous pass
    # (state.Ts_preheater), the same lag every zone's
    # chemistry already has.
    # ------------------------------------------------------
    def apply_preheater(self, state, solid_holdup_mass):

        solid_holdup_mass = float(solid_holdup_mass)

        if not (np.isfinite(solid_holdup_mass) and solid_holdup_mass > 0.0):
            raise ValueError("Preheater solid hold-up mass must be > 0.")

        Ts = np.asarray(state.Ts_preheater, dtype=float)

        N = Ts.size

        flows = state.material_flows["preheater"]

        flow = raw_meal_solid_flow(state.m_dot_s_preheater)

        Q_cells = np.zeros(N)

        for i in range(N - 1, -1, -1):

            m_dot_s_in = sum(flow.values())

            if m_dot_s_in > 0.0:

                Q_cells[i], evaporated = self.drying.react_flow(
                    flow,
                    float(Ts[i]),
                    solid_holdup_mass / m_dot_s_in,
                )

            else:

                evaporated = 0.0

            flows.gases.H2O[i] = evaporated

            set_cell_solid_flow(
                flows.solids,
                i,
                flow,
            )

        state.Drying_Q_sink_cells = Q_cells

        state.Drying_Q_sink = float(np.sum(Q_cells))

        state.m_dot_H2O_evaporated_preheater = float(
            np.sum(flows.gases.H2O)
        )

        state.Preheater_Q_sink = float(
            state.Drying_Q_sink
        )

        return state



    # ======================================================
    # CALCINER CHEMISTRY
    # ======================================================

    def apply_calciner(
        self,
        state,
        dz,
        u_s,
        commit_phases=True,
        m_dot_CaCO3_in=None,
        m_dot_BoundH2O_in=None,
    ):

        # Dehydroxylation runs first: it only touches Bound_H2O,
        # but CalcinationModel.apply()'s handoff to the transition
        # zone (copy_solid_phases) copies every solid species, so
        # Bound_H2O must already be reacted before that copy runs.
        #
        # m_dot_BoundH2O_in [kg/s]: Bound_H2O entering the
        # calciner. When None it falls back to m_dot_s_calciner
        # times the raw-meal Bound_H2O fraction, the same
        # fallback CalcinationModel.apply() uses for CaCO3.
        state = self.dehydroxylation.apply_spatial(
            state,
            dz,
            u_s,
            m_dot_BoundH2O_in=m_dot_BoundH2O_in,
            commit_phases=commit_phases,
        )

        # m_dot_CaCO3_in [kg/s]: CaCO3 entering the calciner.
        # When None the calcination model falls back to
        # m_dot_s_calciner times the raw-meal CaCO3 fraction,
        # which is only right while no mass leaves the solid
        # upstream (e.g. before evaporated moisture is removed).
        state = self.calcination.apply(
            state,
            dz,
            u_s,
            m_dot_CaCO3_in=m_dot_CaCO3_in,
            commit_phases=commit_phases,
        )

        state.Calciner_Q_sink = (
            state.Calcination_Q_sink
            + state.Dehydroxylation_Q_sink
        )

        return state



        # ======================================================
        # BURNING CHEMISTRY
        # ======================================================

    # ------------------------------------------------------
    # Steady-state clinkering on species mass FLOWS [kg/s].
    #
    # The solid stream entering the kiln is the flow leaving
    # the last transition cell (state.material_flows). It is
    # marched cell by cell (solid direction 0 -> N-1); in each
    # cell every reaction integrates its first-order kinetics
    # exactly over the cell residence time tau = dz / u_s at
    # the cell solid temperature, so reacted amounts are kg/s
    # and heats W -- independent of state.dt, and converging
    # with N instead of scaling as 1/N like the held-up
    # inventory form did.
    #
    # The four reactions compete for CaO and belite feeds
    # alite, so within a cell they are coupled. They are
    # applied as a symmetric (Strang) sequence,
    #
    #   belite, alite, C3A (h/2) -> C4AF (h)
    #   -> C3A, alite, belite (h/2)
    #
    # over M sub-steps h = tau / M. Strang splitting is only
    # accurate while k*h is small: in the hottest cells the
    # reactions saturate (k*tau ~ 3-7 at N=20), and a single
    # step per cell then shares CaO by sequence order rather
    # than by kinetics. Measured on a frozen N=40 profile,
    # that made the clinkering heat oscillate with the mesh
    # (2.06 / 2.51 / 2.33 / 2.36 MW at N = 10/20/40/80).
    # M is therefore chosen per cell so that k_max*h <=
    # _MAX_RATE_SUBSTEP; at 0.02 the splitting error is below
    # the spatial error at every N tested, which then
    # converges at order ~2.3-2.6 (reference N=320). Rates
    # depend only on the cell temperature, so they are
    # evaluated once per cell.
    #
    # dz [m] and u_s [m/s] are the Burning zone's own cell
    # length and solid axial velocity.
    # ------------------------------------------------------
    # ======================================================
    # BURNING-ZONE REACTIONS OVER ONE STRETCH OF TIME
    #
    # Shared by the steady flow march (apply_burning, one cell's
    # residence time tau at a time) and the dynamic parcel train
    # (chemistry/parcels.py, a parcel's time in a cell within one
    # step). Both apply it to species amounts: a flow [kg/s] or a
    # parcel [kg]. Every reaction here is first order in an
    # amount (or the min of amounts), so the result scales with
    # the amount and the two uses are the same operation.
    # ======================================================
    def burning_rates(self, T):
        """Rate [1/s] of each clinkering reaction at T, and of
        calcination."""

        rate = {
            model: float(model.reaction_rate(T))
            for model in (
                self.belite,
                self.alite,
                self.c3a,
                self.c4af,
            )
        }

        return rate, float(self.calcination.reaction_rate(T))

    def react_burning(
        self,
        flow,
        T,
        length,
        rate,
        rate_calcination,
        heat,
    ):
        """Advance `flow` (mutated) by `length` [s] at T.

        Adds each clinkering heat to heat[model] and returns
        (total heat, calcination heat, CO2 released), in the
        units of `flow` times seconds over seconds -- W and kg/s
        for a flow, J and kg for a parcel."""

        half_sequence = (
            self.belite,
            self.alite,
            self.c3a,
        )

        # Substep count is set by the CLINKERING rates only.
        #
        # _MAX_RATE_SUBSTEP bounds the STRANG SPLITTING error,
        # and that error is a property of the four reactions
        # that compete for one CaO pool -- splitting them means
        # each is advanced while the others are frozen, which
        # is only accurate while k*h is small.
        #
        # Calcination is not in that sequence (see apply_burning)
        # and is not split against anything: it is a first-order
        # decay of CaCO3 integrated EXACTLY by
        # ReactionBase.reacted_mass as available*(1-exp(-k*h)),
        # which is unconditionally accurate for any h. Including
        # its rate here therefore bought no accuracy and instead
        # made the substep count scale with a reaction that does
        # not need substepping at all.
        #
        # That was harmless only while the calcination rate was
        # orders of magnitude below the clinkering rates. At the
        # literature rate the kiln reaches k ~ 76-300 1/s, and
        # with tau ~ 190 s per cell the old criterion demanded
        # ~1e5-1e6 substeps per cell, so a single plant sweep
        # never completed.
        n_sub = max(
            1,
            math.ceil(
                max(rate.values())
                * length
                / self._MAX_RATE_SUBSTEP
            ),
        )

        h = length / n_sub

        Q_total = 0.0

        Q_calcination = 0.0

        dm_CO2_total = 0.0

        def calcine(length):
            nonlocal Q_total, Q_calcination, dm_CO2_total

            q_calc, dm_CO2 = self.calcination.react_flow(
                flow,
                T,
                length,
                rate_calcination,
            )

            Q_calcination += q_calc
            dm_CO2_total += dm_CO2
            Q_total += q_calc

        for _ in range(n_sub):

            # Calcination in two halves around the clinkering
            # sequence, so the whole substep is a symmetric (Strang)
            # split. It competes with nothing for CaCO3, but it FEEDS
            # the CaO pool the four below draw on, and through the
            # burning zone belite is CaO-limited (CaO/required
            # 3.4-7.9 kg/s against 9.8-11.6 of SiO2). Released whole
            # at the start of each substep, as it was, it handed them
            # a substep's CaO early: a first-order split error that
            # put the clinker 3.3 % high in C3S and 2.2 % in C2S
            # against the converged ODE (substep -> 0). Halved, the
            # error is second order: 5e-4 in C3S at the same substep
            # count. Its total over the substep is unchanged --
            # exp(-k h/2)^2 = exp(-k h).
            calcine(0.5 * h)

            for model in half_sequence:
                q = model.react_flow(flow, T, 0.5 * h, rate[model])
                heat[model] += q
                Q_total += q

            q = self.c4af.react_flow(flow, T, h, rate[self.c4af])
            heat[self.c4af] += q
            Q_total += q

            for model in reversed(half_sequence):
                q = model.react_flow(flow, T, 0.5 * h, rate[model])
                heat[model] += q
                Q_total += q

            calcine(0.5 * h)

        return Q_total, Q_calcination, dm_CO2_total

    def apply_burning(self, state, dz, u_s):

        dz = float(dz)
        u_s = float(u_s)

        if not (np.isfinite(dz) and dz > 0.0):
            raise ValueError("Burning dz must be > 0.")

        if not (np.isfinite(u_s) and u_s > 0.0):
            raise ValueError("Burning solid velocity u_s must be > 0.")

        tau = dz / u_s

        Ts = np.asarray(state.Ts_burning, dtype=float)

        N = Ts.size

        flows = state.material_flows

        N_transition = flows["transition"].solids.CaCO3.size

        flow = get_cell_solid_flow(
            flows["transition"].solids,
            N_transition - 1,
        )

        heat = {
            self.belite: 0.0,
            self.alite: 0.0,
            self.c3a: 0.0,
            self.c4af: 0.0,
        }

        Q_cells = np.zeros(N)

        # Residual calcination in the kiln. The meal arrives still
        # carbonated, and until now nothing here consumed it: CaCO3
        # crossed the burning zone with in == out and left as
        # "clinker". It is not counted in the substep criterion --
        # its decay is integrated exactly for any length -- but it
        # is split symmetrically around the clinkering sequence,
        # because it feeds their CaO pool (react_burning).
        #
        # Its CO2 leaves the solid stream, so it is accumulated
        # separately and handed to the zone as a per-cell mass
        # release, the same quantity the transition and calciner
        # already publish.
        dm_CO2_cells = np.zeros(N)

        Q_calcination_cells = np.zeros(N)

        # dQ/dTs of the calcination term, for the source-term
        # linearisation in
        # physics.variable_flow_rows.apply_solid_energy_balance.
        #
        # ONLY calcination. Patankar's rule applies to any subset
        # of a source; a term left un-linearised simply stays in b
        # as it was. Calcination is the stiff one -- k crosses
        # orders of magnitude within a cell's temperature span --
        # while the four clinkering reactions are the ones the
        # Strang split exists for, and an exact slope through that
        # split is a different and much larger problem.
        #
        # The substepping does not complicate it. Calcination is a
        # first-order decay run at full step length once per
        # substep, so n_sub steps of available*(1-exp(-k h)) leave
        # exactly CaCO3_in*exp(-k*tau): the cell total is
        # CaCO3_in*(1-exp(-k tau))*deltaH however many substeps the
        # clinkering rates demanded. Nor do the other four
        # interfere -- they consume CaO, never CaCO3.
        Q_calcination_slope_cells = np.zeros(N)

        for i in range(N):

            T_i = float(Ts[i])

            # The CaCO3 entering this cell, read before the
            # substep loop consumes it.
            CaCO3_in_cell = float(flow["CaCO3"])

            rate, rate_calcination = self.burning_rates(T_i)

            (
                Q_cell,
                Q_calcination_cell,
                dm_CO2_cell,
            ) = self.react_burning(
                flow,
                T_i,
                tau,
                rate,
                rate_calcination,
                heat,
            )

            Q_cells[i] = Q_cell

            Q_calcination_cells[i] = Q_calcination_cell

            Q_calcination_slope_cells[i] = (
                self.calcination.reaction_heat_slope(
                    CaCO3_in_cell,
                    T_i,
                    tau,
                )
            )

            dm_CO2_cells[i] = dm_CO2_cell

            set_cell_solid_flow(
                flows["burning"].solids,
                i,
                flow,
            )

        state.Belite_Q_sink = heat[self.belite]
        state.Alite_Q_sink = heat[self.alite]
        state.C3A_Q_sink = heat[self.c3a]
        state.C4AF_Q_sink = heat[self.c4af]

        # Kept separate from the four clinkering terms because it
        # is the one that also moves mass, and the burning zone
        # needs the CO2 profile, not just the heat.
        state.Calcination_Q_burning = float(
            np.sum(Q_calcination_cells)
        )

        state.Calcination_Q_burning_cells = Q_calcination_cells

        state.Calcination_Q_burning_slope_cells = (
            Q_calcination_slope_cells
        )

        state.m_dot_CO2_generated_burning_cells = dm_CO2_cells

        state.m_dot_CO2_generated_burning = float(
            np.sum(dm_CO2_cells)
        )

        state.Burning_Q_sink_cells = Q_cells

        # Must include calcination, because Q_cells does: the two
        # are the same quantity at different resolutions and the
        # zone balance reads the scalar while the solid row reads
        # the array. Summing only the four clinkering terms here
        # would have left the balance short by the calcination
        # heat with nothing to flag it.
        state.Burning_Q_sink = (
            state.Belite_Q_sink
            + state.Alite_Q_sink
            + state.C3A_Q_sink
            + state.C4AF_Q_sink
            + state.Calcination_Q_burning
        )

        return state