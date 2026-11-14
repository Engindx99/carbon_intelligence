"""The P&ID's symbols and the ports a line may start or end on.

The ports mirror the CFD boundary names where a CFD solid exists
(calciner, cooler, cyclones). SRC / SNK are the plant's boundary
terminals; their names are listed here.
"""

# symbol -> ports
SYMBOLS = {
    "cyclone": {"gas_in", "gas_out", "dust_out", "dust_esc"},
    "riser": {"gas_in", "gas_out", "meal_in"},
    "feed_chute": {"in", "out", "dust_in"},
    "flap_valve": {"in", "out"},
    "fan": {"gas_in", "gas_out"},
    "vessel": {"kiln_gas_inlet", "tertiary_air_inlet", "meal_feed", "fuel_inlet", "gas_outlet"},
    "gooseneck": {"gas_in", "gas_out"},
    "duct": {"air_in", "air_out"},
    "nozzle_meal": {"meal_in", "meal_out"},
    "nozzle_fuel": {"fuel_in", "fuel_out"},
    "chamber": {"gas_in", "gas_out", "meal_in", "meal_out"},
    "hood": {"sec_in", "sec_out", "ter_in", "ter_out"},
    "rotary_kiln": {"burner_in", "air_in", "meal_in", "gas_out", "clinker_out"},
    "burner": {"air_in", "fuel_in", "flame_out"},
    "grate_cooler": {"grate_air", "hood_1", "hood_2", "vent_outlet", "clinker_in", "clinker_out"},
}

SOURCES = {"raw_meal", "fuel_kiln", "fuel_calciner", "primary_air", "cooler_air"}
SINKS = {"stack", "clinker", "cooler_vent"}

# service -> (line-number letter, layer)
SERVICES = {
    "gas": ("G", "GAZ"),
    "meal_raw": ("M", "FARIN"),
    "meal_hot": ("M", "FARIN"),
    "dust": ("D", "TOZ"),
    "air_primary": ("A", "HAVA"),
    "air_hot": ("A", "GAZ"),
    "air_cooler": ("A", "HAVA"),
    "fuel": ("F", "YAKIT"),
    "clinker": ("K", "KLINKER"),
}
