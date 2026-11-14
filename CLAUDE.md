# CLAUDE.md

1. This is a physics-based steady-state cement pyroprocess Digital Twin; preserve physical consistency over heuristic behavior.
2. Use the existing architecture and code structure as the foundation; avoid unnecessary rewrites or refactoring. However, modify modules or the physical model when technically necessary for model improvement.
3. Work incrementally: one focused task at a time, keeping changes small and reviewable.
4. Use SI units exclusively.
5. Maintain causal physics: mass/energy transport → reactions → enthalpy/heat transfer → temperature/state updates.
6. Prefer physical models and conservation laws over arbitrary clamps, heuristics, or empirical fixes.
7. Validate mass and energy conservation, handoffs, units, bounds, and numerical stability after changes.
8. Geometry exists to parametrically define physically meaningful, continuous fluid volumes for CFD, not to perform structural or manufacturing CAD design. Prefer simple, clean, and CFD-oriented geometry over detailed or production-oriented geometry. Keep geometry calculations/solvers only when necessary to construct, validate, or derive relevant hydraulic/geometric properties of the fluid volume; avoid unnecessary geometric detail and computational complexity.
   Exception: `geometry/macros/plant_topology_2d.bas` draws a schematic, real-scale 2D drawing (SLDDRW) of the plant topology (equipment, and the gas, meal and air paths between them); it is not a CFD input.
   Exception: `geometry/macros/drawings.bas` makes ISO engineering drawings of each equipment's inner (fluid) geometry from the CFD solids (`geometry/drawings/`); they are not fabrication drawings and draw no wall, flange, support or material.
   Exception: `geometry/macros/pid.bas` draws the P&ID of the plant as the twin models it (4 A1 sheets, ISO 10628 / ISA 5.1 symbols; topology and instruments from `geometry/pid/pid.yaml`, line sizes from `plant_geometry.yaml`); it shows only what the twin has and is not a CFD input.
   
9. For CFD, review the literature, but use the simplest and fastest sufficient solution; do not add academic-level complexity.

