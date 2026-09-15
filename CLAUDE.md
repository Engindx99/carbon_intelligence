# CLAUDE.md

1. This is a physics-based cement pyroprocess Digital Twin; preserve physical consistency over heuristic behavior.
2. Follow the existing architecture and code structure; do not rewrite or reorganize modules without explicit approval.
3. Work incrementally: one focused task at a time, keeping changes small and reviewable.
4. Never delete, rename, or bypass existing variables, equations, states, or interfaces without explicit approval.
5. Use SI units exclusively.
6. Maintain causal physics: mass/energy transport → reactions → enthalpy/heat transfer → temperature/state updates.
7. Prefer physical models and conservation laws over arbitrary clamps, heuristics, or empirical fixes.
8. Validate mass and energy conservation, handoffs, units, bounds, and numerical stability after changes.
9. The pyroprocess is modular: Preheater, Precalciner, Transition, Burning, and Cooler are separate physical units.
10. Before making architectural or physics-level changes, explain the proposed change and wait for approval.