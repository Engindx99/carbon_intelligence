"""Write one CFD run's record: what was run and what came out, from the files.

Nothing is typed in by hand: the numbers come from the run's report file
(steady.out), its Fluent transcript and the mesh transcript, and the inputs
from the plant's one geometry source. One record per run:

    <run dir>/records/<name>.json   all of it, for tests and comparisons
    <run dir>/RUNS.md               one line per run, newest last (appended;
                                    a rerun of a name replaces its line)

    python3 tools/cfd_record.py C:/Users/engin/calciner_v2 --name run1 \
        --mesh-transcript fluent-20261114-164038-22120.trn \
        --note "new mitred neck, equal split by targeted mass flow"

--transcript defaults to the newest solve transcript (the one with a
residual table). Missing pieces are left out of the record, not guessed.
"""

import argparse
import hashlib
import json
import re
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

STEP = ROOT / "geometry" / "output" / "2500" / "calciner.step"
TAIL = 100   # iterations the stability numbers are taken over


def read_report(path):
    """{name: [values]} of a Fluent report file (steady.out)."""
    cols, rows = None, []
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith('("Iteration"'):
            cols = re.findall(r'"([^"]+)"', line)
        elif cols and re.match(r"^\s*\d+\s", line):
            v = line.split()
            if len(v) == len(cols):
                rows.append([float(x) for x in v])
    if not cols or not rows:
        raise SystemExit(f"{path}: no report table")
    return {c: [r[i] for r in rows] for i, c in enumerate(cols)}


def solve_numbers(rep, y_co2):
    last = {k: v[-1] for k, v in rep.items()}
    n = min(TAIL, len(rep["Iteration"]))
    tail = {k: v[-n:] for k, v in rep.items()}
    out = {
        "iterations": int(last["Iteration"]),
        "last": last,
        "tail_n": n,
        "tail_mean": {k: statistics.fmean(v) for k, v in tail.items()},
        "tail_range": {k: max(v) - min(v) for k, v in tail.items()},
    }
    m = out["tail_mean"]
    if "co2_out1" in m and y_co2:
        # CO2 is the mixing tracer: kiln-gas share of an outlet = Y_CO2 / Y_CO2(kiln gas)
        out["kiln_gas_share"] = {"outlet_1": m["co2_out1"] / y_co2,
                                 "outlet_2": m["co2_out2"] / y_co2}
    return out


def residuals(path):
    """Last row of the newest residual table in a transcript."""
    head, last = None, None
    for line in path.read_bytes().decode("latin-1").splitlines():
        if "iter  continuity" in line:
            head = line.split()
        elif head and re.match(r"^\s+\d+\s+[\d.e+-]+", line):
            last = line.split()
    if not head or not last:
        return None
    names = head[1:12]
    return {"iter": int(last[0]), **{n: float(last[1 + i]) for i, n in enumerate(names)}}


def mesh_numbers(path):
    """Counts and quality of the last mesh report in a Fluent transcript."""
    t = path.read_bytes().decode("latin-1")
    out = {}
    for key, pat in (("tet_cells", r"(\d+) tetrahedral cells, zone\s+\d+\.\s"),
                     ("poly_cells", r"(\d+) polyhedra cells, zone\s+\d+\.\s"),
                     ("nodes_final", None)):
        if pat:
            m = re.findall(pat, t)
            if m:
                out[key] = int(m[-1])
    nodes = re.findall(r"(\d+) nodes\.", t)
    if nodes:
        out["nodes"] = int(nodes[-1])
    oq = re.findall(r"Minimum Orthogonal Quality =\s+([\d.e+-]+)", t)
    ar = re.findall(r"Maximum Aspect Ratio =\s+([\d.e+-]+)", t)
    vol = re.findall(r"total volume \(m3\):\s+([\d.e+-]+)", t)
    if oq:
        out["min_orthogonal_quality_first"] = float(oq[0])
        out["min_orthogonal_quality_last"] = float(oq[-1])
    if ar:
        out["max_aspect_ratio_last"] = float(ar[-1])
    if vol:
        out["volume_m3"] = float(vol[-1])
    return out


def _read_dpm(path):
    """[(parcel name, values)] of a Fluent DPM sample file."""
    rows = []
    for line in path.read_text(errors="replace").splitlines():
        m = re.match(r"\(\((.*)\)\s*(\S+)\)", line.strip())
        if m:
            rows.append((m.group(2), [float(x) for x in m.group(1).split()]))
    return rows


def _wstats(tw):
    """Mass-weighted mean, p10, p50, p90, max of [(t, w)]."""
    tw = sorted(tw)
    w_sum = sum(w for _, w in tw)
    out = {"mean": sum(t * w for t, w in tw) / w_sum, "max": tw[-1][0]}
    c = 0.0
    for p in (0.1, 0.5, 0.9):
        c = 0.0
        for t, w in tw:
            c += w
            if c >= p * w_sum:
                out["p%d" % round(p * 100)] = t
                break
    return out


