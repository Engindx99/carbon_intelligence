# CLAUDE.md

1. This is a physics-based cement pyroprocess Digital Twin; preserve physical consistency over heuristic behavior.
2. Follow the existing architecture and code structure; do not rewrite or reorganize modules without a clear technical reason.
3. Work incrementally: one focused task at a time, keeping changes small and reviewable.
4. Preserve existing variables, equations, states, and interfaces unless a change is technically necessary.
5. Use SI units exclusively.
6. Maintain causal physics: mass/energy transport → reactions → enthalpy/heat transfer → temperature/state updates.
7. Prefer physical models and conservation laws over arbitrary clamps, heuristics, or empirical fixes.
8. Validate mass and energy conservation, handoffs, units, bounds, and numerical stability after changes.