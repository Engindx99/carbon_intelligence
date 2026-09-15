from reporter.json_logger import log_validation


def report_validation(
    result,
    equipment,
    balance_type="energy",
):

    status = (
        "PASS"
        if result["converged"]
        else "FAIL"
    )

    if "mass_in" in result:
        flow_in, flow_source, flow_out = (
            "mass_in",
            "mass_source",
            "mass_out",
        )
    else:
        flow_in, flow_source, flow_out = (
            "energy_in",
            "energy_source",
            "energy_out",
        )

    validation = {
        "equipment": equipment,
        "balance_type": balance_type,
        "status": status,
        flow_in: result[flow_in],
        flow_source: result[flow_source],
        flow_out: result[flow_out],
        "residual": result["residual"],
        "relative_residual": result["relative_residual"],
        "absolute_tolerance": result[
            "absolute_tolerance"
        ],
        "relative_tolerance": result[
            "relative_tolerance"
        ],
    }

    log_validation(validation)

    return validation