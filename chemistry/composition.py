# ======================================================
# Raw meal composition
# Mass basis: species masses [kg]; users normalise by the sum
# ======================================================

RAW_MEAL_COMPOSITION = {

    # Free moisture at the preheater inlet: 1 wt %, the meal dried
    # in the raw mill (CEMCAP D3.2, VDZ reference plant, Table 3.2).
    # raw_meal_solid_flow normalises by the sum, so the basis no
    # longer adds up to 100 000 kg.
    "H2O": 1000,

    "Bound_H2O": 2000,

    "CaCO3": 73000, #kg

    "CaO": 0.000,

    "SiO2": 13000,
    "Al2O3": 4000,
    "Fe2O3": 3000,

    "C2S":0.0,
    "C3S":0.0,
    "C3A":0.0,
    "C4AF":0.0,
}