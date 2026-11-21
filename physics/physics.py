import numpy as np

ZONE_ENERGY_WEIGHTS = {
    "burning": {
        "axial": [
            0.05,
            0.10,
            0.20,
            0.35,
            0.30,
        ],
    },

    "transition": {
        "axial": [
            0.10,
            0.15,
            0.20,
            0.25,
            0.30,
        ],
    },

    # Highest where the gas enters, as before: the riser is now
    # co-current, its gas entering at cell 0 (the bottom, with the
    # tertiary air and the fuel), so the profile runs the other way.
    "calciner": {
        "axial": [
            0.30,
            0.25,
            0.20,
            0.15,
            0.10,
        ],
    },

    "preheater": {
        "axial": [
            0.10,
            0.15,
            0.20,
            0.25,
            0.30,
        ],
    },

    "cooler": {
        "axial": [
            0.30,
            0.25,
            0.20,
            0.15,
            0.10,
        ],
    },
}


# ======================================================
# AXIAL PROFILE RESAMPLING
#
# Resample a calibrated axial profile (given at its own
# cell-center positions) onto N new cell centers via linear
# interpolation, then renormalize so the weights still sum
# to 1 (total energy is conserved regardless of N). This
# lets a profile calibrated at one mesh resolution be reused
# at a finer one without inventing new physics.
# ======================================================
def resample_axial_weights(weights, N):

    weights = np.asarray(weights, dtype=float)
    n_ref = len(weights)

    x_ref = (np.arange(n_ref) + 0.5) / n_ref
    x_new = (np.arange(N) + 0.5) / N

    resampled = np.interp(x_new, x_ref, weights)

    return resampled / np.sum(resampled)


# ======================================================
# GAS THERMODYNAMIC PROPERTIES
# ======================================================

def cp_gas(T):
    """
    Temperature-dependent representative combustion-gas Cp.

    SI units:
        T  : K
        Cp : J/(kg K)

    Temporary thermodynamic closure.
    Later this can be replaced by species-based Cp.
    """

    # Scalar fast path. This is called ~880k times per
    # steady-state solve, almost always on one temperature at a
    # time (Tg_iter[i] inside the per-cell assembly loops), and
    # np.asarray + np.maximum on a 0-d array cost ~17 us against
    # ~0.2 us for the same arithmetic in plain Python.
    #
    # np.float64 subclasses float, so array elements take this
    # path too. T*T is what numpy's ** 2 already lowers to, so
    # the result is bit-identical to the array path -- verified
    # over 30000 temperatures in [250, 3500] K.
    if isinstance(T, float):

        Cp = (
            1050.0
            + 0.18 * T
            - 3.0e-5 * (T * T)
        )

        return Cp if Cp > 1050.0 else 1050.0

    T = np.asarray(T, dtype=float)

    Cp = (
        1050.0
        + 0.18 * T
        - 3.0e-5 * T**2
    )

    return np.maximum(Cp, 1050.0)


def h_gas(T, T_ref):
    """
    Gas sensible enthalpy relative to T_ref.

    SI units:
        T     : K
        T_ref : K
        h     : J/kg
    """

    # Scalar fast path -- see cp_gas. The cubic term keeps ** 3
    # rather than T*T*T: repeated multiplication is NOT
    # bit-identical to the array path here (~1 ulp), whereas
    # T*T for the square and ** 3 for the cube reproduce it
    # exactly -- verified over 30000 temperatures in
    # [250, 3500] K.
    if isinstance(T, float):

        return (
            1050.0 * (T - T_ref)
            + 0.09 * (T * T - T_ref**2)
            - 1.0e-5 * (T**3 - T_ref**3)
        )

    T = np.asarray(T, dtype=float)

    h = (
        1050.0 * (T - T_ref)
        + 0.09 * (T**2 - T_ref**2)
        - 1.0e-5 * (T**3 - T_ref**3)
    )

    return h


# ======================================================
# SOLID THERMODYNAMIC PROPERTIES
#
# One enthalpy for every solid stream in the plant -- raw meal,
# calcined meal, clinker -- so a handoff that passes H between
# two zones hands over the same temperature it would read back.
# Every zone used to carry its own literal Cp_s = 850 and build
# H = m Cp (T - T_ref) itself; the solid rows now linearise
# h_solid at the iterate the way the gas rows linearise h_gas
# (physics/variable_flow_rows.py), so h_solid is free to be
# nonlinear.
#
# SENSIBLE HEAT. A Maier-Kelley form, Cp = a + b T - c / T^2,
# fitted (least squares on h) to the "Clinker 2000" column of the
# clinker enthalpy table in cementkilns.co.uk, "Thermochemistry
# of clinker minerals" (D. Moore, cemkilndoc021, data mainly
# CODATA), 0-1550 degC: the fit reproduces every tabulated h
# within 3.5 kJ/kg. Cp runs from ~750 J/(kg K) at 300 K to ~1180
# at 1500 K, where the constant 850 it replaces sat. One
# relation for meal, calcined meal and clinker alike (user
# decision, 13 Oct 2026): their table Cp's differ by a few %.
# Cp > 0 above ~160 K, so h is strictly increasing over the
# T_SOLID_MIN..T_SOLID_MAX window the inverse searches.
#
# MELTING. The table excludes the melt; its Note 2 gives the
# latent heat taken up by a typical modern clinker as "about
# 60 kJ/kg ... between 1320 and 1360 degC, and as temperature
# rises, further melting requires an extra 0.08 kJ/kg/degC" --
# a 60 kJ/kg ramp over 1593.15-1633.15 K plus 80 J/(kg K)
# above it. It is part of h, so the cooler gets the same heat
# back when the liquid freezes, and the handoffs conserve it.
#
# SMOOTH MELT CURVE (21 Nov 2026). The latent heat is taken up
# along a smoothstep in s = (T - onset) / (end - onset),
# L (3 s^2 - 2 s^3), not a straight ramp, and the 80 J/(kg K)
# comes in over the band as 80 dT (s^3 - s^2), which meets
# 80 (T - end) at the end with the same slope. So h is C1 and
# Cp continuous everywhere. With the straight ramp Cp jumped by
# ~1500 J/(kg K) at both ends of the band: the solid rows
# linearise h at the iterate (Newton), and a bed node sitting on
# the kink at 1633.15 K flipped between the two slopes, a
# 7-sweep limit cycle that stopped the dynamic solve (burning
# node 4, t = 350 s of a 5 % fuel step). Unchanged: the 60 kJ/kg
# total, the band, and h below and above the band exactly; only
# the shape inside the band moves (by at most 5.9 kJ/kg, the
# latent's S-curve against the line); Cp peaks at 1.5x the old
# ramp's 1500 J/(kg K) at the band's middle. A melt fraction that
# starts and ends smoothly is no less physical than the line:
# the source gives the total and the band, not the shape. The
# 80 J/(kg K) term is slightly negative inside the band (Cp
# down by at most 27 J/(kg K) at s = 1/3, against a total of
# >1200), so Cp stays positive and h strictly increasing.
# ======================================================

