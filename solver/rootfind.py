"""A bracketed scalar root find for residuals that are
expensive and can FAIL.

Why not scipy.optimize.brentq: scipy is absent from
requirements.txt and from every source file in this repo, so
importing it would add an undeclared dependency. It is also
the wrong tool here. brentq has no hook for an evaluation that
raises -- and evaluations here DO raise, because one residual
is a whole plant solve and the plant has feasibility limits
(the cooler air split, the preheater's counter-current fixed
point, the shell's hot-face guard). Under brentq the exception
propagates and every evaluation already paid for is lost.

The in-repo precedents are physics.physics.gas_mass_balance,
which bisects the excess-air ratio against the dry stack O2
target, and physics.physics.T_gas_from_h, which is a bracketed
safeguarded Newton that degrades to bisection whenever a step
would leave the bracket. This follows both.

Illinois (modified regula falsi) rather than plain secant:
the secant can step outside the bracket, and this residual is
not guaranteed monotone. Illinois ALWAYS retains the bracket,
so a non-monotone patch or an infeasible point cannot lose it,
while still converging superlinearly (order ~1.44) -- 5 to 7
evaluations from a decent bracket, against ~40 for bisection
at the same tolerance. At 27 s to 900 s per evaluation that
difference is the whole cost of the solve.
"""

from dataclasses import dataclass, field


class _Infeasible:
    """Returned by a residual that could not be evaluated.

    A sentinel rather than None, NaN or a large number: NaN
    poisons the arithmetic silently, and a large number is a
    LIE about the residual that the root find would then chase.
    """

    def __repr__(self):
        return "INFEASIBLE"

    def __bool__(self):
        return False


INFEASIBLE = _Infeasible()


# Fraction of the remaining interval to step back when an
# endpoint or a trial point cannot be evaluated. The golden
# ratio's conjugate: retreating by this keeps the surviving
# interval self-similar, so repeated retreats do not collapse
# the bracket faster than they have to.
_RETREAT = 0.381966011250105


@dataclass
class RootResult:

    x: float
    residual: float
    converged: bool
    evaluations: int
    reason: str
    history: list = field(default_factory=list)


def _is_infeasible(value):
    return isinstance(value, _Infeasible)


