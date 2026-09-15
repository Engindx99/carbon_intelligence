def validate_mass(
    mass_in,
    mass_out,
    mass_source=0.0,
    absolute_tolerance=1e-6,
    relative_tolerance=1e-9,
):
    residual = (
        mass_in
        + mass_source
        - mass_out
    )

    scale = max(
        abs(mass_in),
        abs(mass_out),
        abs(mass_source),
        1.0,
    )

    relative_residual = abs(residual) / scale

    converged = (
        abs(residual) <= absolute_tolerance
        or relative_residual <= relative_tolerance
    )

    return {
        "mass_in": float(mass_in),
        "mass_source": float(mass_source),
        "mass_out": float(mass_out),
        "residual": float(residual),
        "relative_residual": float(relative_residual),
        "absolute_tolerance": float(absolute_tolerance),
        "relative_tolerance": float(relative_tolerance),
        "converged": converged,
    }
