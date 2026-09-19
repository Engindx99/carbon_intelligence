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
            # Clamped for the same reason the scalar path returns
            # 0.0 on a non-positive slope: a negative value on the
            # solid row's diagonal would REMOVE diagonal dominance
            # instead of adding it. The scalar path had this guard
            # and the array path did not.
            * np.maximum(slope, 0.0)
        )

        if np.any(~np.isfinite(derivative)):
            raise FloatingPointError(
                f"{self.__class__.__name__}: "
                "reaction_heat_derivative produced NaN/Inf"
            )

        return derivative


    # ======================================================
    # TEMPERATURE AT WHICH THIS REACTION STOPS [K]
    #
    # The temperature below which the rate is EXACTLY zero, so
    # Q(T_vanish) = 0 exactly. For the base window law that is
    # T_start, where temperature_window clips to 0. A subclass
    # whose rate is gated by something else -- calcination, by
    # the CO2 back-pressure -- overrides this with its own.
    #
    # It is the anchor of the chord in reaction_heat_slope
    # below, so it has to be an EXACT zero of Q, not an
    # approximate one, or the chord stops being a secant of the
    # real function.
    # ======================================================
    def rate_vanishing_temperature(self):

        return float(self.T_start)


    # ======================================================
    # SLOPE HANDED TO THE SOLID ROW'S DIAGONAL [W/K]
    #
    # This is the S that apply_solid_energy_balance puts on the
    # diagonal, and reaction_heat_derivative above is only one
    # candidate for it.
    #
    # THE KEY IDENTITY. The linearisation is
    #
    #   Q_eff(Ts) = Q(Ts*) + S (Ts - Ts*)
    #
    # and at the fixed point Ts == Ts*, so Q_eff == Q(Ts*) FOR
    # ANY S WHATSOEVER. The converged answer does not depend on
    # S at all. S is therefore free to be chosen for robustness,
    # and the tangent is a poor choice for a SATURATING source.
    #
    # WHY THE TANGENT FAILS. Q = available (1 - exp(-k dt)) dH
    # saturates at available*dH once k*dt is large, and a
    # saturated sink has no slope. Measured for calcination at
    # the literature rate with dt = 66 s, in W/K per kg/s:
    #
    #   1088 K (plateau)  6.8e5
    #   1100 K            2.5e3
    #   1110 K            9.7
    #   1150 K            4e-14
    #   >= 1200 K         ~0
    #
    # So the tangent stabilises the NEIGHBOURHOOD of the
    # solution and gives nothing from a hot start. Solving a
    # single calciner cell that starts at 1223 K, where the
    # kinetics demand 36 MW and the streams carry 5 MW, gives
    # Ts = -704 K -- which is the negative hot face the shell
    # closure used to reject.
    #
    # THE CHORD. Use instead the secant to the temperature where
    # the reaction stops:
    #
    #   S = max( dQ/dTs , Q(Ts*) / (Ts* - T_vanish) )
    #
    # This is not invented damping. It is a secant of the TRUE
    # Q(T) through two EXACT points of it: Q(T_vanish) = 0,
    # because the rate is identically zero there, and Q(Ts*),
    # the value the chemistry just computed. Substituting gives
    #
    #   Q_eff(T) = Q(Ts*) (T - T_vanish) / (Ts* - T_vanish)
    #
    # a sink that vanishes at the equilibrium temperature and
    # equals the computed value at Ts*. That is the physical
    # statement the tangent cannot express -- a cell cannot
    # absorb reaction heat below the temperature at which its
    # own product gas stops the reaction -- and it makes the
    # solve unconditionally bounded, because the energy equation
    # can always find a T >= T_vanish that balances.
    #
    # Same cell as above, with the chord: Ts lands at 1106 K and
    # the sink applied is 4.9 MW, i.e. what the cell actually
    # has. Iterated to its fixed point it reaches 1088.03 K with
    # the energy balance closing exactly. A cell with heat to
    # spare reaches the IDENTICAL fixed point under chord and
    # tangent (2783.1353 K, reaction complete), which is the
    # identity above doing its work: the chord changes the path,
    # never the answer.
    #
    # max() and not the chord alone, so this is never weaker
    # than the tangent. Over-damping only slows convergence;
    # under-damping is what breaks the solve.
    # ======================================================
    def reaction_heat_slope(
        self,
        available,
        T,
        dt,
    ):

        tangent = self.reaction_heat_derivative(
            available,
            T,
            dt,
        )

        T = float(T)
        available = float(available)
        dt = float(dt)

        if available <= 0.0 or dt <= 0.0:
            return 0.0

        T_vanish = self.rate_vanishing_temperature()

        span = T - T_vanish

        # At or below the stopping temperature the reaction is
        # dead and there is no chord to take: Q is zero and so
        # is its secant.
        if span <= 0.0:
            return float(tangent)

        rate = float(self.reaction_rate(T))

        heat = (
            self.reacted_mass(available, rate, dt)
            * self.deltaH
        )

        chord = heat / span

        if not math.isfinite(chord):
            raise FloatingPointError(
                f"{self.__class__.__name__}: "
                "reaction_heat_slope produced NaN/Inf"
            )

        return max(float(tangent), chord)


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