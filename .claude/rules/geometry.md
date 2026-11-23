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
Exception: `geometry/macros/kiln_wall.bas` builds the kiln's wall as the twin models it (one brick tube innermost at the flow bore, one steel shell tube outside, over the whole kiln; the zones' brick grades are a model split, no joint; no coating for now; physics/shell.py) with the two ISO 5417 end rings built brick by brick, and `drawings.bas kiln` draws it with the kiln's gas bore on the one kiln sheet (`geometry/drawings/kiln/`; user, 22 Nov 2026) (user request, 22 Nov 2026); neither is a CFD input or a fabrication drawing.
Exception: `geometry/macros/kiln_rotax.bas` builds the kiln's mechanical parts after FLS ROTAX-2 (tyres with tangential suspension, roller stations, friction drive, thrust device, seals, cooling fans, piers, walkway) as simple envelopes laid out by `plant_geometry.kiln_rotax()` (user request, 22 Nov 2026: the kiln's dimensions stay, only these parts are added), and `drawings.bas kiln_rotax` draws them (`geometry/drawings/kiln_rotax/`, the kiln shell as a phantom outline); not a CFD input or a fabrication drawing.
Exception: `geometry/macros/kiln_burner_body.bas` builds the whole kiln burner (JETFLEX 2.0) as simple envelopes laid out by `plant_geometry.kiln_burner_body()` (brochure side-view ratios of the tip D; user request, 22 Nov 2026), and `drawings.bas kiln_burner_body` draws it (`geometry/drawings/kiln_burner_body/`); not a CFD input or a fabrication drawing. The CFD input is the channel solid `kiln_burner.bas` (sheet `kiln_burner`).