CP_SOLID_A = 924.488  # J/(kg K)
CP_SOLID_B = 0.173533  # J/(kg K^2)
CP_SOLID_C = 2.20348e7  # J K/kg

MELT_T_ONSET = 1593.15  # K, 1320 degC
MELT_T_END = 1633.15  # K, 1360 degC
MELT_LATENT = 60.0e3  # J/kg clinker, over the onset ramp
MELT_CP_EXTRA = 80.0  # J/(kg K), further melting above MELT_T_END

T_SOLID_MIN = 200.0  # K
T_SOLID_MAX = 4000.0  # K

_MELT_DT = MELT_T_END - MELT_T_ONSET


def _H_solid_abs(T):
    """Solid enthalpy on an arbitrary common datum [J/kg]."""

    sensible = (
        CP_SOLID_A * T
        + 0.5 * CP_SOLID_B * T * T
        + CP_SOLID_C / T
    )

    s = np.clip((T - MELT_T_ONSET) / _MELT_DT, 0.0, 1.0)

    melt = (
        MELT_LATENT * s * s * (3.0 - 2.0 * s)
        + MELT_CP_EXTRA * _MELT_DT * s * s * (s - 1.0)
        + MELT_CP_EXTRA * np.maximum(T - MELT_T_END, 0.0)
    )

    return sensible + melt


def cp_solid(T):
    """Solid Cp [J/(kg K)] at T [K], the derivative of h_solid,
    the latent heat of the melt included."""

    scalar = np.ndim(T) == 0
    T = np.asarray(T, dtype=float)

    s = np.clip((T - MELT_T_ONSET) / _MELT_DT, 0.0, 1.0)

    cp = (
        CP_SOLID_A
        + CP_SOLID_B * T
        - CP_SOLID_C / (T * T)
        + (MELT_LATENT / _MELT_DT) * 6.0 * s * (1.0 - s)
        + MELT_CP_EXTRA * np.where(T >= MELT_T_END, 1.0, s * (3.0 * s - 2.0))
    )

    return float(cp) if scalar else cp


def h_solid(T, T_ref):
    """Solid enthalpy relative to T_ref [J/kg]."""

    scalar = np.ndim(T) == 0

    h = _H_solid_abs(np.asarray(T, dtype=float)) - _H_solid_abs(
        float(T_ref)
    )

    return float(h) if scalar else h


def T_solid_from_h(h_target, T_ref):
    """Invert h_solid: the T [K] with h_solid(T, T_ref) = h_target.

    Bracketed Newton on cp_solid, as T_gas_from_h: h_solid is
    strictly increasing, so the root is unique; a step leaving
    the bracket falls back to bisection. Out of the window it
    raises rather than clip, like the gas inverse.
    """

    if np.ndim(h_target) > 0:
        return np.array(
            [
                T_solid_from_h(h, T_ref)
                for h in np.asarray(h_target, dtype=float).ravel()
            ]
        ).reshape(np.shape(h_target))

    h_target = float(h_target)
    lo, hi = T_SOLID_MIN, T_SOLID_MAX

    f_lo = h_solid(lo, T_ref) - h_target
    f_hi = h_solid(hi, T_ref) - h_target

    if f_lo > 0.0 or f_hi < 0.0:
        raise ValueError(
            f"solid enthalpy {h_target:.6g} J/kg is outside "
            f"[{T_SOLID_MIN}, {T_SOLID_MAX}] K"
        )

    # The constant-Cp guess is within a few % everywhere.
    T = min(max(float(T_ref) + h_target / 1000.0, lo), hi)

    for _ in range(100):

        f = h_solid(T, T_ref) - h_target

        if f > 0.0:
            hi = T
        else:
            lo = T

        T_new = T - f / cp_solid(T)

        if not (lo < T_new < hi):
            T_new = 0.5 * (lo + hi)

        if abs(T_new - T) <= 1e-12 * T:
            return T_new

        T = T_new

    return T


def T_gas_from_h(h_target, T_ref, T_min, T_max):
    """
    Invert h_gas: solve h_gas(T, T_ref) = h_target for T,
    restricted to [T_min, T_max].

    SI units:
        h_target : J/kg
        T_*      : K

    h_gas is a cubic whose derivative is exactly cp_gas
    (1050 + 0.18*T - 3e-5*T^2, strictly positive over any
    physical range here), so h_gas is strictly increasing, the
    root is unique, and Newton on cp_gas converges
    quadratically -- typically 4 evaluations.

    The bracket is carried along and a Newton step that would
    leave it degrades to a bisection step, so convergence is
    never worse than the plain bisection this replaces.

    An out-of-range target RAISES. It used to return the
    corresponding bound, silently, and that was not a harmless
    convenience -- MEASURED on the literature-kinetics tree:
    the transition gas inlet needed 4037.9 K, the bound is
    4000.0, and the 7.281181e5 W of enthalpy above the bound
    was destroyed. That is exactly the residual by which the
    Transition and Pyroprocess energy balances were failing,
    reproduced to every digit. The same clamp also saturated
    reporter.diagnostics.burning_enthalpy_ceiling, which
    returned precisely 4000.0 -- the diagnostic meant to
    arbitrate a runaway was itself the thing being clamped.

    Worse than the leak: inside the clamped region dT/dh is
    ZERO, so the inverted temperature stops responding to the
    upstream enthalpy altogether. The feedback that stabilises
    a handoff is severed, which is a mechanism for a limit
    cycle and not merely for a wrong number.

    The fix is to raise, NOT to move the bound to 6000. A gas
    at 4000 K is a finding about the plant, and widening the
    window would hide it while keeping the same cliff further
    out. A caller that can legitimately meet an out-of-range
    state -- a root finder exploring operating points -- should
    catch this and treat the point as infeasible, which is
    information; a silent bound is not.

    NOTE for anyone raising T_max: h_gas is the analytic cubic
    integral of cp_gas and is NOT monotone forever. cp_gas
    floors at 1050 J/(kg K); h_gas does not carry that floor,
    so it follows the polynomial, whose integrand crosses zero
    near 9633 K -- above that the inverse is not unique and
    this function will happily return nonsense. Note what that
    figure means: the ceiling is 2.4x the 4000 K window, so
    the window is a MODELLING choice, not a numerical
    necessity. Which is precisely why clamping silently at it
    was indefensible.

    This replaces three separate 100-step bisections (burning,
    transition and calciner gas inlets). Those spent half their
    work below double precision: halving [200, 4000] K 100
    times passes the resolution of a double at ~52 steps.
    """

    T_low = float(T_min)
    T_high = float(T_max)

    h_at_low = h_gas(T_low, T_ref)
    h_at_high = h_gas(T_high, T_ref)

    if h_target < h_at_low:
        raise ValueError(
            "gas enthalpy below the inversion window: "
            f"h_target={h_target:.6e} J/kg is under "
            f"h_gas({T_low:.2f} K)={h_at_low:.6e} J/kg"
        )

    if h_target > h_at_high:
        raise ValueError(
            "gas enthalpy above the inversion window: "
            f"h_target={h_target:.6e} J/kg exceeds "
            f"h_gas({T_high:.2f} K)={h_at_high:.6e} J/kg "
            f"by {(h_target - h_at_high):.6e} J/kg. The gas is "
            "hotter than the window allows; widening the window "
            "would hide that, not fix it."
        )

    # The bounds themselves remain exact answers.
    if h_target == h_at_low:
        return T_low

    if h_target == h_at_high:
        return T_high

    T = 0.5 * (T_low + T_high)

    for _ in range(60):

        if T_high - T_low <= 1.0e-12 * T_high:
            break

        residual = h_gas(T, T_ref) - h_target

        if residual < 0.0:
            T_low = T
        elif residual > 0.0:
            T_high = T
        else:
            return T

        cp = cp_gas(T)

        T_newton = (
            T - residual / cp
            if cp > 0.0
            else 0.5 * (T_low + T_high)
        )

        if not (T_low < T_newton < T_high):
            T_newton = 0.5 * (T_low + T_high)

        if T_newton == T:
            break

        T = T_newton

    return T


