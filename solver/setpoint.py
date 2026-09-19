"""Fuel as an outcome: solve the firing rate against a product
specification instead of reading it from the config.

`fuel.Fuel_rate_total` is a config constant, so nothing in the
model can reject a wrong value -- a surplus leaves as
temperature, wall loss and exhaust, and D11 has been reporting
1.53x over-fired against it. reporter.diagnostics says the
missing mechanism in its own words: a real kiln modulates fuel
against burning-zone temperature and free lime, "so nothing in
the model can push back on a wrong value."

WHAT THIS DOES AND DOES NOT TOUCH. It moves one REAL OPERATOR
HANDLE to meet a REAL PRODUCT SPECIFICATION. It does not touch
kinetics, closures, emissivities or any other model parameter.
Setting fuel to achieve a product spec is what an operator
does; leaving it pinned at an unjustified 2.5 kg/s is the less
defensible choice. That distinction is the whole licence for
this module and it should not be blurred later.

This is NOT an NMPC and could not be: the twin is steady state
-- no state vector, no time derivative, no horizon (the
simulation.dt/total_hours/chunk_hours config keys are dead).
An NMPC horizon would collapse to one step and what remains is
exactly this inverse solve.

COST. One residual evaluation is one full plant solve: ~27 s
at the committed kinetics, ~900 s (216 sweeps) with the
literature calcination rate. The bracketing below exists to
spend as few of those as possible.
"""

import contextlib
import io
from dataclasses import dataclass, field

from physics.physics import gas_mass_balance
from reporter import diagnostics
from solver.rootfind import INFEASIBLE, find_root


# ======================================================
# SPECIFICATIONS
# ======================================================
@dataclass(frozen=True)
class Spec:
    """A process specification and how to read it off a solved plant."""

    name: str
    read: callable
    target: float
    tolerance: float
    unit: str = ""


# Plants specify free lime in the 0.5-2.0% band (see
# diagnostics.FREE_LIME_BAND). 1.5% is the user's choice of
# ceiling. Note that a real plant TRIMS to roughly 1.0% and
# treats 1.5% as the limit, because sitting on a limit leaves
# no margin for a disturbance -- so this target is the
# conservative-fuel end of the acceptable range, not the
# middle of it.
DEFAULT_FREE_LIME_TARGET = 1.5

# 0.05 percentage points. The plant's own thermal convergence
# is 1e-3 K, so the residual carries far less noise than this;
# chasing a tighter free lime than ~0.01 pp would be bisecting
# solver noise rather than physics.
DEFAULT_FREE_LIME_TOLERANCE = 0.05


def free_lime_spec(
    target=DEFAULT_FREE_LIME_TARGET,
    tolerance=DEFAULT_FREE_LIME_TOLERANCE,
):
    """
    The specification a real kiln is actually trimmed against.

    MEASURED, and the reason this is the usable residual:
    on the committed kinetics free lime RISES with fuel
    (+6.64 pp per kg/s), because calcination still happens
    inside the kiln, so more fuel converts more CaCO3 to CaO
    while the slow clinkering reactions cannot consume it.
    Once calcination finishes upstream in the calciner, CaO
    arrives already released and fuel drives only clinkering,
    so the sign flips to the correct direction. Check which
    regime the plant is in before trusting a solve.
    """

    return Spec(
        name="free lime",
        read=lambda twin: diagnostics.free_lime(twin)["free_lime_pct"],
        target=float(target),
        tolerance=float(tolerance),
        unit="%",
    )


def clinker_temperature_spec(target=1723.0, tolerance=0.5):
    """
    Clinker discharge temperature, the other operator handle.

    MEASURED on the committed kinetics: dT/dfuel = -6.50 K per
    kg/s -- the WRONG SIGN, because the kiln's discharge end is
    its coldest section and is re-cooled against 541 K
    secondary air. There is no root. Kept because it is the
    quantity BOUNDS["clinker_kiln_outlet"] already bounds and
    it becomes usable once the cooler stream split is fixed,
    but do not reach for it before then.
    """

    return Spec(
        name="clinker discharge",
        read=lambda twin: diagnostics._solid_outlet_face(twin, "burning"),
        target=float(target),
        tolerance=float(tolerance),
        unit="K",
    )


# ======================================================
# FEASIBILITY: THE COOLER AIR SPLIT
#
# main._update_steady_state_mass_flow raises when
#   m_dot_vent_air = cooling_air_rate * m_clinker
#                    - m_secondary - m_tertiary  <  0
# and, expanding the two air terms,
#   m_secondary + m_tertiary
#     = m_dot_air * (1 - primary_air_fraction * kiln_fraction)
#
# m_dot_air is EXACTLY linear in the fuel rate: gas_mass_balance
# solves the excess-air ratio lambda against the dry stack O2
# target, which is a ratio and so carries no fuel rate, then
# returns fuel * lambda * m_air_st + fuel.
#
# The clinker flow is NOT independent of fuel, though -- measured
# 19.184 kg/s at 2.5 and 20.310 at 2.0, because more fuel means
# more calcination and so less solid mass. Clinker therefore
# FALLS as fuel rises and the constraint tightens faster than
# this linear form predicts. So the bound below is a cheap guide
# that costs no plant solve, not a guarantee; points beyond it
# are certainly infeasible, points inside it may still be.
# ======================================================
def air_per_kg_fuel(o2_target, eps=1.0e-12):
    """Combustion air per kg of fuel at the dry stack O2 target."""

    return gas_mass_balance(
        fuel_rate_total=1.0,
        O2=o2_target,
        eps=eps,
    ) - 1.0


