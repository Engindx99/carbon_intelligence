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
    # ARRHENIUS RATE DERIVATIVE [1/(s K)]
    #
    # d/dT of reaction_rate, for the source-term linearisation
    # in physics.variable_flow_rows.apply_solid_energy_balance.
    # Analytic, because a finite difference of a rate that
    # crosses orders of magnitude within a cell is not worth
    # trusting.
    #
    # With k(T) = A exp(-EA/RT) w(T) and w the clipped window:
    #
    #   dk/dT = A exp(-EA/RT) [ w EA/(R T^2) + w' ]
    #
    # Both terms are >= 0: the Arrhenius factor grows with T and
    # the window is non-decreasing. So dk/dT >= 0 ALWAYS, which
    # is the property the linearisation relies on -- it is what
    # makes the slope join the diagonal with the sign Patankar's
    # rule requires. A subclass that overrides reaction_rate must
    # override this with it and must preserve that sign.
    #
    # Zero wherever the rate is pinned: below T_start the window
    # is clipped to 0 and kills both terms, and at the T_safe
    # floor dT_safe/dT is 0.
    # ======================================================
    def reaction_rate_derivative(self, T):

        self.validate_parameters()

        span = self.T_end - self.T_start + 1e-12

        # Scalar fast path, for the same reason reacted_mass has
        # one: the solid row evaluates this once per cell per
        # Picard iteration.
        if isinstance(T, float):

            if T <= 1.0:
                return 0.0

            window = (T - self.T_start) / span

            if window <= 0.0:
                return 0.0

            # Past T_end the window is clipped, so it no longer
            # contributes a slope -- only the Arrhenius factor does.
            if window >= 1.0:
                window = 1.0
                window_slope = 0.0
            else:
                window_slope = 1.0 / span

            arrhenius = self.prefactor * math.exp(
                -self.activation_energy / (self.R * T)
            )

            derivative = arrhenius * (
                window
                * self.activation_energy
                / (self.R * T * T)
                + window_slope
            )

            if not math.isfinite(derivative):
                raise FloatingPointError(
                    f"{self.__class__.__name__}: "
                    "reaction_rate_derivative produced NaN/Inf"
                )

            return derivative

        T = np.asarray(T, dtype=float)

        T_safe = np.maximum(T, 1.0)

        window = self.temperature_window(T_safe)

        window_slope = np.where(
            (T_safe > self.T_start)
            & (T_safe < self.T_end)
            & (T > 1.0),
            1.0 / span,
            0.0,
        )

        arrhenius = (
            self.prefactor
            * np.exp(
                -self.activation_energy
                / (self.R * T_safe)
            )
        )

        derivative = arrhenius * (
            window
            * self.activation_energy
            / (self.R * T_safe * T_safe)
            + window_slope
        )

        # The T_safe floor freezes the rate, so the derivative
        # through it is zero, not the frozen value's slope.
        derivative = np.where(
            T > 1.0,
            derivative,
            0.0,
        )

        if np.any(~np.isfinite(derivative)):
            raise FloatingPointError(
                f"{self.__class__.__name__}: "
                "reaction_rate_derivative produced NaN/Inf"
            )

        return derivative


    # ======================================================
    # REACTION HEAT DERIVATIVE [W/K]
    #
    # d/dT of the heat this cell's reaction absorbs, given the
    # mass available to it and the time it has. It is the S in
    #
    #   Q(Ts) ~ Q(Ts*) + S (Ts - Ts*)
    #
    # that apply_solid_energy_balance moves to the diagonal.
    #
    # Q = available (1 - exp(-k dt)) deltaH, and `available` is
    # held FIXED here: it is the flow entering the cell, set by
    # the cells upstream. Differentiating it as well would add
    # the lower-triangular part of the Jacobian, which is not
    # the stiff term and would change the matrix sparsity.
    #
    #   dQ/dT = available dt exp(-k dt) deltaH dk/dT
    #
    # Non-negative whenever available and dt are, since
    # dk/dT >= 0.
    # ======================================================
    def reaction_heat_derivative(
        self,
        available,
        T,
        dt,
    ):

        if (
            isinstance(available, float)
            and isinstance(dt, float)
            and isinstance(T, float)
        ):

            if available <= 0.0 or dt <= 0.0:
                return 0.0

            rate = float(self.reaction_rate(T))
            slope = self.reaction_rate_derivative(T)

            if slope <= 0.0:
                return 0.0

            return (
                available
                * dt
                * math.exp(-rate * dt)
                * self.deltaH
                * slope
            )

        available = np.asarray(available, dtype=float)
        dt = np.asarray(dt, dtype=float)

        rate = np.asarray(self.reaction_rate(T), dtype=float)
        slope = np.asarray(
            self.reaction_rate_derivative(T),
            dtype=float,
        )

        derivative = (
            np.maximum(available, 0.0)
            * np.maximum(dt, 0.0)
            * np.exp(-rate * np.maximum(dt, 0.0))
            * self.deltaH
            * slope
        )

        if np.any(~np.isfinite(derivative)):
            raise FloatingPointError(
                f"{self.__class__.__name__}: "
                "reaction_heat_derivative produced NaN/Inf"
            )

        return derivative


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