# ======================================================
# GAS TRANSPORT PROPERTIES (SUTHERLAND'S LAW)
#
#   mu(T) = mu_0 (T/T_0)^1.5 (T_0 + S_mu) / (T + S_mu)
#   k(T)  = k_0  (T/T_0)^1.5 (T_0 + S_k)  / (T + S_k)
#
# Air constants (White, Viscous Fluid Flow; as tabulated in
# the COMSOL CFD Module guide): mu_0 = 1.716e-5 Pa s,
# k_0 = 0.0241 W/(m K), T_0 = 273 K, S_mu = 111 K,
# S_k = 194 K.
#
# Against tabulated air data (Incropera, Table A.4) the
# deviation is within 2 % for 300-1000 K but grows with T:
# at 1500 K mu is ~5 % and k ~14 % low. Burning-zone gas
# runs well above 1000 K, so this closure under-predicts k_g
# there.
#
# The kiln gas is represented by air, the same representative-
# gas closure cp_gas() uses. Where high-T accuracy or CO2/H2O
# fractions matter, a species-based closure should replace it.
# ======================================================
SUTHERLAND_AIR = {
    "mu_0": 1.716e-5,   # Pa s
    "k_0": 0.0241,      # W/(m K)
    "T_0": 273.0,       # K
    "S_mu": 111.0,      # K
    "S_k": 194.0,       # K
}


def _sutherland(T, ref_value, T_0, S):

    # Scalar fast path, on the same grounds as cp_gas above and
    # verified the same way: np.asarray + np.any on a 0-d array
    # cost ~14 us against ~0.3 us for the arithmetic in plain
    # Python, and physics.shell calls this four times per pass of
    # a Newton solve that itself sits inside the preheater's
    # per-node wall solve. The arithmetic is identical, and the
    # two paths were verified bit for bit over 40000
    # temperatures in [250, 1200] K.
    if isinstance(T, float):

        if T <= 0.0:
            raise ValueError("Sutherland's law needs T > 0 K")

        return (
            ref_value
            * (T / T_0) ** 1.5
            * (T_0 + S)
            / (T + S)
        )

    T = np.asarray(T, dtype=float)

    if np.any(T <= 0.0):
        raise ValueError("Sutherland's law needs T > 0 K")

    value = ref_value * (T / T_0) ** 1.5 * (T_0 + S) / (T + S)

    return float(value) if value.ndim == 0 else value


def mu_gas(T):
    """Dynamic viscosity of the representative gas [Pa s], T in K."""

    c = SUTHERLAND_AIR

    return _sutherland(T, c["mu_0"], c["T_0"], c["S_mu"])


def k_gas(T):
    """Thermal conductivity of the representative gas [W/(m K)], T in K."""

    c = SUTHERLAND_AIR

    return _sutherland(T, c["k_0"], c["T_0"], c["S_k"])


# ======================================================
# SECOND-ORDER ADVECTION CORRECTION (van Leer TVD)
#
# Every zone discretises axial transport in conservative
# flux form and takes each face value as the UPSTREAM CELL
# CENTRE:
#
#   m_dot * (phi_face_out - phi_face_in) = sources
#   phi_face := phi[upstream cell]
#
# That is first-order upwind. Its truncation error is
# O(dz) and, worse, that error acts as a numerical
# DIFFUSION which smears exactly the steep axial gradients
# the cold end of the kiln is made of. The N=10/20/40 grid
# study measured the resulting observed order at ~0.83.
#
# This helper upgrades the face value to a limited linear
# reconstruction (MUSCL, kappa = -1):
#
#   phi_face = phi_U + 0.5 * psi(r) * (phi_U - phi_UU)
#   r        = (phi_D - phi_U) / (phi_U - phi_UU)
#
# with U the upstream cell, UU the cell upstream of U and D
# the downstream cell. psi is the van Leer limiter, written
# here in its equivalent harmonic form
#
#   0.5 * psi(r) * b = a * b / (a + b)   for a * b > 0
#                    = 0                 otherwise
#
# (a = phi_D - phi_U, b = phi_U - phi_UU). That form needs
# no division guard: a and b share a sign wherever the
# branch is taken, so a + b cannot be zero there. van Leer
# is TVD, so the reconstruction creates no new extremum --
# it cannot introduce an unphysical temperature over- or
# undershoot -- and wherever the profile is not smooth
# (a * b <= 0) it degrades continuously back to the current
# first-order scheme.
#
# APPLICATION. The correction is returned PER CELL and is
# meant to be applied by DEFERRED CORRECTION: the caller
# leaves its matrix exactly as it is -- still the
# first-order upwind operator, still diagonally dominant --
# and subtracts (flux capacity) * correction[i] from b[i].
# The anti-diffusive part is therefore frozen at the Picard
# iterate, and at the fixed point, where the iterate equals
# the solution, the converged answer satisfies the full
# second-order equation. Keeping the implicit operator
# first-order is deliberate: moving the reconstruction into
# A introduces a POSITIVE off-diagonal and destroys the
# M-matrix property the existing Picard loop relies on.
#
# CONSERVATION. An interior face contributes +D to one cell
# and -D to its neighbour, so the corrections telescope and
# the scheme stays exactly conservative cell to cell. The
# inlet face carries no correction (its value is the known
# handoff stream, not a reconstruction), so
#
#   sum(corrections) == outlet face correction
#
# which is precisely the amount by which the zone's outlet
# flux changes. The caller MUST therefore feed the same
# reconstructed outlet value into its handoff, or that
# difference leaks out of the energy balance.
# outlet_face_value() below returns it, and is defined to
# agree with the last entry of this function bit for bit.
#
# ORIENTATION. `reverse=False` means the stream enters at
# index 0 and leaves at index N-1 (the solid phase in every
# zone). `reverse=True` means it enters at N-1 and leaves
# at 0 (the gas phase in burning, transition and cooler).
#
# The quantity reconstructed must be the one the flux is
# linear in: gas enthalpy h for the gas phase (h is cubic
# in T, so reconstructing T would not be conservative), and
# temperature for the solid phase, whose flux
# m_dot_s * Cp_s * (Ts - T_ref) is affine in Ts.
# ======================================================
def second_order_upwind_correction(phi, phi_in, reverse=False):

    D = second_order_upwind_face_corrections(
        phi,
        phi_in,
        reverse=reverse,
    )

    if D.size < 2:
        return np.zeros(np.asarray(phi, dtype=float).size)

    # Cell i gains its outflow face correction and loses
    # its inflow face correction.
    correction = D[1:] - D[:-1]

    if reverse:
        correction = correction[::-1]

    return correction


