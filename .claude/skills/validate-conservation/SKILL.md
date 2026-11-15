---
name: validate-conservation
description: Validate mass/energy conservation, handoffs, bounds and stability after a model change (CLAUDE.md rule 7)
disable-model-invocation: true
---

1. `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 pytest tests/ -q`
2. Run the twin via tests/twin_harness.py and read the reporter diagnostics (reporter/diagnostics.py); report mass and energy residuals.
3. `python -m tools.benchmark --dynamic` for RTF and stability.
4. Compare with the latest entry in reporter/logs/validation.jsonl. Report failures verbatim; never loosen a tolerance or add a clamp to pass.
