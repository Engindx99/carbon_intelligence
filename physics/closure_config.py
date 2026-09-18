"""
Faz 5 closure settings, read once per zone construction.

Kept in its own module so the two rotating zones read the SAME
material properties from the SAME place. Copying the block into each
zone is how transition ended up with its own inlined area formula in
the first place (audit B3).
"""

from physics.physics import CONTACT_GAP_CHI_RANGE


class ClosureSettings:

    __slots__ = (
        "bed_emissivity",
        "wall_emissivity",
        "particle_diameter",
        "bed_conductivity",
        "contact_chi",
    )

    def __init__(
        self,
        bed_emissivity,
        wall_emissivity,
        particle_diameter,
        bed_conductivity,
        contact_chi,
    ):

        for name, value in (
            ("bed_emissivity", bed_emissivity),
            ("wall_emissivity", wall_emissivity),
        ):
            if not (0.0 < value <= 1.0):
                raise ValueError(
                    f"kiln_closure.{name} must be in (0, 1], got {value}"
                )

        for name, value in (
            ("particle_diameter_m", particle_diameter),
            ("bed_conductivity", bed_conductivity),
        ):
            if value <= 0.0:
                raise ValueError(
                    f"kiln_closure.{name} must be > 0, got {value}"
                )

        chi_min, chi_max = CONTACT_GAP_CHI_RANGE

        if not (chi_min <= contact_chi <= chi_max):
            raise ValueError(
                f"kiln_closure.contact_gap_chi must be in "
                f"[{chi_min}, {chi_max}], got {contact_chi}"
            )

        self.bed_emissivity = float(bed_emissivity)
        self.wall_emissivity = float(wall_emissivity)
        self.particle_diameter = float(particle_diameter)
        self.bed_conductivity = float(bed_conductivity)
        self.contact_chi = float(contact_chi)


def closure_settings(cfg):
    """Build the Faz 5 closure settings from a loaded config dict."""

    section = (cfg or {}).get("kiln_closure", {}) or {}

    return ClosureSettings(
        bed_emissivity=section.get("bed_emissivity", 0.90),
        wall_emissivity=section.get("wall_emissivity", 0.85),
        particle_diameter=section.get("particle_diameter_m", 1.0e-3),
        bed_conductivity=section.get("bed_conductivity", 0.4),
        contact_chi=section.get("contact_gap_chi", 0.147),
    )