# ======================================================
# FACE-RESOLVED SECOND-ORDER CORRECTIONS
#
# The same van Leer reconstruction as above, but returned
# per FACE instead of already differenced per cell.
#
# A cell's correction is only the difference of its two face
# corrections when the same mass flow passes through both.
# Where a stream gains or loses mass inside the zone -- a
# calcining bed shedding CO2, say -- the two faces carry
# different flows and the flux correction is
#
#   m_out * D[out face] - m_in * D[in face]
#
# which cannot be recovered from the difference alone. Those
# callers take the faces from here.
#
# The returned array has N+1 entries in FLOW order: D[p] is
# the inflow face of the p-th cell along the stream and
# D[p+1] its outflow face, so D[0] is the zone inlet face and
# D[N] the outlet face. With reverse=True, flow order runs
# from the last array index to the first, i.e. the cell at
# array index i sits at flow position p = N-1-i.
# ======================================================
def second_order_upwind_face_corrections(phi, phi_in, reverse=False):

    phi = np.asarray(phi, dtype=float)

    N = phi.size

    # Two cells are the minimum needed to form an upstream
    # gradient; below that the scheme stays first-order.
    if N < 2:
        return np.zeros(N)

    if reverse:
        phi = phi[::-1]

    # --------------------------------------------------
    # INTERIOR FACES
    #
    # Face f (1 .. N-1) separates cell f-1 (upstream) from
    # cell f (downstream).
    # --------------------------------------------------

    a = phi[1:] - phi[:-1]

    b = np.empty(N - 1)

    # The first interior face has no cell upstream of its
    # upstream cell -- the inlet FACE sits there instead,
    # half a cell further up. Its one-sided gradient is
    # therefore (phi[0] - phi_in) / (dz/2), i.e. twice the
    # per-cell difference, which keeps the reconstruction
    # second-order right at the inlet rather than dropping
    # to first order on the face where the incoming stream
    # is still steepest.
    b[0] = 2.0 * (phi[0] - phi_in)

    b[1:] = phi[1:-1] - phi[:-2]

    ab = a * b

    D = np.zeros(N + 1)

    np.divide(
        ab,
        a + b,
        out=D[1:N],
        where=ab > 0.0,
    )

    # --------------------------------------------------
    # OUTLET FACE
    #
    # Nothing lies downstream, so there is no ratio to
    # limit against; the standard second-order outflow
    # condition is a plain linear extrapolation of the last
    # cell-centre gradient onto the boundary face, half a
    # cell away. This is the term that removes the
    # half-cell bias in the zone handoff enthalpies.
    # --------------------------------------------------

    D[N] = 0.5 * (phi[N - 1] - phi[N - 2])

    return D


# ======================================================
# RECONSTRUCTED OUTLET FACE VALUE
#
# The boundary value matching second_order_upwind_correction
# above. Zones hand off to the next unit with the value at
# their outlet FACE, but the solution array only holds cell
# CENTRES, and the last centre sits half a cell short of
# that face -- a systematic O(dz) bias in exactly the
# handoff quantities the grid study found worst converged.
#
# Returns the linear extrapolation used as the outlet flux
# by the correction above, so the zone's internal energy
# balance and its handoff stay consistent to the last bit.
#
# Since the argument may be any quantity affine in the
# reconstructed one (gas ENTHALPY per unit mass or the
# enthalpy FLOW m_dot * h, solid TEMPERATURE or the flow
# m_dot_s * Cp_s * (Ts - T_ref)), the extrapolation may be
# taken directly on whichever of those the caller holds.
# ======================================================
def outlet_face_value(phi, reverse=False):

    phi = np.asarray(phi, dtype=float)

    if phi.size < 2:
        return float(phi[-1]) if phi.size else 0.0

    if reverse:
        return float(phi[0] + 0.5 * (phi[0] - phi[1]))

    return float(phi[-1] + 0.5 * (phi[-1] - phi[-2]))


# ======================================================
# REPRESENTATIVE PETCOKE COMPOSITION
# [mass fraction]
#
# Read by gas_mass_balance (to size the combustion air) and by
# physics.kiln_closures.fuel_combustion_products (to size the
# radiating CO2 and H2O). One definition, two consumers.
# ======================================================
FUEL_COMPOSITION = {
    "C": 0.88,
    "H": 0.04,
    "O": 0.02,
    "S": 0.06,
}


