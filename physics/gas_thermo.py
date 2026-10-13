"""
Composition-aware ideal-gas enthalpy from NIST species data.

physics.cp_gas / h_gas is ONE representative combustion-gas curve
applied to every gas in the plant. Measured against NIST (scratchpad
props_check.py, 13 Oct 2026) it runs +5..10 % on dry AIR at every
temperature (+6.7 % at 1400 K) -- and the cooler is pure air -- and
+4..11 % on the plant's flue gases below 800 K, while it is within
+-3 % on hot flue gas above 1000 K, which is what it was built for.

Here a gas is an ideal mixture of N2, O2, Ar, CO2 and H2O:

    h(T, w) = sum_i w_i h_i(T),   cp(T, w) = sum_i w_i cp_i(T)

with w the MASS fractions and h_i the NIST Shomate fits (Chase,
NIST-JANAF Thermochemical Tables, 4th ed., 1998, as served by the
NIST Chemistry WebBook). SO2 from the fuel sulphur is booked as CO2
mass: at < 0.5 vol% its Cp difference from CO2 is far below the
other approximations here.

THE MIXTURE IS ONE POLYNOMIAL. Shomate is linear in its
coefficients, so a mixture's coefficients are the mass-weighted sum
of the species' (each divided by its molar mass) on the union of
the species' temperature segments. A GasMixture is built once per
composition and every h / cp call is then one polynomial, the same
cost as the old closure.

SI throughout: T in K, h in J/kg relative to T_ref, cp in J/(kg K).
"""

import bisect
import functools
import math

import numpy as np


# ======================================================
# SPECIES DATA
#
# Shomate: with t = T / 1000,
#
#   Cp       = A + B t + C t^2 + D t^3 + E / t^2        [J/(mol K)]
#   H - H298 = A t + B t^2/2 + C t^3/3 + D t^4/4 - E/t + F - H
#                                                        [kJ/mol]
#
# Each species is a list of (T_upper, (A, B, C, D, E, F - H)); a
# segment applies below its T_upper, the last one above everything.
# Below a species' lowest NIST range (N2/O2 100 K, CO2 298 K, H2O
# 500 K) its first segment is extrapolated; the twin's gases do
# not go below ~290 K, and gas-phase H2O at 290-500 K is a
# minority species in the preheater exhaust only.
#
# Argon is monatomic, Cp = 5/2 R = 20.786 J/(mol K) at all T.
#
# Checked against the NIST tables in tests/test_gas_thermo.py.
# ======================================================

MOLAR_MASS = {           # kg/mol
    "N2": 0.0280134,
    "O2": 0.0319988,
    "Ar": 0.039948,
    "CO2": 0.0440095,
    "H2O": 0.01801528,
}

SPECIES = tuple(MOLAR_MASS)

_SHOMATE = {
    "N2": [
        (500.0, (28.98641, 1.853978, -9.647459, 16.63537, 0.000117, -8.671914)),
        (2000.0, (19.50583, 19.88705, -8.598535, 1.369784, 0.527601, -4.935202)),
        (math.inf, (35.51872, 1.128728, -0.196103, 0.014662, -4.553760, -18.97091)),
    ],
    "O2": [
        (700.0, (31.32234, -20.23531, 57.86644, -36.50624, -0.007374, -8.903471)),
        (2000.0, (30.03235, 8.772972, -3.988133, 0.788313, -0.741599, -11.32468)),
        (math.inf, (20.91111, 10.72071, -2.020498, 0.146449, 9.245722, 5.337651)),
    ],
    "Ar": [
        (math.inf, (20.786, 0.0, 0.0, 0.0, 0.0, -20.786 * 0.29815)),
    ],
    "CO2": [
        (1200.0, (24.99735, 55.18696, -33.69137, 7.948387, -0.136638, -403.6075 + 393.5224)),
        (math.inf, (58.16639, 2.720074, -0.492289, 0.038844, -6.447293, -425.9186 + 393.5224)),
    ],
    "H2O": [
        (1700.0, (30.09200, 6.832514, 6.793435, -2.534480, 0.082139, -250.8810 + 241.8264)),
        (math.inf, (41.96426, 8.622053, -1.499780, 0.098119, -11.15764, -272.1797 + 241.8264)),
    ],
}

# Dry air by mass (N2 78.08, O2 20.95, Ar 0.93, CO2 0.04 vol%).
AIR = {
    "N2": 0.7552,
    "O2": 0.2314,
    "Ar": 0.0129,
    "CO2": 0.0005,
    "H2O": 0.0,
}

T_REF = 298.15

# Union of every species' segment edges: on each interval between
# them, every species is on one fixed segment.
_EDGES = sorted(
    {upper for segs in _SHOMATE.values() for upper, _ in segs if upper < math.inf}
)


def _species_coeffs(name, T_mid):
    for upper, coeffs in _SHOMATE[name]:
        if T_mid < upper:
            return coeffs
    return _SHOMATE[name][-1][1]


# ======================================================
# MIXTURE
# ======================================================

