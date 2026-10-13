"""The clinkering prefactors are consequences of stated anchors
(chemistry/base.py, "CLINKER KINETICS: CALIBRATED, AND SAID SO").

Each k0 is re-derived here from its anchor and from the plant
chemistry statements the anchors encode, rather than read back as
a number, so the test fails if a constant drifts from its reason.
"""

import math
import unittest

from chemistry.alite import AliteModel
from chemistry.base import anchored_prefactor
from chemistry.belite import BeliteModel
from chemistry.c3a import C3AModel
from chemistry.c4af import C4AFModel
from chemistry.composition import RAW_MEAL_COMPOSITION

R = 8.314

# Mastorakos et al. (1999), via Ritschel et al. 2024 Table A.1 and
# Svensen et al. 2025 Table 5 [J/mol]
MASTORAKOS_EA = {
    BeliteModel: 240e3,
    AliteModel: 420e3,
    C3AModel: 310e3,
    C4AFModel: 330e3,
}


def _conversion(model, T, t):
    return 1.0 - math.exp(-float(model.reaction_rate(T)) * t)


def _free_lime_before_alite():
    """CaO left once belite, C3A and C4AF have taken theirs, and the
    clinker mass, from the raw meal [kg per 100 t meal]."""

    m = RAW_MEAL_COMPOSITION
    CaO = m["CaCO3"] * 56.08 / 100.09
    Fe2O3 = m["Fe2O3"]
    Al2O3 = m["Al2O3"]
    SiO2 = m["SiO2"]

    c4af = C4AFModel()
    Al_c4af = Fe2O3 / c4af.Fe2O3_required
    CaO -= Al_c4af * c4af.CaO_required
    CaO -= (Al2O3 - Al_c4af) * C3AModel().CaO_required
    CaO -= SiO2 * BeliteModel().CaO_required

    clinker = m["CaCO3"] * 56.08 / 100.09 + SiO2 + Al2O3 + Fe2O3

    return CaO, clinker


class TheShapeIsMastorakosTest(unittest.TestCase):

    def test_activation_energies(self):
        for cls, Ea in MASTORAKOS_EA.items():
            with self.subTest(reaction=cls.__name__):
                self.assertEqual(cls().activation_energy, Ea)


class TheSolidStateReactionsAreDoneBelow1300CTest(unittest.TestCase):
    """Belite, aluminate and ferrite form from 650-900 C and are
    "complete below 1300 C" (cementkilns.co.uk)."""

    def test_the_anchor_holds(self):
        for cls in (BeliteModel, C3AModel, C4AFModel):
            with self.subTest(reaction=cls.__name__):
                self.assertAlmostEqual(
                    _conversion(cls(), 1473.0, 600.0), 0.99, places=9
                )

    def test_nothing_forms_below_onset(self):
        for cls, T0 in ((BeliteModel, 923.0), (C3AModel, 973.0), (C4AFModel, 973.0)):
            with self.subTest(reaction=cls.__name__):
                self.assertEqual(float(cls().reaction_rate(T0 - 1.0)), 0.0)


class AliteNeedsTheMeltTest(unittest.TestCase):

    def test_no_alite_without_liquid(self):
        """"only begins to form when liquid is formed", 1300-1425 C."""
        for T in (1300.0, 1500.0, 1573.0):
            with self.subTest(T=T):
                self.assertEqual(float(AliteModel().reaction_rate(T)), 0.0)

    def test_free_lime_lands_at_the_anchor(self):
        """1.25 % of clinker after 900 s at 1450 C."""

        CaO, clinker = _free_lime_before_alite()
        self.assertAlmostEqual(CaO, 8978.8, delta=0.1)
        self.assertAlmostEqual(clinker, 60901.6, delta=0.1)

        left = CaO * (1.0 - _conversion(AliteModel(), 1723.0, 900.0))
        self.assertAlmostEqual(left / clinker, 0.0125, places=9)


class TheHelperTest(unittest.TestCase):

    def test_round_trip(self):
        k0 = anchored_prefactor(2.0e5, 1500.0, 100.0, 0.5)
        k = k0 * math.exp(-2.0e5 / (R * 1500.0))
        self.assertAlmostEqual(1.0 - math.exp(-k * 100.0), 0.5, places=12)

    def test_rejects_a_bad_anchor(self):
        for args in ((1e5, 1500.0, 100.0, 1.0), (1e5, 1500.0, 0.0, 0.5)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    anchored_prefactor(*args)


if __name__ == "__main__":
    unittest.main()