def gas_mass_balance(
    fuel_rate_total,
    O2,
    eps=1e-12,
):
    # Hoisted to a module constant (FUEL_COMPOSITION) so the
    # radiation closure can derive the combustion products' CO2 and
    # H2O from the SAME composition this balance burns, rather than
    # keeping a second copy that can drift out of step.
    fuel_composition = FUEL_COMPOSITION

    # ======================================================
    # MOLAR MASSES [kg/mol]
    # ======================================================
    M_C = 0.012011
    M_H = 0.001008
    M_O = 0.015999
    M_S = 0.03206
    M_O2 = 0.031998

    # Dry air oxygen mass fraction
    Y_O2_air = 0.232

    # ======================================================
    # FUEL MASS FRACTIONS
    # ======================================================
    w_C = fuel_composition["C"]
    w_H = fuel_composition["H"]
    w_O = fuel_composition["O"]
    w_S = fuel_composition["S"]

    # ======================================================
    # STOICHIOMETRIC O2 [mol/kg fuel]
    # ======================================================
    n_O2_st = (
        w_C / M_C
        + 0.25 * w_H / M_H
        + w_S / M_S
        - 0.5 * w_O / M_O
    )

    # ======================================================
    # STOICHIOMETRIC O2 [kg/kg fuel]
    # ======================================================
    m_O2_st = n_O2_st * M_O2

    # ======================================================
    # STOICHIOMETRIC AIR [kg/kg fuel]
    # ======================================================
    m_air_st = m_O2_st / Y_O2_air

    # ======================================================
    # DRY FLUE-GAS O2 TARGET
    # O2 = vol% dry O2
    # ======================================================
    O2_dry_target = O2 / 100.0

    # ======================================================
    # PRODUCT MOLES [mol/kg fuel]
    # ======================================================
    n_CO2 = w_C / M_C
    n_SO2 = w_S / M_S

    # ======================================================
    # DRY FLUE-GAS O2 FRACTION
    # ======================================================
    def dry_O2_fraction(lam):

        n_O2_excess = (lam - 1.0) * n_O2_st

        n_N2 = lam * n_O2_st * (79.0 / 21.0)

        n_dry = (
            n_CO2
            + n_SO2
            + n_O2_excess
            + n_N2
        )

        return n_O2_excess / (n_dry + eps)

    # ======================================================
    # SOLVE λ FROM DRY FLUE-GAS O2
    # ======================================================
    lam_low = 1.0
    lam_high = 3.0

    for _ in range(60):

        lam_mid = 0.5 * (lam_low + lam_high)

        if dry_O2_fraction(lam_mid) < O2_dry_target:
            lam_low = lam_mid
        else:
            lam_high = lam_mid

    lam = 0.5 * (lam_low + lam_high)

    # ======================================================
    # ACTUAL AIR FLOW
    # ======================================================
    m_air_per_kg_fuel = lam * m_air_st

    m_dot_air = (
        fuel_rate_total
        * m_air_per_kg_fuel
    )

    # ======================================================
    # TOTAL GAS MASS FLOW
    # ======================================================
    m_dot_g = (
        m_dot_air
        + fuel_rate_total
    )

    return m_dot_g


# ======================================================
# SUPERSEDED FOR THE ROTARY KILN by rotary_bed_motion below,
# which carries the correlation this one mis-states. Kept only
# because pyroprocess/precalciner/precalciner.py:130/:285 still
# calls it through solid_axial_velocity().
#
# What is wrong with it, stated once so the next reader does not
# have to re-derive it: Sullivan's correlation has sqrt(angle of
# repose) in the NUMERATOR and the inclination in DEGREES in the
# denominator, and has no fill-fraction term at all. This form
# dropped the repose angle, put tan(inclination) where degrees
# belong -- a factor of 180/pi = 57.3 at these angles -- and
# introduced a fill fraction the correlation never had. It also
# returns Sullivan's MINUTES to callers that consume seconds.
#
# It is left alone here rather than fixed in place because its
# only remaining caller is the precalciner, which is a vertical
# riser, not a rotating cylinder: a rotary-kiln transit
# correlation does not apply to it at all, and giving it the
# right velocity is a different question from fixing this one.
# Changing it here would move the calciner in the same commit
# that moves the kiln and make neither attributable.
# ======================================================
def residence_time(L, D, slope_deg, fill_fraction, rpm, eps):

    theta = np.deg2rad(slope_deg)

    tau = (
        1.77
        * L
        / (
            D
            * rpm
            * np.tan(theta)
            * (fill_fraction + eps)
        )
    )

    return tau


# ======================================================
# SOLID TRANSIT THROUGH A ROTARY KILN
#
# Sullivan, Maier & Ralston (1927), US Bureau of Mines TP 384 --
# the correlation the cement industry still sizes kilns with:
#
#   tau [min] = 1.77 * L * sqrt(theta) / (D * N * beta)
#
#     theta = dynamic angle of repose of the bed   [DEGREES]
#     beta  = kiln inclination                     [DEGREES]
#     N     = rotational speed                     [rpm]
#     L, D  = length and inside diameter           [any one unit]
#
# beta enters as a NUMBER OF DEGREES, not as tan(beta), and theta
# enters as the square root of a number of degrees. That is an
# empirical fit from 1927, not a dimensional statement, and it is
# the single easiest thing to get wrong here -- so it is checked
# rather than asserted. Three industry restatements of the same
# correlation, each folding a repose angle into the constant:
#
#   t = 11.2 L / (r D s),    s in DEGREES        (cemnet, kiln speed)
#   T = 11.4 L(ft) / (RPH * Dia(ft) * S),  S = ft/ft   (US BoM)
#   RT = 23 L / (rpm D SlopePct)                 (cemnet, SIMEQ)
#
# The second is quoted against the SLOPE AS A FRACTION and in
# revolutions per HOUR; converting it to metres and rpm gives
# 0.19 L/(D N tan beta), and 0.19 * 180/pi = 10.89. That it lands
# on the first form's 11.2 is not a coincidence -- 180/pi = 57.2958
# is exactly the small-angle conversion from tan(beta) to beta in
# degrees, so the two forms ARE the same correlation and the fact
# that they agree to 3% is the proof that beta is in degrees.
#
# Solving 1.77*sqrt(theta) for those constants gives theta = 40.0
# and 37.8 degrees respectively, and a cement-industry forum
# thread on the angle of repose states "for many raw material its
# about 40 deg". 1.77*sqrt(40) = 11.194 against cemnet's 11.2.
# The third form implies 55 degrees and is the outlier; it is a
# conservative shorthand and is not used.
#
# WHAT THIS REPLACES, and why it is not a refinement but a fix.
# The previous version closed residence_time() against mass
# continuity to eliminate the fill fraction:
#
#   tau = L sqrt(1.77 rho A / (D N tan(beta) m_dot_s))
#
# That derivation is sound arithmetic on an unsound premise.
# Sullivan's correlation ALREADY gives the transit time; it has no
# fill-fraction term to eliminate, so there was no loop to close.
# The fill fraction is an OUTPUT of the transit time through
# continuity, not an input to it, and that is how it is computed
# below. Continuity is still enforced -- it is just no longer
# asked to supply a number the correlation never wanted.
#
# The units are fixed here too: Sullivan returns MINUTES and every
# caller consumes seconds, so the conversion is explicit.
# ======================================================
SECONDS_PER_MINUTE = 60.0

SULLIVAN_C = 1.77