class GasMixture:
    """An ideal gas mixture of fixed mass fractions.

    Built once per composition; h, cp and the inverse are then one
    polynomial on the interval T falls in."""

    def __init__(self, mass_fractions):

        w = {s: float(mass_fractions.get(s, 0.0)) for s in SPECIES}

        unknown = set(mass_fractions) - set(SPECIES)
        if unknown:
            raise ValueError(f"unknown gas species {sorted(unknown)}")

        if any(v < 0.0 for v in w.values()):
            raise ValueError(f"negative mass fraction in {w}")

        total = sum(w.values())
        if not total > 0.0:
            raise ValueError("a gas mixture needs a positive total mass")

        self.w = {s: v / total for s, v in w.items()}

        # Per interval, sum_i w_i coeffs_i / M_i: J/(kg K) for the
        # Cp part, kJ/kg for the enthalpy part (x1e3 below).
        lows = [-math.inf] + _EDGES
        highs = _EDGES + [math.inf]
        self._coeffs = []

        for lo, hi in zip(lows, highs):
            # Any point inside the interval picks the same segments.
            T_mid = hi - 1.0 if lo == -math.inf else lo + 1.0
            mix = [0.0] * 6
            for s in SPECIES:
                if self.w[s] == 0.0:
                    continue
                c = _species_coeffs(s, T_mid)
                f = self.w[s] / MOLAR_MASS[s]
                for k in range(6):
                    mix[k] += f * c[k]
            self._coeffs.append(tuple(mix))

        # NIST's segment fits do not meet exactly: H steps by up to
        # a few tens of J/kg at an edge. Shift each upper interval's
        # constant so H is continuous there; otherwise an enthalpy
        # read at an edge inverts a hundredth of a kelvin off.
        for k, edge in enumerate(_EDGES):
            step = self._H_on(k, edge) - self._H_on(k + 1, edge)
            A, B, C, D, E, K = self._coeffs[k + 1]
            self._coeffs[k + 1] = (A, B, C, D, E, K + step / 1000.0)

        self._h_ref = self._H(T_REF)

    def _H_on(self, k, T):
        A, B, C, D, E, K = self._coeffs[k]
        t = T * 1e-3
        return 1000.0 * (
            t * (A + t * (0.5 * B + t * (C / 3.0 + t * 0.25 * D)))
            - E / t + K
        )

    # ------------------------------------------------------
    # internals: absolute H (J/kg, H(298.15 K) ~ 0) and Cp
    # ------------------------------------------------------

    # Plain-Python scalar arithmetic: these run inside the per-cell
    # assembly loops, where numpy's per-call overhead dominates.

    def _H(self, T):
        A, B, C, D, E, K = self._coeffs[bisect.bisect_right(_EDGES, T)]
        t = T * 1e-3
        return 1000.0 * (
            t * (A + t * (0.5 * B + t * (C / 3.0 + t * 0.25 * D)))
            - E / t + K
        )

    def _cp(self, T):
        A, B, C, D, E, _ = self._coeffs[bisect.bisect_right(_EDGES, T)]
        t = T * 1e-3
        return A + t * (B + t * (C + t * D)) + E / (t * t)

    # ------------------------------------------------------
    # public
    # ------------------------------------------------------

    def h(self, T, T_ref=T_REF):
        """Sensible enthalpy [J/kg] at T relative to T_ref."""

        H_ref = self._h_ref if T_ref == T_REF else self._H(T_ref)

        if isinstance(T, float):
            return self._H(T) - H_ref

        T = np.asarray(T, dtype=float)
        out = np.vectorize(self._H, otypes=[float])(T)
        return out - H_ref

    def cp(self, T):
        """Isobaric heat capacity [J/(kg K)] at T, dh/dT."""

        if isinstance(T, float):
            return self._cp(T)

        T = np.asarray(T, dtype=float)
        return np.vectorize(self._cp, otypes=[float])(T)

    def T_from_h(self, h_target, T_ref, T_min, T_max):
        """Inverse of h(T, T_ref) on [T_min, T_max]; raises outside it.

        Bracketed Newton, the pattern of physics.T_gas_from_h: the
        enthalpy is monotone (Cp > 0), so the bracket never loses
        the root, and Newton steps that leave it fall back to
        bisection."""

        h_target = float(h_target)

        lo, hi = float(T_min), float(T_max)
        f_lo = self.h(lo, T_ref) - h_target
        f_hi = self.h(hi, T_ref) - h_target

        if f_lo > 0.0 or f_hi < 0.0:
            raise ValueError(
                f"gas enthalpy {h_target:.6g} J/kg is outside "
                f"[{T_min}, {T_max}] K for this mixture"
            )

        T = lo + (hi - lo) * (-f_lo) / (f_hi - f_lo)

        for _ in range(100):
            f = self.h(T, T_ref) - h_target
            if f > 0.0:
                hi = T
            else:
                lo = T
            step = f / self._cp(T)
            T_new = T - step
            if not (lo < T_new < hi):
                T_new = 0.5 * (lo + hi)
            if abs(T_new - T) <= 1e-12 * T:
                return T_new
            T = T_new

        return T


