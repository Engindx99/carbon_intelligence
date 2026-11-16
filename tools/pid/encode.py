"""Turn geometry/pid/pid.yaml into what the drawing and the docs need.

consts(p, g)  the generated Const block of geometry/macros/pid.bas
rows_*(p, g)  the generated tables of geometry/pid/pid.md

The macro reads, per sheet SH, the strings PID_<SH>_1 .. PID_<SH>_16
(rows ';', fields '~', as drawings.bas's parameter table) and PID_<SH>_NO,
PID_<SH>_TITLE, PID_<SH>_HASH (sheet_hash). A record's first field is its type:

  E~id~tag~symbol~col~row~w~h~qty~extra~label
  L~no~service~fromId~fromPort~toId~toPort~sizeText~status~via
  I~tag~status~at~mount~var~side~along
  O~id~line~dir~otherSheetNo~service~label
  S~id~measured~manipulated~spec

A size is written as the sheet prints it ('D 3.070', 'D 0.849 E', '-'),
so the macro formats no number from data.
"""

from . import model

CHUNKS = 16
CHUNK_LEN = 700
FORBIDDEN = ";~\""


def _field(x):
    s = str(x)
    if any(ch in s for ch in FORBIDDEN) or not s.isascii():
        raise ValueError(f"a record field may not hold ; ~ a quote or non-ASCII: {s!r}")
    return s


def _row(*fields):
    return "~".join(_field(f) for f in fields) + ";"


def _end(text):
    if text.startswith("OPC-"):
        return text, "-"
    head, _, port = text.partition(".")
    return head, port


def _extra(e, g):
    out = []
    if "zones" in e:
        k = model.pg.kiln(g)
        out.append(f"zones={len(e['zones'])},split={k['transition_L'] / k['L']:.4f}")
    if "segments" in e:
        out.append(f"seg={e['segments']},hood={e.get('hood_segments', 0)}")
    return ",".join(out) if out else "-"


def sheet_rows(p, g, sh):
    """Every record of sheet `sh`, in drawing order."""
    rows = []
    for i, e in p["equipment"].items():
        if e["sheet"] != sh:
            continue
        w, h = e.get("size", [1, 1])
        rows.append(_row("E", i, e["tag"], e["symbol"], e["cell"][0], e["cell"][1], w, h,
                         e.get("qty", "-"), _extra(e, g), e.get("label", e["tag"])))
    for no, ln in p["lines"].items():
        if ln["sheet"] != sh:
            continue
        value, status, _ = model.resolve_size(g, ln["size"])
        fi, fp = _end(ln["from"])
        ti, tp = _end(ln["to"])
        via = "/".join(f"{c},{r}" for c, r in ln.get("via", [])) or "-"
        rows.append(_row("L", no, ln["service"], fi, fp, ti, tp, model.size_text(value, status), status, via))
    for tag, it in p["instruments"].items():
        on = it["at"]
        host = p["lines"][on]["sheet"] if on in p["lines"] else p["equipment"][on]["sheet"]
        if host == sh:
            rows.append(_row("I", tag, it["status"], on, it["mount"], it["var"], it.get("side", "top"), it.get("along", 0)))
    num = {k: s["num"] for k, s in p["sheets"].items()}
    for cid, c in p["connectors"].items():
        if c["from_sheet"] == sh:
            line = next(n for n, ln in p["lines"].items() if ln["to"] == cid)
            rows.append(_row("O", cid, line, "out", num[c["to_sheet"]], c["service"], c["label"]))
        if c["to_sheet"] == sh:
            line = next(n for n, ln in p["lines"].items() if ln["from"] == cid)
            rows.append(_row("O", cid, line, "in", num[c["from_sheet"]], c["service"], c["label"]))
    for sid, s in p.get("setpoints", {}).items():
        if s["sheet"] == sh:
            rows.append(_row("S", sid, s["measured"], s["manipulated"], s["spec"]))
    return rows


def macro_code():
    """pid.bas without its generated block: the drawing code, whose
    changes also change what the sheet shows."""
    from tools.gen_geometry import BEGIN, END, MACROS
    text = (MACROS / "pid.bas").read_text(encoding="latin-1")
    head, _, rest = text.partition(BEGIN)
    _, _, tail = rest.partition(END)
    return "\n".join(l.rstrip() for l in (head + tail).splitlines())


def sheet_hash(p, g, sh):
    """Fingerprint of everything sheet `sh` is drawn from: its number,
    title and records, and the macro's drawing code. pid.bas writes it
    next to the PDF (pid_<SH>.stamp); a stamp that differs means the
    committed sheet was drawn from an older source."""
    import hashlib
    s = p["sheets"][sh]
    text = "\n".join([str(s["num"]), s["title"], *sheet_rows(p, g, sh), macro_code()])
    return hashlib.sha256(text.encode("ascii", "replace")).hexdigest()[:16]