def rotary_bed_motion(
    L,
    D,
    slope_deg,
    rpm,
    repose_deg,
    m_dot_s,
    rho_bulk,
    A_cross,
    eps,
):

    if min(L, D, rpm, m_dot_s, rho_bulk, A_cross) <= 0.0:
        raise ValueError(
            "L, D, rpm, m_dot_s, rho_bulk and A_cross must be > 0, got "
            f"L={L}, D={D}, rpm={rpm}, m_dot_s={m_dot_s}, "
            f"rho_bulk={rho_bulk}, A_cross={A_cross}"
        )

    if slope_deg <= 0.0:
        raise ValueError(
            f"slope_deg must be a positive inclination, got {slope_deg}"
        )

    # The correlation is a fit over granular solids; outside this
    # the sqrt(theta) grouping is an extrapolation and the caller
    # should know rather than be given a number.
    if not (15.0 <= repose_deg <= 55.0):
        raise ValueError(
            "repose_deg outside the granular range the Sullivan "
            f"correlation was fitted over (15-55 deg), got {repose_deg}"
        )

    tau = SECONDS_PER_MINUTE * (
        SULLIVAN_C
        * L
        * np.sqrt(repose_deg)
        / (D * rpm * slope_deg)
    )

    u_s = L / (tau + eps)

    # Continuity, and now nothing but continuity: the hold-up the
    # transit time implies, expressed as a cross-section fraction.
    fill_fraction = m_dot_s / (rho_bulk * u_s * A_cross)

    if not (0.0 < fill_fraction < 1.0):
        raise ValueError(
            "bed fill fraction out of range: "
            f"{fill_fraction} (tau={tau}, u_s={u_s})"
        )

    return tau, u_s, fill_fraction


def solid_axial_velocity(L, D, slope_deg, fill_fraction, rpm, eps):

    tau = residence_time(
        L,
        D,
        slope_deg,
        fill_fraction,
        rpm,
        eps,
    )

    return L / (tau + eps)


def gas_axial_velocity(m_dot_g, rho_g, A_cross, eps):

    return m_dot_g / (rho_g * A_cross + eps)


# ======================================================
# SOLID TRANSPORT IN SUSPENSION
#
# For the equipment that does NOT rotate and is NOT a packed bed:
# the precalciner riser and the cyclone preheater's ducts. In both
# the meal is carried by the process gas, so its velocity is the
# gas velocity less the slip the particle's own weight costs it,
#
#   u_s = u_g - u_t
#
# and the suspension density follows from continuity afterwards,
# exactly as the kiln's bed fill does. There is no fill fraction
# to configure and no correlation: this is transport.
#
# u_t is the terminal settling velocity. Cement raw meal is
# ground to ~12-14 % residue on 90 um, so the particles are tens
# of microns and the particle Reynolds number is far below 1 --
# Stokes' law, which the function CHECKS rather than assumes:
#
#   u_t = (rho_p - rho_g) g d_p^2 / (18 mu)
#
# NOTE WHICH DENSITY. rho_p is the PARTICLE density, ~2700 kg/m3
# for limestone and clay, not the ~1100 kg/m3 BULK density the
# zones carry as `rho_s`. Bulk density already contains the void
# fraction of a settled heap, which is meaningless for a particle
# falling through gas, and using it here would understate the
# slip by a factor of 2.5.
#
# The slip turns out to be tiny -- fractions of a percent of u_g
# for meal-sized particles -- which is the physical content of
# "pneumatic conveying": the meal goes where the gas goes. That
# is why these vessels hold their solids for SECONDS while a
# rotary kiln holds its bed for half an hour, and it is the whole
# distinction the packed-bed treatment erased.
# ======================================================
G_ACCEL = 9.80665      # m/s2


def stokes_terminal_velocity(d_p, rho_p, rho_g, mu):

    if min(d_p, rho_p, rho_g, mu) <= 0.0:
        raise ValueError(
            "d_p, rho_p, rho_g and mu must be > 0, got "
            f"d_p={d_p}, rho_p={rho_p}, rho_g={rho_g}, mu={mu}"
        )

    if rho_p <= rho_g:
        raise ValueError(
            "a particle lighter than the gas does not settle: "
            f"rho_p={rho_p}, rho_g={rho_g}"
        )

    u_t = (rho_p - rho_g) * G_ACCEL * d_p ** 2 / (18.0 * mu)

    # Stokes' law holds for Re_p < 1; past that the drag is no
    # longer linear in velocity and this expression overstates
    # u_t. Checked, not assumed, because d_p is configurable.
    reynolds = rho_g * u_t * d_p / mu

    if reynolds >= 1.0:
        raise ValueError(
            "particle Reynolds number "
            f"{reynolds:.3f} >= 1: outside Stokes' law, where this "
            "expression overstates the settling velocity. A "
            "correlation valid in the intermediate regime is "
            "needed, not a wider tolerance."
        )

    return u_t


def suspension_transport(
    m_dot_g,
    m_dot_s,
    rho_g,
    A_cross,
    d_p,
    rho_particle,
    mu,
    eps,
):
    """(u_s, u_g, u_t, solids_volume_fraction) for a vessel whose
    solids are carried by the gas."""

    if A_cross <= 0.0 or m_dot_s <= 0.0:
        raise ValueError(
            f"A_cross and m_dot_s must be > 0, got A_cross={A_cross}, "
            f"m_dot_s={m_dot_s}"
        )

    u_g = gas_axial_velocity(m_dot_g, rho_g, A_cross, eps)
    u_t = stokes_terminal_velocity(d_p, rho_particle, rho_g, mu)

    u_s = u_g - u_t

    if u_s <= 0.0:
        raise ValueError(
            "the gas cannot carry the solids upward: "
            f"u_g={u_g:.4f} m/s against a terminal velocity of "
            f"{u_t:.4f} m/s. The vessel would fill, which is a "
            "statement about the plant, not a number to clamp."
        )

    # Continuity, the same statement rotary_bed_motion makes about
    # the kiln's bed -- on the PARTICLE density, because this is a
    # dispersion of individual particles, not a settled heap.
    solids_fraction = m_dot_s / (rho_particle * u_s * A_cross)

    if not (0.0 < solids_fraction < 1.0):
        raise ValueError(
            "suspension solids fraction out of range: "
            f"{solids_fraction} (u_s={u_s}, u_g={u_g})"
        )

    return u_s, u_g, u_t, solids_fraction

# ======================================================
# COMBUSTION
# ======================================================
def combustion_efficiency(O2, O2_opt, O2_sigma2):

    return np.exp(
        -((O2 - O2_opt) ** 2) / O2_sigma2
    )
    
def fuel_heat_release(
    fuel_rate_total,     # kg/s
    O2,
    O2_opt,
    O2_sigma2,
    LHV,
    inputs,
    eps,
):

    # ======================================================
    # PETCOKE-ONLY FUEL MODEL
    # ======================================================

    Q_petcoke = (
        fuel_rate_total
        * LHV["petcoke"]
    )

    # ======================================================
    # COMBUSTION EFFICIENCY
    # ======================================================

    eta = combustion_efficiency(
        O2,
        O2_opt,
        O2_sigma2,
    )

    # ======================================================
    # TOTAL HEAT RELEASE
    # ======================================================

    Q_burning = (
        eta
        * Q_petcoke
    )

    return Q_petcoke, Q_burning


