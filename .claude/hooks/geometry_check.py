#!/usr/bin/env python3
"""PostToolUse: after an edit under geometry/, run gen_geometry.py --check.

Exit 2 reports stale generated blocks back to Claude (the edit is not undone).
"""
import json, os, subprocess, sys

d = json.load(sys.stdin)
f = (d.get("tool_input") or {}).get("file_path", "").replace("\\", "/")
if "/geometry/" not in f or not f.endswith((".yaml", ".bas", ".md")):
    sys.exit(0)
root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
r = subprocess.run([sys.executable, "tools/gen_geometry.py", "--check"],
                   cwd=root, capture_output=True, text=True, timeout=120)
if r.returncode:
    sys.stderr.write("gen_geometry.py --check failed: generated blocks are stale. "
                     "Run tools/gen_geometry.py; do not hand-edit generated blocks.\n"
                     + (r.stdout + r.stderr)[-1500:])
    sys.exit(2)