def dpm_numbers(d):
    """Split and residence times from gas_outlet_1/2.dpm and neckp.dpm in d
    (columns: x y z u v w diameter t mass-flow mass frequency time name)."""
    out1, out2, neck = (d / "gas_outlet_1.dpm"), (d / "gas_outlet_2.dpm"), (d / "neckp.dpm")
    if not (out1.exists() and out2.exists()):
        return None
    per = {}
    allv, allo = [], []
    outs = {}
    for f, o in ((out1, 1), (out2, 2)):
        for name, v in _read_dpm(f):
            outs.setdefault(name.split(":")[0], []).append((v[11], v[8], o))
    first = {}
    if neck.exists():
        for name, v in _read_dpm(neck):
            if name not in first or v[11] < first[name][11]:
                first[name] = v
    vessel = {}
    for name, v in first.items():
        vessel.setdefault(name.split(":")[0], []).append((v[11], v[8]))
    for c in sorted(outs):
        o = outs[c]
        m = sum(w for _, w, _ in o)
        per[c] = {"to_outlet_1": sum(w for _, w, k in o if k == 1) / m,
                  "domain": _wstats([(t, w) for t, w, _ in o]), "parcels": len(o)}
        if c in vessel:
            per[c]["vessel"] = _wstats(vessel[c])
            allv += vessel[c]
        allo += [(t, w) for t, w, _ in o]
    m = sum(w for _, w in allo)
    res = {"classes": per, "parcels": len(allo),
           "to_outlet_1": sum(w for _, w, k in sum(outs.values(), []) if k == 1) / m,
           "domain": _wstats(allo)}
    if allv:
        res["vessel"] = _wstats(allv)
    return res


def dpm_settings(path):
    """What a Fluent settings file says about the DPM: injections' file dir, tries,
    particle cp, wall coefficients, coupling."""
    t = path.read_text(errors="replace")
    out = {}
    m = re.findall(r'\(file . "([^"]+)"\)', t)
    if m:
        out["injection_dir"] = m[0].rsplit("/", 1)[0]
    m = re.findall(r"\(ntries \. (\d+)\)", t)
    if m:
        out["ntries"] = int(m[0])
    m = re.search(r"\(specific-heat \(constant \. ([\d.]+)\)\)", t)
    if m:
        out["particle_cp_J_kgK"] = float(m.group(1))
    m = re.findall(r"\(dpm/bc-norm-coeff \(polynomial angle ([\d.]+)\)\)", t)
    if m:
        out["wall_normal_coeff"] = float(m[0])
    return out


def inputs():
    import yaml
    from geometry import plant_geometry as pg
    from tools import calciner_named_selections as ns

    g = yaml.safe_load((ROOT / "geometry" / "plant_geometry.yaml").read_text(encoding="utf-8"))
    b = pg.calciner_boundaries(g)
    return {
        "kiln_gas": {"flow_kg_s": b["kiln_gas_inlet"]["flow"], "T_K": b["kiln_gas_inlet"]["T"],
                     "y_CO2": b["kiln_gas_inlet"]["y"]["CO2"]},
        "tertiary_air": {"flow_kg_s": b["tertiary_air_inlet"]["flow"], "T_K": b["tertiary_air_inlet"]["T"]},
        "mesh_sizes_m": {"global": ns.GLOBAL_SIZE, **ns.FACE_SIZES},
        "solid_volume_m3": solid_volume(),
    }, b["kiln_gas_inlet"]["y"]["CO2"]


def solid_volume():
    """The CFD solid's volume as the macro logged it (decimal comma)."""
    log = ROOT / "geometry" / "output" / "2500" / "calciner_build.log"
    if log.exists():
        m = re.search(r"CFD domain volume\s+([\d,.]+)", log.read_text(errors="replace"))
        if m:
            return float(m.group(1).replace(",", "."))
    return None


