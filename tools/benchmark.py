"""Steady-state performance benchmark for the twin.

    python3 -m tools.benchmark [--nodes N|cfg] [--profile K] [--reference PATH]
    python3 -m tools.benchmark --dynamic STEPS [--dt 10] [--fuel-step 1.05]

--dynamic times Twin.advance instead: real-time factor (simulated
over wall time, the steady solve not counted), sweeps per step and
the worst per-step global energy residual with stored energy.

Reports the wall time of one cold-start steady solve, the outer sweep
count and the time spent in each zone's apply(). With --profile K it
also prints the K most expensive functions (cProfile, by own time);
profiling roughly doubles the wall time, so the timing table of a
profiled run is not the number to quote.

With --reference (the default when --nodes is 1) the converged state
is compared against a saved snapshot: the worst temperature
difference in K and the worst relative difference of every other
quantity. This is what makes a speed-up checkable -- a faster path to
the SAME fixed point leaves both within the solver tolerance; a faster
path to a different answer does not.

Pin BLAS to one thread for numbers that compare across runs:

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \\
        python3 -m tools.benchmark
"""

import argparse
import collections
import contextlib
import cProfile
import io
import json
import os
import pstats
import sys
import time
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np

import main
from pyroprocess.globalstate import GlobalState
from tests.twin_harness import capture_state


ZONES = ("burning", "transition", "calciner", "preheater", "cooler")

DEFAULT_REFERENCE = REPO_ROOT / "tests" / "data" / "twin_state_reference.json"


def _timed(fn, totals, key):
    """Wrap fn so its wall time accumulates into totals[key]."""

    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            totals[key] += time.perf_counter() - t0

    return wrapper


def run(nodes_per_stage, profile_rows=0):
    """One cold-start steady solve. Returns a result dict."""

    validations = []

    def collect(result, equipment, balance_type="energy"):
        validations.append(
            {
                "equipment": equipment,
                "balance_type": balance_type,
                "result": result,
            }
        )
        return result

    cwd = os.getcwd()
    os.chdir(REPO_ROOT)

    try:
        cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")

        if nodes_per_stage is not None:
            cfg["preheater"]["nodes_per_stage"] = nodes_per_stage

        twin = main.Twin(
            state=GlobalState(N=cfg["plant"]["N"]),
            cfg=cfg,
        )

        totals = collections.defaultdict(float)

        for zone in ZONES:
            model = getattr(twin, zone)
            model.apply = _timed(model.apply, totals, zone)

        sweeps = [0]
        step = twin.step

        def counted_step():
            sweeps[0] += 1
            step()

        twin.step = counted_step

        profiler = cProfile.Profile() if profile_rows else None

        t0 = time.perf_counter()

        with mock.patch.object(main, "report_validation", collect):
            with contextlib.redirect_stdout(io.StringIO()):
                if profiler:
                    profiler.enable()
                twin.run()
                if profiler:
                    profiler.disable()

        wall = time.perf_counter() - t0

    finally:
        os.chdir(cwd)

    profile_text = None

    if profiler:
        buffer = io.StringIO()
        stats = pstats.Stats(profiler, stream=buffer)
        stats.sort_stats("tottime").print_stats(profile_rows)
        profile_text = buffer.getvalue().replace(f"{REPO_ROOT}/", "")

    return {
        "wall": wall,
        "sweeps": sweeps[0],
        "zones": dict(totals),
        "converged": bool(twin.converged),
        "snapshot": capture_state(twin, validations),
        "profile": profile_text,
    }


def run_dynamic(steps, dt, fuel_step):
    """Steady solve, then fuel x fuel_step and `steps` dynamic
    steps of dt [s]. Returns RTF, sweeps per step and the worst
    per-step global energy residual (stored energy included)."""

    residuals = []

    def collect(result, equipment, balance_type="energy"):
        residuals.append(result)
        return result

    cwd = os.getcwd()
    os.chdir(REPO_ROOT)

    try:
        cfg = main.load_cfg(REPO_ROOT / "configs" / "twin_cfg.yaml")

        twin = main.Twin(
            state=GlobalState(N=cfg["plant"]["N"]),
            cfg=cfg,
        )

        sweeps = [0]
        step = twin.step

        def counted_step():
            sweeps[0] += 1
            step()

        twin.step = counted_step

        with contextlib.redirect_stdout(io.StringIO()):
            twin.run(report=False)

        twin._last_inputs["Fuel_rate_total"] *= fuel_step
        sweeps[0] = 0
        wall = 0.0

        with mock.patch.object(main, "report_validation", collect):
            with contextlib.redirect_stdout(io.StringIO()):
                for _ in range(steps):
                    t0 = time.perf_counter()
                    twin.advance(dt)
                    wall += time.perf_counter() - t0
                    # Measures only; outside the timed step.
                    twin._validate_global_energy_balance()

    finally:
        os.chdir(cwd)

    return {
        "wall": wall,
        "rtf": steps * dt / wall,
        "sweeps_per_step": sweeps[0] / steps,
        "worst_global_relative": max(
            r["relative_residual"] for r in residuals
        ),
    }


