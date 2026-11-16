"""Check geometry/pid/pid.yaml against the plant and the twin.

validate(p, g) returns a list of problems; empty means the P&ID says
only what the sources say.
"""

import re
from collections import defaultdict, deque

from tools.drawings import inventory as inv

from . import model, scope, symbols

GRID_COLS, GRID_ROWS = 41, 32
LINE_RE = re.compile(r"^([GMDAFK])([1-4])(\d{2})$")
INSTR_RE = re.compile(r"^(TT|TI|FT|FI|FY|AT|ST|PDI|JI)-([1-4])(\d{2})$")
OPC_RE = re.compile(r"^OPC-\d{2}$")

# the gas path the twin solves, in flow order (string A)
GAS_CHAIN = ("BRN", "KILN", "KIC", "ILC", "GN", "C5A", "R4A", "C4A", "R3A", "C3A",
             "R2A", "C2A", "R1A", "C1A", "IDFA")


def _end(text):
    """('EQ', id, port) / ('SRC'|'SNK', None, name) / ('OPC', id, None)."""
    if OPC_RE.match(text):
        return "OPC", text, None
    head, _, port = text.partition(".")
    if head in ("SRC", "SNK"):
        return head, None, port
    return "EQ", head, port


def validate(p, g=None, cfg=None, snapshot=None):
    g = g or model.pg.load()
    err = []
    sheets = p["sheets"]
    eq = p["equipment"]
    lines = p["lines"]
    conns = p["connectors"]
    instr = p["instruments"]

    # ---- sheets
    nos = sorted(s["num"] for s in sheets.values())
    if nos != list(range(1, len(nos) + 1)):
        err.append(f"sheet numbers {nos} are not 1..n")
    sheet_no = {k: s["num"] for k, s in sheets.items()}
    for k, s in sheets.items():
        if not str(s.get("scope", "")).strip():
            err.append(f"sheet {k}: no scope (the title block's 'as the twin models it, <scope>')")

    # ---- equipment
    tags = {row[1] for row in inv.EQUIPMENT}
    for i, e in eq.items():
        if e["tag"] not in tags:
            err.append(f"equipment {i}: tag {e['tag']!r} is not an inventory tag")
        if e["sheet"] not in sheets:
            err.append(f"equipment {i}: unknown sheet {e['sheet']!r}")
        if e["symbol"] not in symbols.SYMBOLS:
            err.append(f"equipment {i}: unknown symbol {e['symbol']!r}")
        c0, r0 = e["cell"]
        w, h = e.get("size", [1, 1])
        if not (0 <= c0 and c0 + w <= GRID_COLS and 0 <= r0 and r0 + h <= GRID_ROWS):
            err.append(f"equipment {i}: cell {e['cell']} size {[w, h]} leaves the {GRID_COLS} x {GRID_ROWS} grid")
    drawn = {e["tag"] for e in eq.values()}
    for t in sorted(tags - drawn - {"VF"}):
        err.append(f"inventory tag {t} is on no sheet")

    # ---- lines
    seen = set()
    ins, outs = defaultdict(list), defaultdict(list)
    to_conn, from_conn = defaultdict(list), defaultdict(list)
    for no, ln in lines.items():
        m = LINE_RE.match(no)
        svc = ln["service"]
        if svc not in symbols.SERVICES:
            err.append(f"line {no}: unknown service {svc!r}")
            continue
        if not m:
            err.append(f"line {no}: not <GMDAFK><sheet 1-4><nn>")
        else:
            if m.group(1) != symbols.SERVICES[svc][0]:
                err.append(f"line {no}: service {svc} takes letter {symbols.SERVICES[svc][0]}")
            if ln["sheet"] not in sheets or int(m.group(2)) != sheet_no[ln["sheet"]]:
                err.append(f"line {no}: its digit is not its sheet's number")
        if no in seen:
            err.append(f"line {no}: duplicated")
        seen.add(no)
        for side, key in (("from", ln["from"]), ("to", ln["to"])):
            kind, ident, port = _end(key)
            if kind == "EQ":
                if ident not in eq:
                    err.append(f"line {no}: {side} {key}: no equipment {ident}")
                    continue
                e = eq[ident]
                if e["sheet"] != ln["sheet"]:
                    err.append(f"line {no}: {side} {ident} is on sheet {e['sheet']}, the line on {ln['sheet']}")
                if port not in symbols.SYMBOLS.get(e["symbol"], ()):
                    err.append(f"line {no}: {side} {key}: {e['symbol']} has no port {port!r}")
                (outs if side == "from" else ins)[ident].append(no)
            elif kind == "SRC":
                if side != "from" or port not in symbols.SOURCES:
                    err.append(f"line {no}: {key} is not a source on the from side")
            elif kind == "SNK":
                if side != "to" or port not in symbols.SINKS:
                    err.append(f"line {no}: {key} is not a sink on the to side")
            else:
                if ident not in conns:
                    err.append(f"line {no}: unknown connector {ident}")
                (to_conn if side == "to" else from_conn)[ident].append(no)
        try:
            model.resolve_size(g, ln["size"])
        except Exception as ex:
            err.append(f"line {no}: size {ln['size']!r}: {ex}")
        via = ln.get("via", [])
        for a, b in zip(via, via[1:]):
            if a[0] != b[0] and a[1] != b[1]:
                err.append(f"line {no}: via {a} -> {b} is not orthogonal")

    # ---- connectors
    for cid, c in conns.items():
        if not OPC_RE.match(cid):
            err.append(f"connector {cid}: not OPC-nn")
        if c["from_sheet"] == c["to_sheet"]:
            err.append(f"connector {cid}: both ends on sheet {c['from_sheet']}")
        a, b = to_conn.get(cid, []), from_conn.get(cid, [])
        if len(a) != 1 or len(b) != 1:
            err.append(f"connector {cid}: ends {len(a)} line(s) and starts {len(b)}; each must be exactly one")
            continue
        if lines[a[0]]["sheet"] != c["from_sheet"]:
            err.append(f"connector {cid}: its ending line {a[0]} is not on sheet {c['from_sheet']}")
        if lines[b[0]]["sheet"] != c["to_sheet"]:
            err.append(f"connector {cid}: its starting line {b[0]} is not on sheet {c['to_sheet']}")
        for no in (a[0], b[0]):
            if lines[no]["service"] != c["service"]:
                err.append(f"connector {cid}: line {no} is {lines[no]['service']}, the connector {c['service']}")

    # ---- the stream graph (connectors collapsed)
    edges = []
    for no, ln in lines.items():
        fk, fi, _ = _end(ln["from"])
        tk, ti, _ = _end(ln["to"])
        if tk == "OPC":
            nxt = from_conn.get(ti, [])
            if len(nxt) == 1:
                tk2, ti2, p2 = _end(lines[nxt[0]]["to"])
                edges.append((ln, fi if fk == "EQ" else ln["from"], ti2 if tk2 == "EQ" else lines[nxt[0]]["to"]))
        elif fk != "OPC":
            edges.append((ln, fi if fk == "EQ" else ln["from"], ti if tk == "EQ" else ln["to"]))
    for i in eq:
        if not ins[i]:
            err.append(f"equipment {i}: no line enters it")
        if not outs[i]:
            err.append(f"equipment {i}: no line leaves it")
    # one connected graph over every sheet
    adj = defaultdict(set)
    for _, a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    if eq:
        start = next(iter(eq))
        seen_n, todo = {start}, deque([start])
        while todo:
            for n in adj[todo.popleft()]:
                if n not in seen_n:
                    seen_n.add(n)
                    todo.append(n)
        for i in eq:
            if i not in seen_n:
                err.append(f"equipment {i}: not connected to the rest of the plant")
    # the gas path of the twin, burner to stack
    gas = defaultdict(set)
    for ln, a, b in edges:
        if ln["service"] == "gas":
            gas[a].add(b)
    reach, todo = {"BRN"}, deque(["BRN"])
    while todo:
        for n in gas[todo.popleft()]:
            if n not in reach:
                reach.add(n)
                todo.append(n)
    for i in GAS_CHAIN:
        if i not in reach:
            err.append(f"gas path: {i} is not reached from the burner by gas lines")
    if "SNK.stack" not in reach:
        err.append("gas path: the stack is not reached")

    # ---- instruments
    covered = defaultdict(list)
    for tag, it in instr.items():
        m = INSTR_RE.match(tag)
        if not m:
            err.append(f"instrument {tag}: not ISA <letters>-<sheet 1-4><nn>")
        on = it["at"]
        if on in lines:
            sh = lines[on]["sheet"]
        elif on in eq:
            sh = eq[on]["sheet"]
        else:
            err.append(f"instrument {tag}: at {on!r} is neither a line nor an equipment")
            sh = None
        if m and sh and int(m.group(2)) != sheet_no[sh]:
            err.append(f"instrument {tag}: its digit is not the number of sheet {sh}, where {on} is")
        if it.get("side", "top") not in ("top", "right", "left"):
            err.append(f"instrument {tag}: side {it['side']!r} is not top, right or left")
        if not 0 <= it.get("along", 0) <= 1:
            err.append(f"instrument {tag}: along {it['along']} is not in 0..1")
        if ("side" in it or "along" in it) and on not in eq:
            err.append(f"instrument {tag}: side and along place a bubble on an equipment, not on a line")
        try:
            status, _ = model.resolve_twin_key(it["key"])
            if status != it["status"]:
                err.append(f"instrument {tag}: key {it['key']} is {status}, written {it['status']}")
            if it["status"] != "Modelled" and it["mount"] != "P":
                err.append(f"instrument {tag}: an {it['status']} value has no field device (mount P)")
        except Exception as ex:
            err.append(f"instrument {tag}: {ex}")
        covered[it["key"]].append(tag)
    for sp_id, sp in p.get("setpoints", {}).items():
        covered[sp["manipulated"]].append(sp_id)
        if sp["measured"] not in instr:
            err.append(f"setpoint {sp_id}: measured {sp['measured']} is not an instrument")
        if sp["sheet"] not in sheets:
            err.append(f"setpoint {sp_id}: unknown sheet")
    for key in scope.SCOPE:
        n = len(covered.get(key, []))
        if n != 1:
            err.append(f"scope: {key} is covered {n} times ({covered.get(key, [])}); it must be once")
    for key in covered:
        if key not in scope.SCOPE:
            err.append(f"scope: {key} ({covered[key]}) is not something the twin models in scope.py")
    return err