def git_head():
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def sha(path):
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def md_line(rec):
    s = rec.get("solve", {})
    m = s.get("tail_mean", {})
    sh = s.get("kiln_gas_share", {})
    r = rec.get("residuals") or {}
    mesh = rec.get("mesh", {})
    f = lambda x, p=1: "-" if x is None else f"{x:.{p}f}"
    return ("| {name} | {date} | {note} | {poly} / {nodes} | {oq} | {it} | {m1} / {m2} | {t1} / {t2} | "
            "{s1} / {s2} | {cont} | {dpm} |").format(
        name=rec["name"], date=rec["date"][:10], note=rec.get("note", ""),
        poly=mesh.get("poly_cells", "-"), nodes=mesh.get("nodes", "-"),
        oq=f(mesh.get("min_orthogonal_quality_last"), 3), it=s.get("iterations", "-"),
        m1=f(-m.get("m_out1", float("nan")) if m else None), m2=f(-m.get("m_out2", float("nan")) if m else None),
        t1=f(m.get("t_out1")), t2=f(m.get("t_out2")),
        s1=f(sh.get("outlet_1"), 3), s2=f(sh.get("outlet_2"), 3),
        cont="-" if not r else f"{r.get('continuity', float('nan')):.1e}",
        dpm="-" if not rec.get("dpm", {}).get("domain") else
            "{c}: out1 {p:.1%}, vessel {v:.2f} s, domain {dm:.2f} s".format(
                c=rec["dpm"].get("coupling") or "dpm", p=rec["dpm"]["to_outlet_1"],
                v=rec["dpm"].get("vessel", {}).get("mean", float("nan")), dm=rec["dpm"]["domain"]["mean"]))


HEADER = ("| run | date | note | poly cells / nodes | min OQ | iterations | outlet mass flow 1 / 2 [kg/s] | "
          "outlet T 1 / 2 [K] | kiln-gas share 1 / 2 | continuity residual | meal DPM |\n"
          "|---|---|---|---|---|---|---|---|---|---|---|\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--name", required=True)
    ap.add_argument("--report", default="steady.out")
    ap.add_argument("--transcript")
    ap.add_argument("--mesh-transcript")
    ap.add_argument("--note", default="")
    ap.add_argument("--dpm-dir", help="folder with gas_outlet_1/2.dpm (+ neckp.dpm)")
    ap.add_argument("--dpm-set", help="Fluent settings file the DPM run used")
    ap.add_argument("--dpm-load", type=float, help="meal mass flow per pipe the injections carry [kg/s]")
    ap.add_argument("--coupling", default="", help="one-way | two-way momentum | two-way")
    a = ap.parse_args()

    d = Path(a.run_dir)
    inp, y_co2 = inputs()
    rec = {"name": a.name, "date": datetime.now().isoformat(timespec="seconds"), "note": a.note,
           "git": git_head(), "solid_step_sha256_16": sha(STEP), "inputs": inp}

    if (d / a.report).exists():
        rec["solve"] = solve_numbers(read_report(d / a.report), y_co2)
    tr = Path(a.transcript) if a.transcript else None
    if tr is None:
        cands = sorted(d.glob("fluent-2*.trn"), key=lambda p: p.stat().st_mtime, reverse=True)
        tr = next((p for p in cands if b"iter  continuity" in p.read_bytes()), None)
    elif not tr.is_absolute():
        tr = d / tr
    if tr and tr.exists():
        rec["residuals"] = residuals(tr)
        rec["transcript"] = tr.name
    if a.mesh_transcript:
        mt = Path(a.mesh_transcript)
        mt = mt if mt.is_absolute() else d / mt
        rec["mesh"] = mesh_numbers(mt)
        rec["mesh"]["transcript"] = mt.name
    if a.dpm_dir:
        dd = Path(a.dpm_dir)
        dd = dd if dd.is_absolute() else d / dd
        rec["dpm"] = dpm_numbers(dd) or {}
        rec["dpm"]["dir"] = dd.name
        rec["dpm"]["coupling"] = a.coupling
        if a.dpm_load is not None:
            rec["dpm"]["load_kg_s_per_pipe"] = a.dpm_load
            rec["dpm"]["loading_kg_per_kg_gas"] = 2 * a.dpm_load / (inp["kiln_gas"]["flow_kg_s"] + inp["tertiary_air"]["flow_kg_s"])
        if a.dpm_set:
            ds = Path(a.dpm_set)
            rec["dpm"]["settings"] = dpm_settings(ds if ds.is_absolute() else d / ds)
    rec["files"] = {p.name: {"MB": round(p.stat().st_size / 1e6, 1),
                             "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="minutes")}
                    for p in sorted(d.glob("calc_v2_*.h5")) + sorted(d.glob("*.msh")) if p.is_file()}

    (d / "records").mkdir(exist_ok=True)
    (d / "records" / f"{a.name}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")

    runs = d / "RUNS.md"
    lines = runs.read_text(encoding="utf-8").splitlines() if runs.exists() else []
    body = [l for l in lines if l.startswith("|") and not l.startswith("| run ") and not l.startswith("|---")]
    body = [l for l in body if not l.startswith(f"| {a.name} |")] + [md_line(rec)]
    runs.write_text("# CFD runs\n\nWritten by tools/cfd_record.py from the run's files.\n\n" + HEADER
                    + "\n".join(body) + "\n", encoding="utf-8")
    print("wrote", d / "records" / f"{a.name}.json", "and", runs)


if __name__ == "__main__":
    main()
