---
paths:
  - "geometry/**"
---

- Every dimension lives once in geometry/plant_geometry.yaml; never hand-copy.
- Macro Const blocks and doc tables are generated: edit the yaml, then run `python3 tools/gen_geometry.py`; verify with `--check`.
- geometry/<equipment>/*.md are user-owned; do not rewrite or delete without being asked.
- Do not Read .dxf files (large, nondeterministic); use the JSON/inventory or render the PDF with tools/render_pdf.py.

## Exceptions to the CFD-only geometry rule (moved from CLAUDE.md rule 8)
Exception: `geometry/macros/plant_topology_2d.bas` draws a schematic, real-scale 2D drawing (SLDDRW) of the plant topology (equipment, and the gas, meal and air paths between them); it is not a CFD input.
Exception: `geometry/macros/drawings.bas` makes ISO engineering drawings of each equipment's inner (fluid) geometry from the CFD solids (`geometry/drawings/`); they are not fabrication drawings and draw no wall, flange, support or material.
Exception: `geometry/macros/pid.bas` draws the P&ID of the plant as the twin models it (4 A1 sheets, ISO 10628 / ISA 5.1 symbols; topology and instruments from `geometry/pid/pid.yaml`, line sizes from `plant_geometry.yaml`); it shows only what the twin has and is not a CFD input.
