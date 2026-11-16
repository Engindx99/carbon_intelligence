"""Belite forms in the calciner (ChemistryModel.react_calciner_belite).

The riser runs at 1100-1160 K, inside the 815-920 C range Alonso et
al. 2019 fitted their Jander law on; CEMCAP D3.2 Fig. 3.4 has ~30 %
of the silica combined at the kiln inlet. The march must be the
exact Jander integral, conserve solid mass, and hand its conversion
on so the kiln continues from it instead of counting it again.
"""

import unittest
from types import SimpleNamespace

import numpy as np

from chemistry.phases import get_cell_solid_flow, raw_meal_solid_flow, total_solid_flow
from chemistry.phases import set_cell_solid_flow, SolidPhases
from chemistry.reactions import ChemistryModel


def _calcined_inlet():
    """Raw meal with its CaCO3 already calcined, so the CaO cap does
    not depend on the calcination march [kg/s]."""

    flow = raw_meal_solid_flow(90.0)
    chem = ChemistryModel()
    flow["CaO"] += flow["CaCO3"] * chem.calcination.CaO_ratio
    flow["CaCO3"] = 0.0
    return flow


def _state(T, N):
    return SimpleNamespace(
        Ts_calciner=np.full(N, float(T)),
        m_dot_CaCO3_out_cells=np.zeros(N),
    )


class TheMarchIsTheJanderIntegralTest(unittest.TestCase):

    def test_n_cells_equal_one_cell_of_the_whole_residence(self):
        chem = ChemistryModel()
        inlet = _calcined_inlet()
        T, dz, u_s, N = 1150.0, 1.0, 2.0, 20

        state = chem.react_calciner_belite(_state(T, N), dz, u_s, inlet)

        k = float(chem.belite.reaction_rate(T))
        whole = chem.belite.jander_reacted(dict(inlet), k, N * dz / u_s)

        self.assertGreater(whole, 0.0)
        self.assertAlmostEqual(
            float(np.sum(state.Calciner_belite_SiO2_reacted_cells)) / whole,
            1.0,
            places=9,
        )

    def test_the_heat_is_the_exotherm_of_what_reacted(self):
        chem = ChemistryModel()
        state = chem.react_calciner_belite(
            _state(1150.0, 10), 1.0, 2.0, _calcined_inlet()
        )
        reacted = float(np.sum(state.Calciner_belite_SiO2_reacted_cells))
        self.assertLess(state.Calciner_belite_Q_sink, 0.0)
        self.assertAlmostEqual(
            state.Calciner_belite_Q_sink, reacted * chem.belite.deltaH, places=3
        )

    def test_no_inlet_flow_forms_nothing(self):
        state = ChemistryModel().react_calciner_belite(
            _state(1150.0, 5), 1.0, 2.0, None
        )
        self.assertEqual(state.Calciner_belite_Q_sink, 0.0)
        self.assertFalse(np.any(state.Calciner_belite_Q_cells))


class TheKilnContinuesFromItTest(unittest.TestCase):
    """The conversion travels in the species (X = 2 n_Si,comb / n_Ca),
    so calciner then kiln equals one Jander integral over both."""

    def test_calciner_then_kiln_is_one_integral(self):
        chem = ChemistryModel()
        belite = chem.belite
        inlet = _calcined_inlet()
        T, dz, u_s, N = 1150.0, 1.0, 2.0, 10
        tau_kiln = 30.0

        state = chem.react_calciner_belite(_state(T, N), dz, u_s, inlet)
        done = float(np.sum(state.Calciner_belite_SiO2_reacted_cells))

        handed = dict(inlet)
        handed["SiO2"] -= done
        handed["CaO"] -= done * belite.CaO_required
        handed["C2S"] += done * belite.C2S_produced

        k = float(belite.reaction_rate(T))
        kiln = belite.jander_reacted(handed, k, tau_kiln)
        whole = belite.jander_reacted(dict(inlet), k, N * dz / u_s + tau_kiln)

        self.assertAlmostEqual((done + kiln) / whole, 1.0, places=9)


class TheProfileConservesTest(unittest.TestCase):

    def test_solid_mass_and_silicon(self):
        chem = ChemistryModel()
        inlet = _calcined_inlet()
        N = 8

        state = chem.react_calciner_belite(_state(1150.0, N), 1.0, 2.0, inlet)

        solids = SolidPhases(**{
            name: np.zeros(N) for name in SolidPhases.__dataclass_fields__
        })
        for i in range(N):
            set_cell_solid_flow(solids, i, dict(inlet))

        chem.calciner_belite_flow_profile(state, solids)

        M_SiO2, M_C2S = 60.08, 172.24
        for i in range(N):
            cell = get_cell_solid_flow(solids, i)
            with self.subTest(cell=i):
                self.assertAlmostEqual(
                    total_solid_flow(cell), total_solid_flow(inlet), places=9
                )
                self.assertAlmostEqual(
                    cell["SiO2"] / M_SiO2 + cell["C2S"] / M_C2S,
                    inlet["SiO2"] / M_SiO2,
                    places=9,
                )
        self.assertGreater(get_cell_solid_flow(solids, N - 1)["C2S"], 0.0)


if __name__ == "__main__":
    unittest.main()
