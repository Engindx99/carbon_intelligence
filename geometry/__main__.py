"""python -m geometry [--line KEY] [--export]

Prints the catalogue report of the configured line (or --line). With
--export, also builds every component solid and writes STEP/STL under
geometry/output/<line>/; that part needs CadQuery (requirements-cad.txt).
"""

import argparse

from geometry.catalog import reference_line
from geometry.config import reference_line_key
from geometry.report import line_report


def main(argv=None):

    parser = argparse.ArgumentParser(prog="python -m geometry")
    parser.add_argument("--line", help="catalogue key; default geometry.reference_line")
    parser.add_argument("--export", action="store_true", help="write STEP/STL")
    args = parser.parse_args(argv)

    line = reference_line(args.line or reference_line_key())
    print(line_report(line))

    if args.export:
        from geometry.components import build_component, component_names
        from geometry.export import export_solid
        from geometry.modelling import cfd_boundary_params

        cfd = cfd_boundary_params()
        print("\nSolids")

        for name in component_names(line):
            solid = build_component(line, name, cfd)
            step, _ = export_solid(solid, line.key, name)
            print(f"  {name:<9} V {solid.Volume():8.1f} m3   {step}")


if __name__ == "__main__":
    main()
