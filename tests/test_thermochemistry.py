"""
The clinker phase enthalpies, re-derived from formation data.

These four constants were all positive -- coded as endothermic sinks --
when three of the four reactions are exothermic. That single group of
signs was worth an 8 MW swing at plant scale, and no energy balance
could see it: a reaction heat enters every balance on the OUT side, so
a wrong dH closes perfectly and just moves the temperature.

So the values are not asserted against themselves. Each one is rebuilt
here from standard enthalpies of formation and molar masses that this
file states independently of chemistry/, and the reaction the model
actually implements is read back out of the model's own stoichiometry
ratios. A sign flip, a basis mix-up (per kg product vs per kg limiting
reactant) or a transcription slip all fail.

The same table and the same arithmetic are checked against calcination,
whose enthalpy came into the model from an unrelated source. That is the
control: if the method reproduces 1.78e6 J/kg CaCO3, it is not inventing
the other four.
"""

import unittest

from chemistry.alite import AliteModel
from chemistry.belite import BeliteModel
from chemistry.c3a import C3AModel
from chemistry.c4af import C4AFModel
from chemistry.calcination import CalcinationModel


# Standard enthalpies of formation at 298.15 K [kJ/mol].
HF = {
    "CaO": -635.09,
    "SiO2": -910.70,
    "Al2O3": -1675.70,
    "Fe2O3": -824.20,
    "CaCO3": -1206.90,
    "CO2": -393.51,
    "C2S": -2307.50,
    "C3S": -2927.80,
    "C3A": -3587.80,
    "C4AF": -5080.00,
}

# Molar masses [g/mol].
M = {
    "CaO": 56.08,
    "SiO2": 60.08,
    "Al2O3": 101.96,
    "Fe2O3": 159.69,
    "CaCO3": 100.09,
    "CO2": 44.01,
    "C2S": 172.24,
    "C3S": 228.32,
    "C3A": 270.20,
    "C4AF": 485.97,
}


def reaction_enthalpy(reactants, product):
    """dH [kJ/mol] for reactants -> 1 mol product."""

    return HF[product] - sum(n * HF[s] for s, n in reactants.items())


def per_kg_of(dH_kJ_per_mol, basis):
    """dH [J/kg] on the mass basis of one named species."""

    return dH_kJ_per_mol * 1.0e6 / M[basis]


class ClinkerPhaseEnthalpyTest(unittest.TestCase):

    # reactants, product, and the LIMITING REACTANT the model
    # writes its dH against (chemistry/base.py heat_sink()
    # multiplies dH by the limiting reactant's mass).
    REACTIONS = {
        "belite": (
            BeliteModel,
            {"CaO": 2, "SiO2": 1},
            "C2S",
            "SiO2",
        ),
        "alite": (
            AliteModel,
            {"CaO": 1, "C2S": 1},
            "C3S",
            "C2S",
        ),
        "c3a": (
            C3AModel,
            {"CaO": 3, "Al2O3": 1},
            "C3A",
            "Al2O3",
        ),
        "c4af": (
            C4AFModel,
            {"CaO": 4, "Al2O3": 1, "Fe2O3": 1},
            "C4AF",
            "Al2O3",
        ),
    }

    def test_enthalpies_match_formation_data(self):

        for name, (cls, reac, prod, basis) in self.REACTIONS.items():
            with self.subTest(phase=name):

                expected = per_kg_of(
                    reaction_enthalpy(reac, prod),
                    basis,
                )

                # 1% covers the rounding in the stored constants
                # without admitting a different value.
                self.assertAlmostEqual(
                    cls().deltaH / expected,
                    1.0,
                    delta=0.01,
                    msg=(
                        f"{name}: model {cls().deltaH:.4e} J/kg {basis}, "
                        f"formation data gives {expected:.4e}"
                    ),
                )

    def test_only_alite_is_endothermic(self):
        """Three of the four clinkering reactions release heat.

        This is the property that was wrong, stated directly so it
        cannot regress behind a plausible-looking magnitude.
        """

        self.assertLess(BeliteModel().deltaH, 0.0)
        self.assertLess(C3AModel().deltaH, 0.0)
        self.assertLess(C4AFModel().deltaH, 0.0)

        self.assertGreater(AliteModel().deltaH, 0.0)

    def test_belite_dominates_the_group(self):
        """Belite carries the group, per kg of its own basis.

        It was the phase the raw constants disguised: 5.0e5 next to
        alite's 6.0e5 looked like the smaller term, while on a shared
        basis it is an order of magnitude larger and of the opposite
        sign.
        """

        others = [
            abs(AliteModel().deltaH),
            abs(C3AModel().deltaH),
            abs(C4AFModel().deltaH),
        ]

        self.assertGreater(abs(BeliteModel().deltaH), 4.0 * max(others))

    def test_model_stoichiometry_matches_the_assumed_reaction(self):
        """The reactions above must be the ones the models implement.

        Without this, the enthalpy check could be validating the right
        arithmetic against the wrong reaction.
        """

        belite = BeliteModel()
        self.assertAlmostEqual(
            belite.CaO_required,
            2 * M["CaO"] / M["SiO2"],
            places=3,
        )
        self.assertAlmostEqual(
            belite.C2S_produced,
            M["C2S"] / M["SiO2"],
            places=3,
        )

        alite = AliteModel()
        self.assertAlmostEqual(
            alite.CaO_required,
            M["CaO"] / M["C2S"],
            places=3,
        )
        self.assertAlmostEqual(
            alite.C3S_produced,
            M["C3S"] / M["C2S"],
            places=3,
        )

        c3a = C3AModel()
        self.assertAlmostEqual(
            c3a.CaO_required,
            3 * M["CaO"] / M["Al2O3"],
            places=3,
        )

        c4af = C4AFModel()
        self.assertAlmostEqual(
            c4af.CaO_required,
            4 * M["CaO"] / M["Al2O3"],
            places=3,
        )
        self.assertAlmostEqual(
            c4af.Fe2O3_required,
            M["Fe2O3"] / M["Al2O3"],
            places=3,
        )


class MethodControlTest(unittest.TestCase):
    """Calcination is the control on the method, not a target.

    Its enthalpy entered the model from a different source than this
    file's formation table. If the two agree, the table and the
    arithmetic used for the four clinker phases are sound.
    """

    def test_calcination_reproduces_the_independent_value(self):

        # CaCO3 -> CaO + CO2
        dH = (HF["CaO"] + HF["CO2"]) - HF["CaCO3"]

        derived = per_kg_of(dH, "CaCO3")

        self.assertAlmostEqual(
            derived / CalcinationModel().deltaH,
            1.0,
            delta=0.01,
        )

        # Endothermic, and the largest single reaction in the plant.
        self.assertGreater(CalcinationModel().deltaH, 0.0)


if __name__ == "__main__":
    unittest.main()
