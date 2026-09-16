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

        half_sequence = (
            self.belite,
            self.alite,
            self.c3a,
        )

        heat = {
            self.belite: 0.0,
            self.alite: 0.0,
            self.c3a: 0.0,
            self.c4af: 0.0,
        }

        Q_cells = np.zeros(N)

        for i in range(N):

            T_i = float(Ts[i])

            rate = {
                model: float(model.reaction_rate(T_i))
                for model in heat
            }

            n_sub = max(
                1,
                math.ceil(
                    max(rate.values())
                    * tau
                    / self._MAX_RATE_SUBSTEP
                ),
            )

            h = tau / n_sub

            Q_cell = 0.0

            for _ in range(n_sub):

                for model in half_sequence:
                    q = model.react_flow(flow, T_i, 0.5 * h, rate[model])
                    heat[model] += q
                    Q_cell += q

                q = self.c4af.react_flow(flow, T_i, h, rate[self.c4af])
                heat[self.c4af] += q
                Q_cell += q

                for model in reversed(half_sequence):
                    q = model.react_flow(flow, T_i, 0.5 * h, rate[model])
                    heat[model] += q
                    Q_cell += q

            Q_cells[i] = Q_cell

            set_cell_solid_flow(
                flows["burning"].solids,
                i,
                flow,
            )

        state.Belite_Q_sink = heat[self.belite]
        state.Alite_Q_sink = heat[self.alite]
        state.C3A_Q_sink = heat[self.c3a]
        state.C4AF_Q_sink = heat[self.c4af]

        state.Burning_Q_sink_cells = Q_cells

        state.Burning_Q_sink = (
            state.Belite_Q_sink
            + state.Alite_Q_sink
            + state.C3A_Q_sink
            + state.C4AF_Q_sink
        )

        print("\n========== BURNING CHEMISTRY DEBUG ==========")
        print(f"Belite_Q_sink = {state.Belite_Q_sink:.12e} W")
        print(f"Alite_Q_sink  = {state.Alite_Q_sink:.12e} W")
        print(f"C3A_Q_sink    = {state.C3A_Q_sink:.12e} W")
        print(f"C4AF_Q_sink   = {state.C4AF_Q_sink:.12e} W")
        print(f"Burning_Q_sink = {state.Burning_Q_sink:.12e} W")
        print("==============================================")

        return state