def find_root(
    f,
    lo,
    hi,
    *,
    residual_tolerance,
    x_tolerance,
    max_evaluations=12,
    max_expansions=4,
    max_retreats=4,
):
    """
    Solve f(x) = 0 for x in [lo, hi].

    `f` returns a float, or INFEASIBLE if that x could not be
    evaluated at all. Both tolerances must be met to declare
    convergence: a small step with a large residual means the
    bracket collapsed on an infeasible edge, not on a root.

    Never raises on a failed solve -- it reports. A caller
    driving a physical model needs the evaluation history even
    when there is no root, because "no root in this bracket"
    is itself the finding.
    """

    lo = float(lo)
    hi = float(hi)

    if not (hi > lo):
        raise ValueError(
            f"bracket must satisfy hi > lo, got lo={lo}, hi={hi}"
        )

    if residual_tolerance <= 0.0 or x_tolerance <= 0.0:
        raise ValueError("tolerances must be > 0")

    history = []
    budget = {"n": 0}

    def evaluate(x):

        if budget["n"] >= max_evaluations:
            return None

        budget["n"] += 1
        value = f(x)
        history.append((x, value))
        return value

    def result(x, residual, converged, reason):
        return RootResult(
            x=float(x),
            residual=(
                float("nan")
                if residual is None or _is_infeasible(residual)
                else float(residual)
            ),
            converged=converged,
            evaluations=budget["n"],
            reason=reason,
            history=history,
        )

    # ======================================================
    # FEASIBLE ENDPOINTS
    #
    # An endpoint that cannot be evaluated is not a failure of
    # the solve, it is a statement about where the model lives.
    # Retreat it toward the interior rather than giving up.
    # ======================================================
    def secure_endpoint(x, toward):

        value = evaluate(x)

        for _ in range(max_retreats):

            if value is None:
                return x, value

            if not _is_infeasible(value):
                return x, value

            x = x + _RETREAT * (toward - x)
            value = evaluate(x)

        return x, value

    lo, f_lo = secure_endpoint(lo, hi)

    if f_lo is None or _is_infeasible(f_lo):
        return result(lo, f_lo, False, "lower end infeasible")

    hi, f_hi = secure_endpoint(hi, lo)

    if f_hi is None or _is_infeasible(f_hi):
        return result(hi, f_hi, False, "upper end infeasible")

    # An endpoint may already be the answer.
    for x, value in ((lo, f_lo), (hi, f_hi)):
        if abs(value) <= residual_tolerance:
            return result(x, value, True, "root at a bracket end")

    # ======================================================
    # BRACKET EXPANSION
    #
    # Same sign at both ends means the root, if any, is
    # outside. Grow geometrically -- but only outward from the
    # end whose residual is SMALLER, which is the direction the
    # residual is falling.
    # ======================================================
    expansions = 0

    while f_lo * f_hi > 0.0 and expansions < max_expansions:

        expansions += 1
        span = hi - lo

        if abs(f_lo) <= abs(f_hi):
            candidate = lo - 0.5 * span
            candidate, value = secure_endpoint(candidate, lo)

            if value is None or _is_infeasible(value):
                break

            lo, f_lo = candidate, value

        else:
            candidate = hi + 0.5 * span
            candidate, value = secure_endpoint(candidate, hi)

            if value is None or _is_infeasible(value):
                break

            hi, f_hi = candidate, value

        if abs(f_lo) <= residual_tolerance:
            return result(lo, f_lo, True, "root at a bracket end")

        if abs(f_hi) <= residual_tolerance:
            return result(hi, f_hi, True, "root at a bracket end")

    if f_lo * f_hi > 0.0:

        nearer = lo if abs(f_lo) <= abs(f_hi) else hi
        value = f_lo if nearer == lo else f_hi

        return result(
            nearer,
            value,
            False,
            "no sign change in the bracket -- "
            "the handle may have no authority here",
        )

    # ======================================================
    # ILLINOIS
    # ======================================================
    a, f_a = lo, f_lo
    b, f_b = hi, f_hi

    # Regula falsi STALLS when the two residuals differ by
    # orders of magnitude: the interpolated point crawls along
    # the flat side and the bracket barely shrinks. An
    # Arrhenius-shaped residual does exactly this -- measured,
    # exp(12(x-4)) over [0, 10] spans 1e31 and the plain method
    # never gets there. So the bracket width is watched, and a
    # step that fails to halve it forces a bisection step. Same
    # safeguard philosophy as T_gas_from_h: interpolate when it
    # is working, fall back the moment it is not.
    force_bisection = False

    while budget["n"] < max_evaluations:

        width = abs(b - a)
        denominator = f_b - f_a

        if force_bisection or denominator == 0.0:
            c = 0.5 * (a + b)
        else:
            c = (a * f_b - b * f_a) / denominator

        # A false-position step that leaves the bracket, or
        # lands on an endpoint, degrades to bisection too.
        low, high = (a, b) if a < b else (b, a)

        if not (low < c < high):
            c = 0.5 * (a + b)

        f_c = evaluate(c)

        if f_c is None:
            break

        # An infeasible trial point sits inside a bracket whose
        # ENDS are both feasible, so the model fails somewhere
        # in between. Step back toward the interior midpoint
        # instead of abandoning the bracket.
        retreats = 0

        while _is_infeasible(f_c) and retreats < max_retreats:

            retreats += 1
            c = 0.5 * (a + c)
            f_c = evaluate(c)

            if f_c is None:
                break

        if f_c is None:
            break

        if _is_infeasible(f_c):
            return result(
                c,
                None,
                False,
                "interior of the bracket is infeasible",
            )

        step = abs(c - b)

        if f_c * f_b < 0.0:
            a, f_a = b, f_b
        else:
            # The Illinois modification: halve the retained
            # endpoint's residual so one side cannot stall.
            f_a = 0.5 * f_a

        b, f_b = c, f_c

        force_bisection = abs(b - a) > 0.5 * width

        # The residual alone decides convergence: if it is
        # inside tolerance, this IS a root.
        if abs(f_b) <= residual_tolerance:
            return result(b, f_b, True, "converged")

        # x_tolerance is a STAGNATION check, not a second
        # convergence criterion. Steps this small with the
        # residual still out of tolerance mean the bracket
        # collapsed against something that is not a root --
        # an infeasible edge, or a discontinuity. Report it;
        # do not dress it up as convergence.
        if step <= x_tolerance:
            return result(
                b,
                f_b,
                False,
                "bracket collapsed without reaching the "
                "residual tolerance",
            )

    if abs(f_b) <= residual_tolerance:
        return result(b, f_b, True, "converged on residual only")

    return result(
        b,
        f_b,
        False,
        f"evaluation budget of {max_evaluations} exhausted",
    )