# The one mixture most of the plant's air streams use.
AIR_MIXTURE = GasMixture(AIR)


# ======================================================
# COMPOSITION FROM MASS FLOWS
#
# Species mass flows [kg/s] as dicts over SPECIES. Built from the
# flows the twin already carries (air, fuel, released CO2 / H2O);
# no species balance is solved.
# ======================================================

def air(m_dot):
    """Species flows of m_dot [kg/s] of dry air."""

    return {s: AIR[s] * float(m_dot) for s in SPECIES}


def burned(m_dot_air, m_dot_fuel, fuel_composition):
    """Species flows after m_dot_fuel burns completely in m_dot_air
    of dry air. See burn_in."""

    return burn_in(air(m_dot_air), m_dot_fuel, fuel_composition)


def burn_in(flows, m_dot_fuel, fuel_composition):
    """Species flows after m_dot_fuel burns completely in the gas
    `flows` (a species dict) -- the calciner burns its fuel in kiln
    gas plus tertiary air, not in fresh air.

    C -> CO2, H -> H2O, S -> SO2 (booked as CO2 mass), fuel O
    offsets the O2 demand. Mass is conserved: the result sums to
    the gas plus m_dot_fuel. Raises if the gas cannot burn the fuel."""

    m_fuel = float(m_dot_fuel)

    # Element molar masses; the product masses are built from the
    # SAME ones, so the burn conserves mass to the last bit.
    M_C, M_H, M_S, M_O = 0.012011, 0.001008, 0.032065, 0.015999

    C = m_fuel * fuel_composition["C"]
    H = m_fuel * fuel_composition["H"]
    S = m_fuel * fuel_composition["S"]
    O = m_fuel * fuel_composition["O"]

    n_O2 = C / M_C + H / (4.0 * M_H) + S / M_S - O / (2.0 * M_O)
    O2_demand = n_O2 * 2.0 * M_O

    m_CO2 = C / M_C * (M_C + 2.0 * M_O)
    m_H2O = H / (2.0 * M_H) * (2.0 * M_H + M_O)
    m_SO2 = S / M_S * (M_S + 2.0 * M_O)

    flows = add(flows)

    if O2_demand > flows["O2"] * (1.0 + 1e-12):
        raise ValueError(
            f"{flows['O2']:.6g} kg/s of O2 cannot burn {m_fuel:.6g} kg/s of fuel"
        )

    flows["O2"] -= O2_demand
    flows["CO2"] += m_CO2 + m_SO2
    flows["H2O"] += m_H2O

    # The fuel's mass not in C, H, S, O (ash) stays out of the gas.
    return flows


def add(*flows):
    """Sum of species flow dicts."""

    return {s: sum(float(f.get(s, 0.0)) for f in flows) for s in SPECIES}


def mixture(flows):
    """GasMixture of a species flow dict."""

    return GasMixture(flows)


# ======================================================
# A ZONE'S GAS, CELL BY CELL
#
# The stream enters a zone with species flows `inlet` and picks
# up what each cell's bed releases. Cell i's OUTGOING gas holds
# the inlet plus every release from the inlet cell up to and
# including i, in the flow direction: a suffix sum when the gas
# runs N-1 -> 0 (the kiln, counter-current to the bed), a prefix
# sum when it runs 0 -> N-1 (the calciner riser).
#
# A cell's inflow face is its upstream neighbour's outflow face,
# so a row that rates the inflow with the upstream cell's mixture
# and the outflow with its own telescopes exactly over the zone.
# ======================================================

def cell_species(inlet, released_cells, reverse):
    """Per-cell outgoing species flows [kg/s].

    inlet          : species dict entering the zone
    released_cells : list of N species dicts, what each cell adds
    reverse        : True when the gas runs N-1 -> 0
    """

    N = len(released_cells)
    order = range(N - 1, -1, -1) if reverse else range(N)

    out = [None] * N
    running = add(inlet)

    for i in order:
        running = add(running, released_cells[i])
        out[i] = running

    return out


CO2_GAS = GasMixture({"CO2": 1.0})
H2O_GAS = GasMixture({"H2O": 1.0})


# ======================================================
# CACHED MIXTURES
#
# Building a GasMixture is ~30 us; the preheater's node loops ask
# for the same few compositions thousands of times per sweep.
# Keyed on the mass FRACTIONS rounded to 1e-12, far below any
# property difference that could matter.
# ======================================================

@functools.lru_cache(maxsize=4096)
def _mixture_from_key(key):
    return GasMixture(dict(key))


def mixture_cached(flows):
    """GasMixture of a species flow dict, memoised on its fractions."""

    total = sum(float(flows.get(s, 0.0)) for s in SPECIES)

    if not total > 0.0:
        raise ValueError("a gas mixture needs a positive total mass")

    key = tuple(
        (s, round(float(flows.get(s, 0.0)) / total, 12)) for s in SPECIES
    )

    return _mixture_from_key(key)
