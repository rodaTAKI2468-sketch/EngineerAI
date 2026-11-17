"""Support configuration classification and determinate beam analysis.

This module analyses transverse (vertical-load) Euler-Bernoulli beam statics.
It deliberately refuses unstable and statically indeterminate arrangements.
"""
from __future__ import annotations

from typing import Any

from beam_engine import analyze_beam, build_worked_solution


SUPPORT_TYPES = ("Pin", "Roller", "Fixed", "Free")


def classify_supports(support_a: str, support_b: str) -> dict[str, str]:
    """Classify end supports for a beam carrying transverse loads only."""
    if support_a not in SUPPORT_TYPES or support_b not in SUPPORT_TYPES:
        raise ValueError("Each end must be Pin, Roller, Fixed or Free.")

    if support_a == "Free" and support_b == "Free":
        return {"status": "unstable", "reason": "Both ends are free: there is no vertical or rotational restraint."}

    if support_a in ("Pin", "Roller") and support_b in ("Pin", "Roller"):
        return {
            "status": "determinate",
            "model": "simply_supported",
            "reason": "Two vertical support reactions are available; the transverse beam reactions can be found from ΣFy = 0 and ΣMA = 0.",
        }

    if support_a == "Fixed" and support_b == "Free":
        return {
            "status": "determinate",
            "model": "cantilever_a",
            "reason": "The fixed end provides one vertical reaction and one fixing moment.",
        }

    if support_a == "Free" and support_b == "Fixed":
        return {
            "status": "determinate",
            "model": "cantilever_b",
            "reason": "The fixed end at B provides one vertical reaction and one fixing moment; the beam is analysed from the fixed end.",
        }

    if support_a == "Free" or support_b == "Free":
        return {
            "status": "unstable",
            "reason": "Only one end provides a restraint, and that restraint is not a fixed support. The beam can rotate or translate as a mechanism.",
        }

    return {
        "status": "indeterminate",
        "reason": "The selected supports introduce more than two transverse reaction unknowns. Equilibrium alone is insufficient; use E, I and a compatibility/stiffness-method solver.",
    }


def _mirror_loads(length: float, loads: list[dict[str, float]], position_key: str = "position") -> list[dict[str, float]]:
    return [dict(item, **{position_key: length - float(item[position_key])}) for item in loads]


def analyze_support_configuration(
    support_a: str,
    support_b: str,
    beam_length: float,
    point_loads: list[dict[str, float]] | None = None,
    distributed_loads: list[dict[str, float]] | None = None,
    applied_moments: list[dict[str, float]] | None = None,
    youngs_modulus_gpa: float | None = None,
    second_moment_m4: float | None = None,
) -> dict[str, Any]:
    """Analyse supported determinate end configurations; reject others explicitly."""
    classification = classify_supports(support_a, support_b)
    if classification["status"] != "determinate":
        raise ValueError(classification["reason"])

    points = point_loads or []
    udls = distributed_loads or []
    couples = applied_moments or []
    model = classification["model"]

    if model == "simply_supported":
        result = analyze_beam(
            "Simply supported", beam_length, youngs_modulus_gpa, second_moment_m4,
            points, udls, couples,
        )
        worked = build_worked_solution("Simply supported", beam_length, points, udls, couples, result)
        result["reaction_a_horizontal_kN"] = 0.0
        result["reaction_b_horizontal_kN"] = 0.0
        result["support_explanation"] = (
            f"A is {support_a.lower()} and B is {support_b.lower()}. "
            "For vertical loading, each support contributes one vertical reaction. "
            "Horizontal/axial force analysis is outside this beam model."
        )
    elif model == "cantilever_a":
        result = analyze_beam(
            "Cantilever", beam_length, youngs_modulus_gpa, second_moment_m4,
            points, udls, couples,
        )
        worked = build_worked_solution("Cantilever", beam_length, points, udls, couples, result)
        result["reaction_b_kN"] = 0.0
        result["support_explanation"] = "A is fixed; B is free. The fixed support provides a vertical reaction and a fixing moment."
    else:
        mirrored_points = _mirror_loads(beam_length, points)
        mirrored_udls = [
            {"intensity": float(load["intensity"]),
             "start": beam_length - float(load["end"]),
             "end": beam_length - float(load["start"])}
            for load in udls
        ]
        mirrored_couples = _mirror_loads(beam_length, couples)
        mirrored = analyze_beam(
            "Cantilever", beam_length, youngs_modulus_gpa, second_moment_m4,
            mirrored_points, mirrored_udls, mirrored_couples,
        )
        result = dict(mirrored)
        result["x"] = beam_length - mirrored["x"][::-1]
        result["shear"] = mirrored["shear"][::-1]
        result["moment"] = mirrored["moment"][::-1]
        result["deflection"] = (
            None if mirrored["deflection"] is None else mirrored["deflection"][::-1]
        )
        result["reaction_a_kN"] = 0.0
        result["reaction_b_kN"] = mirrored["reaction_a_kN"]
        result["fixed_moment_a_kNm"] = 0.0
        result["fixed_moment_b_kNm"] = mirrored["fixed_moment_a_kNm"]
        result["max_shear_position_m"] = beam_length - mirrored["max_shear_position_m"]
        result["max_moment_position_m"] = beam_length - mirrored["max_moment_position_m"]
        if mirrored["max_deflection_position_m"] is not None:
            result["max_deflection_position_m"] = beam_length - mirrored["max_deflection_position_m"]
        worked = {
            "support_note": "A is free and B is fixed. Reverse the coordinate direction and analyse from the fixed end B.",
            "reaction_steps": [
                "Take moments and vertical forces about the fixed end B.",
                f"R_B = {mirrored['reaction_a_kN']:.4g} kN (vertical reaction).",
                f"M_B = {mirrored['fixed_moment_a_kNm']:.4g} kN·m (fixing moment).",
            ],
            "point_load_steps": [],
            "udl_steps": [],
            "couple_steps": [],
            "intervals": [],
            "boundary_note": "At the free end A, shear and bending moment are zero when no end force or couple is applied.",
            "applied_moment_note": "Applied couples cause a jump in the bending-moment diagram.",
        }
        result["support_explanation"] = "A is free and B is fixed. Loads are mirrored mathematically so the existing cantilever solver can analyse from B."

    result["support_classification"] = classification
    result["support_a"] = support_a
    result["support_b"] = support_b
    result["fixed_moment_b_kNm"] = result.get("fixed_moment_b_kNm", 0.0)
    result["worked_solution"] = worked
    return result
