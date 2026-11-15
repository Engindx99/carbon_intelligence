---
name: geom-regen
description: Regenerate geometry macros/docs/drawings from plant_geometry.yaml and verify
disable-model-invocation: true
---

1. `python3 tools/gen_geometry.py` then `python3 tools/gen_geometry.py --check`
2. `python3 tools/gen_drawings.py`
3. `pytest tests/test_geometry_single_source.py tests/test_drawings.py tests/test_pid.py tests/test_plant_geometry.py tests/test_fluid_volumes.py -q`
4. Render changed PDFs with tools/render_pdf.py and view the PNG.
5. SolidWorks macros are run by the user: stop here and ask.