def fuel_upper_bound(twin):
    """
    Largest fuel rate the cooler air split can feed, evaluated
    at the plant's CURRENT clinker flow. See the note above:
    an estimate, deliberately.
    """

    inputs = twin._last_inputs

    kiln_fraction = float(twin.burning.kiln_fuel_fraction)
    primary = float(twin.burning.primary_air_fraction)
    cooling_air_rate = float(
        twin.cooler.cooling_air_rate
    )
    clinker = float(twin.mass_flow.m_dot_clinker)

    per_kg = air_per_kg_fuel(inputs["O2"], twin.eps)

    demand_fraction = 1.0 - primary * kiln_fraction

    denominator = per_kg * demand_fraction

    if denominator <= 0.0 or clinker <= 0.0:
        return float("inf")

    return cooling_air_rate * clinker / denominator


# ======================================================
# THE SOLVE
# ======================================================
@dataclass
class SetpointResult:

    fuel: float
    achieved: float
    spec: Spec
    converged: bool
    evaluations: int
    reason: str
    history: list = field(default_factory=list)
    twin: object = None

    def __str__(self):
        return (
            f"{self.spec.name}: target {self.spec.target}"
            f"{self.spec.unit}, achieved {self.achieved:.4f}"
            f"{self.spec.unit} at Fuel_rate_total = "
            f"{self.fuel:.4f} kg/s "
            f"({self.evaluations} evaluations, {self.reason})"
        )


def _evaluate(twin, fuel, spec, max_iterations=None):
    """One residual: set the handle, solve the plant, read the spec.

    Every failure mode becomes INFEASIBLE rather than an
    exception, because a root find that loses its bracket to a
    raise has thrown away every evaluation it paid for. The
    raises that are genuinely reachable here are feasibility
    statements about the plant, not bugs: the cooler air split
    (main), the preheater's counter-current fixed point and the
    cooler's inner loop, the shell hot-face guard, and the bed
    fill-fraction range checks.
    """

    # step() reads _last_inputs, NOT cfg. Mutating cfg after
    # construction does nothing.
    twin._last_inputs["Fuel_rate_total"] = float(fuel)

    if max_iterations is not None:
        twin.cfg.setdefault("simulation", {})["max_iterations"] = int(
            max_iterations
        )

    try:
        with contextlib.redirect_stdout(io.StringIO()):
            twin.run(report=False, raise_on_nonconvergence=False)
    except Exception:
        return INFEASIBLE

    if not twin.converged:
        return INFEASIBLE

    try:
        return float(spec.read(twin)) - spec.target
    except Exception:
        return INFEASIBLE


def solve_fuel_rate(
    twin,
    spec=None,
    *,
    bracket=None,
    max_evaluations=12,
    max_iterations=None,
):
    """
    Move Fuel_rate_total until `spec` is met.

    Returns a SetpointResult. Never raises on a failed solve:
    "no root in this bracket" is itself a finding -- it says
    the handle has no authority over that specification in this
    plant -- and the caller needs the evaluation history to see
    it.

    The twin is driven WARM: run() performs no state reset, so
    each evaluation continues from the previous converged
    temperatures. That cannot move the fixed point (the
    relaxation blends are the identity there) but it does
    change the basin approached, so the published answer should
    be reproduced by a COLD solve at the returned fuel rate
    before it is written anywhere.
    """

    if spec is None:
        spec = free_lime_spec()

    if bracket is None:
        bracket = default_bracket(twin)

    lo, hi = bracket

    result = find_root(
        lambda fuel: _evaluate(twin, fuel, spec, max_iterations),
        lo,
        hi,
        residual_tolerance=spec.tolerance,
        # 1 g/s. Below this the fuel rate is not a meaningful
        # operating distinction.
        x_tolerance=1.0e-3,
        max_evaluations=max_evaluations,
    )

    achieved = (
        spec.target + result.residual
        if result.residual == result.residual
        else float("nan")
    )

    return SetpointResult(
        fuel=result.x,
        achieved=achieved,
        spec=spec,
        converged=result.converged,
        evaluations=result.evaluations,
        reason=result.reason,
        history=list(result.history),
        twin=twin,
    )


def default_bracket(twin, widen=(0.6, 1.6)):
    """
    An initial bracket that costs ZERO plant solves.

    Seeded from D11's specific-heat-consumption band. Using the
    SHC band as a SPECIFICATION would be circular -- it is a
    statement about fuel, which is the unknown -- but as a
    starting guess it is perfectly legitimate and it is the
    only cheap prior the model has. Capped by the cooler air
    split.
    """

    demand = diagnostics.thermal_demand_vs_supply(twin)

    potential = demand.get("clinker_potential")
    lo_shc, hi_shc = diagnostics.SHC_BAND

    if potential:
        lo = widen[0] * lo_shc * potential / diagnostics.FUEL_LHV
        hi = widen[1] * hi_shc * potential / diagnostics.FUEL_LHV
    else:
        current = float(twin._last_inputs["Fuel_rate_total"])
        lo, hi = widen[0] * current, widen[1] * current

    cap = fuel_upper_bound(twin)

    if cap < hi:
        hi = cap

    if not (hi > lo):
        hi = lo * 1.5

    return (lo, hi)
