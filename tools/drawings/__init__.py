"""2D engineering drawings of the plant's equipment, built from
geometry/plant_geometry.yaml through geometry/plant_geometry.py and
written to geometry/drawings/<equipment>/ as DXF (the master), SVG and
PDF (rendered from that DXF) and JSON (every dimension with its source
and status). tools/gen_drawings.py runs them.

They draw the INNER (fluid) geometry the twin and the CFD use: no wall,
refractory, flange, support or material is drawn, because no source in
the repo gives one; each drawing lists those as Unknown.

ezdxf is not part of the twin's environment (requirements-drawings.txt).
"""
