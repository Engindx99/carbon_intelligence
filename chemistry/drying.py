import numpy as np

from chemistry.base import ReactionBase


class DryingModel(ReactionBase):

    def __init__(self):

        super().__init__()

        # ================= KINETICS =================
        self.prefactor = 1.0e3
        self.activation_energy = 5.0e4

        # ================= THERMODYNAMICS =================
        self.deltaH = 2.26e6

        # ================= TEMPERATURE =================
        self.T_start = 300.0
        self.T_end = 473.0

    # ======================================================
    # APPLY (HELD-UP INVENTORY FORM)
    #
    # Advances state.materials["preheater"] by one state.dt.
    # The water it removes is never replenished, so over a
    # steady-state solve it drained the stage inventories and
    # its heat (J per step, read as W) decayed towards zero.
    # No longer called by ChemistryModel.apply_preheater(),
    # which runs the steady-state flow form react_flow()
    # below. Kept unchanged for the inventory interface.
    # ======================================================
    def apply(self, state):

        # ======================================================
        # MATERIAL INVENTORY (PREHEATER)
        # ======================================================
        mat = state.materials["preheater"]

        # ======================================================
        # REACTION RATE
        # ======================================================
        rate = self.reaction_rate(
            state.Ts_preheater
        )

        # ======================================================
        # REACTED MASS
        # ======================================================
        reacted = self.reacted_mass(
            mat.solids.H2O,
            rate,
            state.dt,
        )

        # ======================================================
        # UPDATE PHASES
        # ======================================================
        mat.solids.H2O -= reacted

        mat.gases.H2O += reacted

        # ======================================================
        # REACTION HEAT
        # ======================================================

        state.Drying_Q_sink_cells = self.heat_sink(
            reacted
        )

        state.Drying_Q_sink = float(
            np.sum(state.Drying_Q_sink_cells)
        )

        return state


    # ======================================================
    # REACT FLOW (STEADY-STATE, ONE STAGE)
    #
    # Free moisture in the solid flow `flow` [kg/s] is exposed
    # to solid temperature T [K] for a residence time tau [s].
    # The same first-order kinetics as apply() are integrated
    # exactly over that exposure time,
    #
    #   evaporated = H2O * (1 - exp(-k(T) * tau))   [kg/s]
    #
    # `flow["H2O"]` is reduced in place; the evaporated mass
    # leaves the solid stream and is returned together with
    # the latent heat it absorbs, kg/s * J/kg = W.
    # ======================================================
    def react_flow(self, flow, T, tau, rate=None):

        if rate is None:
            rate = float(self.reaction_rate(T))

        evaporated = float(
            self.reacted_mass(flow["H2O"], rate, tau)
        )

        flow["H2O"] -= evaporated

        return float(self.heat_sink(evaporated)), evaporated
