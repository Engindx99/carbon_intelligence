---
name: cfd-record
description: Build a CFD run record from steady.out and Fluent transcripts
disable-model-invocation: true
argument-hint: <run dir>
---

Run `python3 tools/cfd_record.py` for the run directory given in the arguments (check `--help` first). Summarize residuals, convergence and key results; do not paste raw logs.