def combustion_axial_distribution(
    Q_total,
    weights,
):
    """
    Toplam yanma ısısının eksenel ağırlıklara göre dağıtılması.

    Q_total : toplam yanma ısısı [W]
    weights : hücre ağırlıkları [-]

    Returns
    -------
    q_cell : hücre başına yanma ısısı [W]
    """

    weights = np.asarray(weights, dtype=float)

    if len(weights) == 0:
        raise ValueError("Combustion weights cannot be empty.")

    if np.any(weights < 0.0):
        raise ValueError("Combustion weights must be non-negative.")

    weight_sum = np.sum(weights)

    if weight_sum <= 0.0:
        raise ValueError("Combustion weights must have a positive sum.")

    weights = weights / weight_sum

    q_cell = Q_total * weights

    return q_cell

# ======================================================
# HEAT TRANSFER
# ======================================================

"""
k_eff is an effective radiation scaling factor representing
unresolved radiative effects, including view factors,
participating media, gas absorption, flame radiation,
and other complex heat transfer mechanisms.

FAZ 5 -- "burning" and "transition" are GONE from both dicts below.

Those two zones are rotating cylinders and now resolve all three
coefficients from the local state in physics.kiln_closures. The
entries are deleted rather than left unused so that a call which
still asks for them fails loudly instead of silently falling back
to a constant.

What the deleted entries were, and why they could not stay:
k_eff = 0.005 made ZONE_RAD_COEFF equal to 0.46% of eps * sigma --
a 200-fold suppression. At the burning zone's own working point
that put radiation at 1.0% of the gas -> bed path where the
physical share is 79-86%, so the model was carrying essentially
all of its kiln heat on a mechanism that does not carry it.

The remaining three zones keep these constants ON PURPOSE. A
cyclone string and a grate cooler are not rotating cylinders, so
the rotary-kiln correlations that replaced the constants do not
apply to them; they are Faz 6 work, not Faz 5.
"""

ZONE_RAD_CONFIG = {

    "calciner":{
        "eps":0.82,
        "k_eff":0.005,
    },

    "preheater":{
        "eps":0.70,
        "k_eff":0.005,
    },

    "cooler":{
        "eps":0.55,
        "k_eff":0.005,
    },
}

# See the note above ZONE_RAD_CONFIG: "burning" (hv_gs 700, hv_gw
# 180, hv_ws 220) and "transition" (450 / 150 / 180) were removed by
# Faz 5 and are resolved per cell instead.
ZONE_HT_CONFIG = {
    "calciner": {
        "hv_gs": 350.0,
        "hv_gw": 120.0,
        "hv_ws": 150.0,
    },
    "preheater": {
        "hv_gs": 220.0,
        "hv_gw": 90.0,
        "hv_ws": 110.0,
    },
    "cooler": {
        "hv_gs": 180.0,
        "hv_gw": 70.0,
        "hv_ws": 90.0,
    },
}


sigma = 5.670374419e-8


# ======================================================
# PER-ZONE RADIATION COEFFICIENT
#
# k_eff * eps * sigma is fixed per zone, but radiation() was
# re-reading ZONE_RAD_CONFIG and redoing the product on every
# one of its ~516k calls per steady-state solve. Precomputed
# here with the same left-to-right grouping the inline
# expression used, so the product is bit-identical.
# ======================================================
ZONE_RAD_COEFF = {
    _zone: _cfg["k_eff"] * _cfg["eps"] * sigma
    for _zone, _cfg in ZONE_RAD_CONFIG.items()
}


def radiation(T1, T2, zone, area=1.0):
    """ Stefan–Boltzmann radiation model with zone-dependent tuning."""
    

    q_rad = ZONE_RAD_COEFF[zone] * area * (T1**4 - T2**4)


    return q_rad


def heat_transfer(Tg, Ts, Tw, hv_gs, hv_gw, hv_ws, a_gs, a_gw, a_ws, zone=None):

    # ======================================================
    # CONVECTION
    # ======================================================

    q_gs_conv = hv_gs * a_gs * (Tg - Ts)
    q_gw_conv = hv_gw * a_gw * (Tg - Tw)
    q_ws_conv = hv_ws * a_ws * (Ts - Tw)

    # ======================================================
    # RADIATION (STEFAN–BOLTZMANN)
    # ======================================================
    q_gs_rad = radiation(Tg, Ts, zone, area=a_gs)
    q_gw_rad = radiation(Tg, Tw, zone, area=a_gw)
    q_ws_rad = radiation(Ts, Tw, zone, area=a_ws)

    # ======================================================
    # TOTAL HEAT TRANSFER
    # ======================================================
    q_gs = q_gs_conv + q_gs_rad
    q_gw = q_gw_conv + q_gw_rad
    q_ws = q_ws_conv + q_ws_rad

    

    return q_gs, q_gw, q_ws

    
# ======================================================
# GEOMETRY
# ======================================================
def kiln_geometry(D, L, N):

    # Cross-sectional area (m²)
    A_cross = np.pi * D**2 / 4.0

    # Total kiln volume (m³)
    V_total = A_cross * L

    # Computational cell volume (m³)
    V_cell = V_total / N

    return (
        A_cross,
        V_total,
        V_cell,
    )
# ======================================================
# WALL GEOMETRY
# ======================================================
def wall_geometry(
    D,
    L,
    N,
    V_cell,
    refractory_thickness=0.05,
):

    # Kiln inner perimeter (m)
    wall_perimeter = np.pi * D

    # Total inner wall area (m²)
    A_wall_total = wall_perimeter * L

    # Wall area per computational cell (m²)
    A_wall_cell = A_wall_total / N

    # Gas-wall interfacial area density (m²/m³)
    a_gw = A_wall_cell / V_cell

    # Refractory wall volume (m³)
    V_wall = A_wall_total * refractory_thickness

    return (
        wall_perimeter,
        A_wall_total,
        A_wall_cell,
        a_gw,
        V_wall,
    )
    