def consts(p, g):
    from tools.gen_geometry import Const

    out = []
    for sh, s in p["sheets"].items():
        chunks, cur = [], ""
        for r in sheet_rows(p, g, sh):
            if len(cur) + len(r) > CHUNK_LEN:
                chunks.append(cur)
                cur = ""
            cur += r
        chunks.append(cur)
        if len(chunks) > CHUNKS:
            raise ValueError(f"sheet {sh}: {len(chunks)} chunks, the macro reads {CHUNKS}")
        chunks += [""] * (CHUNKS - len(chunks))
        out.append(Const(f"PID_{sh}_NO", s["num"], f"sheet {sh} number", kind="Long"))
        out.append(Const(f"PID_{sh}_TITLE", _field(s["title"]), f"sheet {sh} title", kind="String"))
        out.append(Const(f"PID_{sh}_HASH", sheet_hash(p, g, sh), f"sheet {sh} source fingerprint", kind="String"))
        out += [Const(f"PID_{sh}_{i + 1}", c, "P&ID records", kind="String") for i, c in enumerate(chunks)]
    return out


# ----------------------------------------------------------------------
# the document's tables
# ----------------------------------------------------------------------
def _short(x):
    return f"{x:.4g}" if isinstance(x, (int, float)) else "-"


def rows_sheets(p, g):
    out = []
    for sh, s in p["sheets"].items():
        n_eq = sum(e["sheet"] == sh for e in p["equipment"].values())
        n_ln = sum(l["sheet"] == sh for l in p["lines"].values())
        n_in = sum((p["lines"][i["at"]]["sheet"] if i["at"] in p["lines"] else p["equipment"][i["at"]]["sheet"]) == sh
                   for i in p["instruments"].values())
        out.append((str(s["num"]), sh, s["title"], str(n_eq), str(n_ln), str(n_in)))
    return out


def rows_equipment(p, g):
    return [(i, e["tag"], e["symbol"], e["sheet"], e.get("qty", "-")) for i, e in p["equipment"].items()]


def rows_lines(p, g):
    out = []
    for no, ln in sorted(p["lines"].items(), key=lambda kv: (p["sheets"][kv[1]["sheet"]]["num"], kv[0])):
        value, status, _ = model.resolve_size(g, ln["size"])
        out.append((no, ln["service"], ln["from"], ln["to"], ln["sheet"], model.size_text(value, status), status))
    return out


def rows_instruments(p, g):
    import json
    snap = json.loads(model.REFERENCE.read_text(encoding="utf-8"))["snapshot"]
    return [(tag, it["var"], it["key"], it["status"], _short(model.reference_value(it["key"], snap)), it["at"])
            for tag, it in p["instruments"].items()]


def rows_connectors(p, g):
    return [(cid, c["service"], c["from_sheet"], c["to_sheet"], c["label"]) for cid, c in p["connectors"].items()]


# ----------------------------------------------------------------------
# geometry/drawings/pid/pid.json
# ----------------------------------------------------------------------
def pid_sheets(p):
    """{inventory tag: ['1 PH', ...]}: the sheets each piece of equipment is drawn on."""
    out = {}
    for e in p["equipment"].values():
        label = f"{p['sheets'][e['sheet']]['num']} {e['sheet']}"
        out.setdefault(e["tag"], [])
        if label not in out[e["tag"]]:
            out[e["tag"]].append(label)
    return {t: sorted(v) for t, v in out.items()}


def payload(p, g):
    """Every line and instrument on the sheets, with the size, status and
    reference value the source gives, and where the drawing's files go."""
    import json
    snap = json.loads(model.REFERENCE.read_text(encoding="utf-8"))["snapshot"]
    lines = []
    for no, ln in p["lines"].items():
        value, status, inputs = model.resolve_size(g, ln["size"])
        lines.append({
            "line": no, "service": ln["service"], "sheet": ln["sheet"],
            "from": ln["from"], "to": ln["to"], "size_ref": ln["size"],
            "size_m": value, "size_text": model.size_text(value, status),
            "status": status, "inputs": inputs,
        })
    instruments = []
    for tag, it in p["instruments"].items():
        status, where = model.resolve_twin_key(it["key"])
        instruments.append({
            "tag": tag, "variable": it["var"], "key": it["key"], "status": status,
            "found_in": where, "at": it["at"], "mount": it["mount"],
            "reference_value": model.reference_value(it["key"], snap),
        })
    return {
        "source": "geometry/pid/pid.yaml",
        "scope_rule": "only what the twin models (tools/pid/scope.py)",
        "drawing": {
            "macro": "geometry/macros/pid.bas",
            "files": {sh: [f"geometry/drawings/pid/pid_{sh}.pdf", f"geometry/drawings/pid/pid_{sh}.dxf"]
                      for sh in p["sheets"]},
            "build_logs": {sh: f"geometry/output/2500/pid_{sh}_build.log" for sh in p["sheets"]},
            "sheet": "A1, ISO 5457 frame, ISO 7200 title block",
            "units": "none (schematic, grid cells)",
        },
        "sheets": [{"code": k, **s} for k, s in p["sheets"].items()],
        "equipment": [{"id": i, **e} for i, e in p["equipment"].items()],
        "lines": lines,
        "instruments": instruments,
        "connectors": [{"id": k, **c} for k, c in p["connectors"].items()],
        "setpoints": [{"id": k, **s} for k, s in p.get("setpoints", {}).items()],
    }