def _is_residual(key):
    # A balance residual sits at round-off; its relative change is
    # noise over noise, so it is compared in absolute terms [W].
    return key.endswith("_residual")


def _is_temperature(key):
    return key.split("_")[0] in ("Tg", "Ts", "Tw") or key.endswith(
        "_temperature"
    )


def compare(snapshot, reference):
    """Worst |dT| [K] over temperatures, worst absolute change of a
    balance residual [W], worst relative difference over every other
    numeric entry, and any key whose booleans or presence differ."""

    worst_T = (0.0, None)
    worst_rel = (0.0, None)
    worst_res = (0.0, None)
    mismatched = []

    for key, ref in reference.items():

        if key not in snapshot:
            mismatched.append(key)
            continue

        new = snapshot[key]

        if isinstance(ref, bool):
            if new != ref:
                mismatched.append(key)
            continue

        a = np.atleast_1d(np.asarray(new, dtype=float))
        b = np.atleast_1d(np.asarray(ref, dtype=float))

        if a.shape != b.shape:
            mismatched.append(key)
            continue

        if _is_residual(key):
            d = float(np.max(np.abs(a - b))) if a.size else 0.0
            if d > worst_res[0]:
                worst_res = (d, key)
        elif _is_temperature(key):
            d = float(np.max(np.abs(a - b))) if a.size else 0.0
            if d > worst_T[0]:
                worst_T = (d, key)
        else:
            scale = np.maximum(np.abs(b), 1.0e-9)
            d = float(np.max(np.abs(a - b) / scale)) if a.size else 0.0
            if d > worst_rel[0]:
                worst_rel = (d, key)

    return worst_T, worst_rel, worst_res, mismatched


def main_cli(argv=None):

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--nodes",
        default="1",
        help="preheater nodes per stage, or 'cfg' for the configured value",
    )
    parser.add_argument("--profile", type=int, default=0, metavar="K")
    parser.add_argument("--reference", default=None)
    parser.add_argument(
        "--dynamic",
        type=int,
        default=0,
        metavar="STEPS",
        help="after the steady solve, step the fuel and time STEPS "
        "dynamic steps (Twin.advance) instead",
    )
    parser.add_argument("--dt", type=float, default=10.0)
    parser.add_argument("--fuel-step", type=float, default=1.05)
    args = parser.parse_args(argv)

    if args.dynamic:
        result = run_dynamic(args.dynamic, args.dt, args.fuel_step)
        print(
            f"{args.dynamic} steps x {args.dt:g} s after fuel "
            f"x{args.fuel_step:g}: wall {result['wall']:.1f} s | "
            f"RTF {result['rtf']:.1f} | "
            f"{result['sweeps_per_step']:.2f} sweeps/step | "
            f"worst global energy residual "
            f"{result['worst_global_relative']:.1e} relative"
        )
        return result

    nodes = None if args.nodes == "cfg" else int(args.nodes)

    result = run(nodes, profile_rows=args.profile)

    print(
        f"wall {result['wall']:.1f} s | sweeps {result['sweeps']} | "
        f"{1e3 * result['wall'] / max(result['sweeps'], 1):.0f} ms/sweep | "
        f"converged {result['converged']}"
        + ("  (profiled)" if args.profile else "")
    )

    for zone, seconds in sorted(
        result["zones"].items(), key=lambda item: -item[1]
    ):
        print(
            f"  {zone:11s} {seconds:8.2f} s  "
            f"{100.0 * seconds / result['wall']:5.1f} %"
        )

    reference_path = args.reference

    if reference_path is None and nodes == 1:
        reference_path = DEFAULT_REFERENCE

    if reference_path:
        with open(reference_path) as handle:
            reference = json.load(handle)["snapshot"]

        (dT, kT), (dr, kr), (dw, kw), mismatched = compare(
            result["snapshot"], reference
        )

        print(f"vs {Path(reference_path).name}:")
        print(f"  worst |dT|        {dT:.3e} K   ({kT})")
        print(f"  worst relative    {dr:.3e}     ({kr})")
        print(f"  worst residual    {dw:.3e} W   ({kw})")
        print(f"  mismatched keys   {len(mismatched)} {mismatched[:5]}")

    if result["profile"]:
        print(result["profile"])

    return result


if __name__ == "__main__":
    main_cli()
