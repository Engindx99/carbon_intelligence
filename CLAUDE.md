# CLAUDE.md

1. This is a physics-based cement pyroprocess Digital Twin; preserve physical consistency over heuristic behavior.
2. Use the existing architecture and code structure as the foundation; avoid unnecessary rewrites or refactoring. However, modify modules or the physical model when technically necessary for model improvement.
3. Work incrementally: one focused task at a time, keeping changes small and reviewable.
4. Use SI units exclusively.
5. Maintain causal physics: mass/energy transport → reactions → enthalpy/heat transfer → temperature/state updates.
6. Prefer physical models and conservation laws over arbitrary clamps, heuristics, or empirical fixes.
7. Validate mass and energy conservation, handoffs, units, bounds, and numerical stability after changes.