# ======================================================
# INTERFACIAL AREAS
# ======================================================
def interfacial_areas(
    D,
    epsilon_bed,
    k_interfacial=1.0,
    d_particle=None,
):
    """
    a_gs is the PACKED-BED SPECIFIC SURFACE, 6(1-eps)/d_p, and d_p
    in it is the PARTICLE diameter. Callers that pass only `D`
    substitute the vessel diameter for it -- a dimensional
    substitution, not a correlation choice, and
    pyroprocess/burning/heat_transfer.py:133-138 already documents
    it in those words for the kiln, which replaced this call with
    bed_segment_geometry. `d_particle` lets a caller supply the
    real one without disturbing the zones that have not been
    revisited yet.

    a_ws is solid->WALL contact. That is a PERIMETER quantity,
    bounded by the vessel, and it is not a packed-bed specific
    surface -- so it stays tied to D whatever d_particle says.
    Scaling it with the particle size would put more wall contact
    area in the zone than the vessel has wall.

    With d_particle=None both come back exactly as before.
    """

    # The vessel-based density. Still what the wall contact is
    # built from, and what a_gs falls back to.
    vessel_base = (
        6.0
        * (1.0 - epsilon_bed)
        / D
    )

    if d_particle is None:
        a_gs_base = vessel_base
    else:
        a_gs_base = (
            6.0
            * (1.0 - epsilon_bed)
            / d_particle
        )

    a_gs = k_interfacial * a_gs_base

    # Wall-solid interfacial area density (m²/m³)
    a_ws = 0.6 * k_interfacial * vessel_base

    return (
        a_gs,
        a_ws,
    )

# ======================================================
# BED FILL FRACTION FROM HOLDUP
#
# Steady-state mass continuity of the solid stream through
# a cross-section: m_dot_s = rho_bulk * u_s * A_bed, with
# A_bed = fill_fraction * A_cross. A fill fraction outside
# [0, 1) means the inputs are physically inconsistent, so
# it is rejected rather than clamped.
# ======================================================
def fill_fraction_from_holdup(
    m_dot_s,     # kg/s
    rho_bulk,    # kg/m³
    u_s,         # m/s
    A_cross,     # m²
):

    if m_dot_s < 0.0:
        raise ValueError(f"m_dot_s must be >= 0 kg/s, got {m_dot_s}")

    if rho_bulk <= 0.0 or u_s <= 0.0 or A_cross <= 0.0:
        raise ValueError(
            "rho_bulk, u_s and A_cross must be > 0, got "
            f"rho_bulk={rho_bulk}, u_s={u_s}, A_cross={A_cross}"
        )

    fill_fraction = m_dot_s / (rho_bulk * u_s * A_cross)

    if fill_fraction >= 1.0:
        raise ValueError(
            f"solid holdup exceeds the kiln cross-section: "
            f"fill_fraction={fill_fraction}"
        )

    return fill_fraction

# ======================================================
# BED SEGMENT GEOMETRY
#
# Rotary-kiln bed as a circular segment of the cross-section
# (flat bed surface, D = inner diameter). theta is the central
# angle the bed subtends:
#
#   fill_fraction = (theta - sin theta) / (2 pi)
#
# Area densities per unit kiln volume (m²/m³), A = pi D² / 4:
#
#   a_gs = D sin(theta/2) / A          bed surface (chord)
#   a_ws = (theta D / 2) / A           wall covered by the bed
#   a_gw = ((2 pi - theta) D / 2) / A  wall exposed to the gas
#
# a_ws + a_gw = 4 / D: the wall area is split, never created.
# D_e = 4 A_gas / P_gas is the hydraulic diameter of the gas
# passage (exposed arc + bed chord).
# ======================================================
def bed_segment_geometry(
    D,               # m
    fill_fraction,   # -
    tol=1e-14,
):

    if D <= 0.0:
        raise ValueError(f"D must be > 0 m, got {D}")

    if not (0.0 <= fill_fraction < 1.0):
        raise ValueError(
            f"fill_fraction must be in [0, 1), got {fill_fraction}"
        )

    # theta - sin(theta) is monotonic on [0, 2 pi]
    # (derivative 1 - cos(theta) >= 0), so bisection is exact
    # to tol and cannot pick a wrong root.
    target = 2.0 * np.pi * fill_fraction

    lo = 0.0
    hi = 2.0 * np.pi

    while hi - lo > tol:

        mid = 0.5 * (lo + hi)

        if mid - np.sin(mid) < target:
            lo = mid
        else:
            hi = mid

    theta = 0.5 * (lo + hi)

    A_cross = np.pi * D**2 / 4.0

    chord = D * np.sin(0.5 * theta)
    arc_covered = 0.5 * theta * D
    arc_exposed = 0.5 * (2.0 * np.pi - theta) * D

    a_gs = chord / A_cross
    a_ws = arc_covered / A_cross
    a_gw = arc_exposed / A_cross

    A_gas = (1.0 - fill_fraction) * A_cross
    P_gas = arc_exposed + chord

    D_e = 4.0 * A_gas / P_gas

    return (
        theta,
        a_gs,
        a_ws,
        a_gw,
        D_e,
    )

# ======================================================
# COVERED WALL -> BED CONTACT HEAT TRANSFER
#
# Extended penetration theory (Li et al., Chem. Eng. Technol.
# 2005): a bed element touches the covered wall for the
# contact time t_c = theta / omega, during which heat
# penetrates the bed as into a semi-infinite solid. Averaged
# over t_c this gives
#
#   h_pen = 2 sqrt(k_b rho_b cp_b / (pi t_c))
#
# in series with the gas gap between the wall and the first
# particle layer, chi d_p / k_g:
#
#   h_ws = 1 / (chi d_p / k_g + 1 / h_pen),  0.096 < chi < 0.198
#
# chi outside its fitted range is rejected, not clamped.
# ======================================================
CONTACT_GAP_CHI_RANGE = (0.096, 0.198)


def wall_bed_contact_coefficient(
    theta,     # rad, bed central angle (bed_segment_geometry)
    rpm,       # 1/min
    k_b,       # W/(m K), effective bed conductivity
    rho_b,     # kg/m³, bed bulk density
    cp_b,      # J/(kg K)
    d_p,       # m, particle diameter
    k_g,       # W/(m K), gas conductivity in the gap
    chi,       # -, gas gap thickness / d_p
):

    if theta <= 0.0 or rpm <= 0.0:
        raise ValueError(
            f"theta and rpm must be > 0, got theta={theta}, rpm={rpm}"
        )

    if min(k_b, rho_b, cp_b, d_p, k_g) <= 0.0:
        raise ValueError("k_b, rho_b, cp_b, d_p and k_g must be > 0")

    chi_min, chi_max = CONTACT_GAP_CHI_RANGE

    if not (chi_min <= chi <= chi_max):
        raise ValueError(
            f"chi must be in [{chi_min}, {chi_max}], got {chi}"
        )

    omega = 2.0 * np.pi * rpm / 60.0    # rad/s

    t_contact = theta / omega           # s

    h_pen = 2.0 * np.sqrt(
        k_b * rho_b * cp_b / (np.pi * t_contact)
    )

    R_gap = chi * d_p / k_g

    return 1.0 / (R_gap + 1.0 / h_pen)
