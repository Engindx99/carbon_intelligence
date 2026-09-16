import math

import numpy as np


class ReactionBase:

    def __init__(self):

        self.R = 8.314

        # ================= KINETICS =================
        # Must be overridden by each reaction model
        self.prefactor = None
        self.activation_energy = None

        # ================= THERMODYNAMICS =================
        self.deltaH = None

        # ================= TEMPERATURE =================
        self.T_start = 300.0
        self.T_end = 2000.0


    # ======================================================
    # PARAMETER VALIDATION
    # ======================================================
    def validate_parameters(self):

        if self.prefactor is None:
            raise ValueError(
                f"{self.__class__.__name__}: "
                "prefactor is not defined"
            )


        if self.activation_energy is None:
            raise ValueError(
                f"{self.__class__.__name__}: "
                "activation_energy is not defined"
            )


        if self.deltaH is None:
            raise ValueError(
                f"{self.__class__.__name__}: "
                "deltaH is not defined"
            )


        if self.T_end <= self.T_start:
            raise ValueError(
                f"{self.__class__.__name__}: "
                "Invalid temperature window"
            )


    # ======================================================
    # TEMPERATURE WINDOW
    # ======================================================
    def temperature_window(self, T):

        window = (
            (T - self.T_start)
            /
            (self.T_end - self.T_start + 1e-12)
        )


        return np.clip(
            window,
            0.0,
            1.0,
        )


    # ======================================================
    # ARRHENIUS RATE
    # ======================================================
    def reaction_rate(self, T):

        self.validate_parameters()


        T_safe = np.maximum(
            T,
            1.0,
        )


        arrhenius = (
            self.prefactor
            *
            np.exp(
                -self.activation_energy
                /
                (self.R * T_safe)
            )
        )


        rate = (
            arrhenius
            *
            self.temperature_window(T_safe)
        )


        if np.any(~np.isfinite(rate)):

            raise FloatingPointError(
                f"{self.__class__.__name__}: "
                "reaction_rate produced NaN/Inf"
            )


        return rate


    # ======================================================
    # REACTED MASS
    # ======================================================
    def reacted_mass(
        self,
        available,
        rate,
        dt,
    ):

        # Scalar fast path, taken by the steady-state flow
        # march (react_flow), which evaluates one cell at a
        # time many times per solve. Same formula and the same
        # physical limits as the array path below.
        if (
            isinstance(available, float)
            and isinstance(rate, float)
            and isinstance(dt, float)
        ):

            if not (math.isfinite(rate) and math.isfinite(available)):
                raise FloatingPointError(
                    f"{self.__class__.__name__}: "
                    "invalid reaction rate"
                )

            reacted = available * (1.0 - math.exp(-rate * dt))

            return min(max(reacted, 0.0), max(available, 0.0))


        if np.any(~np.isfinite(rate)):
            raise FloatingPointError(
                f"{self.__class__.__name__}: "
                "invalid reaction rate"
            )


        reacted = (
            available
            *
            (
                1.0
                -
                np.exp(
                    -rate * dt
                )
            )
        )


        # physical limit
        reacted = np.minimum(
            reacted,
            available,
        )


        reacted = np.maximum(
            reacted,
            0.0,
        )


        if np.any(~np.isfinite(reacted)):

            raise FloatingPointError(
                f"{self.__class__.__name__}: "
                "reacted mass produced NaN/Inf"
            )


        return reacted


    # ======================================================
    # REACTION HEAT
    # ======================================================
    def heat_sink(
        self,
        reacted,
    ):

        self.validate_parameters()


        heat = (
            reacted
            *
            self.deltaH
        )


        if np.any(~np.isfinite(heat)):

            raise FloatingPointError(
                f"{self.__class__.__name__}: "
                "heat sink produced NaN/Inf"
            )


        return heat