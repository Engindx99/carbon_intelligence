from dataclasses import dataclass
import numpy as np

from chemistry.phases import SolidPhases, GasPhases


@dataclass
class ZoneMaterial:
    solids: SolidPhases
    gases: GasPhases


def build_zone_material(N, cell):

    return ZoneMaterial(
        solids=SolidPhases(
            H2O=cell("H2O"),
            Bound_H2O=cell("Bound_H2O"),
            CaCO3=cell("CaCO3"),
            CaO=cell("CaO"),
            SiO2=cell("SiO2"),
            Al2O3=cell("Al2O3"),
            Fe2O3=cell("Fe2O3"),
            C2S=cell("C2S"),
            C3S=cell("C3S"),
            C3A=cell("C3A"),
            C4AF=cell("C4AF"),
        ),
        gases=GasPhases(
            CO2=np.zeros(N, dtype=float),
            H2O=np.zeros(N, dtype=float),
        ),
    )