# CLAUDE.md

1. This is a physics-based dynamic cement pyroprocess Digital Twin; preserve physical consistency over heuristic behavior.
2. Use the existing architecture and code structure as the foundation; avoid unnecessary rewrites or refactoring. However, modify modules or the physical model when technically necessary for model improvement.
3. Work incrementally: one focused task at a time, keeping changes small and reviewable.
4. Use SI units exclusively.
5. Maintain causal physics: mass/energy transport → reactions → enthalpy/heat transfer → temperature/state updates.
6. Prefer physical models and conservation laws over arbitrary clamps, heuristics, or empirical fixes.
7. Validate mass and energy conservation, handoffs, units, bounds, and numerical stability after changes.
8. Geometry and CFD suitability

Geometry must represent the physically meaningful flow domain and preserve the features that materially affect fluid dynamics, including flow direction, inlet/outlet configurations, bends, expansions, contractions, recirculation zones and relevant internal structures.

Keep geometry CFD-oriented and avoid unnecessary manufacturing or structural details. However, never remove physically important geometric features merely to simplify meshing or reduce computational cost. Simplification is acceptable only when its impact on the relevant flow physics is negligible or explicitly justified.

9. CFD methodology and engineering fidelity

Review relevant engineering literature and select CFD methods based on the physical phenomena, required outputs and engineering objectives. Prefer computationally efficient methods, but never sacrifice essential physical fidelity, numerical reliability or engineering usefulness merely to obtain a faster or simpler solution.

Use appropriate turbulence, energy, species transport, combustion and multiphase models whenever required by the problem. Start with a baseline model and increase physical and numerical complexity incrementally, based on validation results and identified modeling limitations.

A CFD solution is acceptable only when its assumptions, boundary conditions, numerical convergence, conservation balances and relevant engineering outputs have been evaluated. A fast but physically inadequate solution is not an acceptable result.

10. Engineering adequacy and model validation

Do not confuse computational simplicity with engineering adequacy. The objective is to develop a model that is sufficiently accurate and reliable for its intended engineering application.

When simplifying a physical model, explicitly document:
- Which physical phenomena are included or excluded.
- Why each simplification is acceptable.
- What outputs may be affected.
- What validation evidence supports the chosen model.

If available computational resources are insufficient for the required fidelity, report the limitation and propose a technically justified alternative rather than silently degrading the model.


## Commands and environment
- Tests: `pytest tests/` from the repo root. Pin `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1` for reproducible runs.
- Geometry: edit only `geometry/plant_geometry.yaml`; `python3 tools/gen_geometry.py` writes macro Consts and doc tables (never hand-edit them); `--check` verifies. See `.claude/rules/geometry.md`.
- Skills: `/validate-conservation`, `/geom-regen`, `/cfd-record`. Agents: `physics-reviewer`, `log-scanner`.
- Repo is on /mnt/c (slow search): avoid broad find/grep over `geometry/`; never read `.dxf`.
