"""Equilibrium-only analysis for statically determinate multiple-support beams.

Units: kN, m and kN.m. Positive vertical loads act upward;
positive applied couples are counter-clockwise.
"""
from __future__ import annotations

import numpy as np


def analyze_determinate_multiple_support_beam(
    beam_length, supports, point_loads=None, distributed_loads=None,
    applied_moments=None, samples=1201,
):
    """Analyse a beam with exactly two vertical simple supports using statics.

    This mode intentionally does not calculate deflection and does not require E or I.
    Fixed supports and more than two supports are indeterminate for this model.
    """
    point_loads = point_loads or []
    distributed_loads = distributed_loads or []
    applied_moments = applied_moments or []
    length = float(beam_length)
    if not np.isfinite(length) or length <= 0:
        raise ValueError("Beam length must be greater than zero.")
    if len(supports) != 2:
        raise ValueError(
            "Exam/statics mode requires exactly two supports. "
            "A beam with more than two supports is statically indeterminate; "
            "use stiffness/deflection mode with E and I."
        )
    ordered = sorted(supports, key=lambda item: float(item["position"]))
    for i, support in enumerate(ordered, 1):
        x = float(support["position"])
        if not np.isfinite(x) or x < 0 or x > length:
            raise ValueError(f"Support {i} must be positioned between 0 and the beam length.")
        if support["type"] not in {"Pin", "Roller"}:
            raise ValueError(
                "Exam/statics mode supports Pin and Roller only. "
                "A Fixed support introduces an unknown reaction moment."
            )
    x1, x2 = (float(s["position"]) for s in ordered)
    if x2 - x1 <= 1e-9:
        raise ValueError("The two supports must be at different positions.")

    for i, load in enumerate(point_loads, 1):
        x, p = float(load["position"]), float(load["magnitude"])
        if not np.isfinite(x) or not np.isfinite(p) or x < 0 or x > length:
            raise ValueError(f"Point load {i} must have a finite value and lie on the beam.")
    for i, load in enumerate(distributed_loads, 1):
        a, b, q = float(load["start"]), float(load["end"]), float(load["intensity"])
        if not all(np.isfinite(v) for v in (a, b, q)) or a < 0 or b > length or a >= b:
            raise ValueError(f"UDL {i} must satisfy 0 ≤ start < end ≤ beam length.")
    for i, load in enumerate(applied_moments, 1):
        x, m = float(load["position"]), float(load["magnitude"])
        if not np.isfinite(x) or not np.isfinite(m) or x < 0 or x > length:
            raise ValueError(f"Applied moment {i} must have a finite value and lie on the beam.")

    total_force = sum(float(p["magnitude"]) for p in point_loads)
    total_moment_about_a = sum(
        float(p["magnitude"]) * (float(p["position"]) - x1) for p in point_loads
    )
    for load in distributed_loads:
        a, b, q = float(load["start"]), float(load["end"]), float(load["intensity"])
        resultant = q * (b - a)
        centroid = (a + b) / 2.0
        total_force += resultant
        total_moment_about_a += resultant * (centroid - x1)
    total_moment_about_a += sum(float(m["magnitude"]) for m in applied_moments)

    r2 = -total_moment_about_a / (x2 - x1)
    r1 = -total_force - r2
    reactions = [
        {"position": x1, "type": ordered[0]["type"], "vertical_kN": r1, "moment_kNm": 0.0},
        {"position": x2, "type": ordered[1]["type"], "vertical_kN": r2, "moment_kNm": 0.0},
    ]

    # Include event coordinates so point-load and couple locations are represented.
    events = [0.0, length, x1, x2]
    events.extend(float(p["position"]) for p in point_loads)
    events.extend(float(m["position"]) for m in applied_moments)
    for load in distributed_loads:
        events.extend([float(load["start"]), float(load["end"])])
    x = np.unique(np.concatenate([np.linspace(0.0, length, max(101, int(samples))), events]))
    shear = np.zeros_like(x)
    moment = np.zeros_like(x)
    for j, xx in enumerate(x):
        for reaction in reactions:
            if reaction["position"] <= xx:
                shear[j] += reaction["vertical_kN"]
                moment[j] += reaction["vertical_kN"] * (xx - reaction["position"])
        for load in point_loads:
            if float(load["position"]) <= xx:
                shear[j] += float(load["magnitude"])
                moment[j] += float(load["magnitude"]) * (xx - float(load["position"]))
        for load in distributed_loads:
            a, b, q = float(load["start"]), float(load["end"]), float(load["intensity"])
            loaded_length = max(0.0, min(xx, b) - a)
            if loaded_length > 0:
                resultant = q * loaded_length
                centroid = a + loaded_length / 2.0
                shear[j] += resultant
                moment[j] += resultant * (xx - centroid)
        for couple in applied_moments:
            if float(couple["position"]) <= xx:
                moment[j] -= float(couple["magnitude"])

    force_residual = r1 + r2 + total_force
    moment_residual = r1 * x1 + r2 * x2
    moment_residual += sum(float(p["magnitude"]) * float(p["position"]) for p in point_loads)
    moment_residual += sum(
        float(w["intensity"]) * (float(w["end"]) - float(w["start"]))
        * (float(w["start"]) + float(w["end"])) / 2.0 for w in distributed_loads
    )
    moment_residual += sum(float(m["magnitude"]) for m in applied_moments)
    return {
        "x": x, "shear": shear, "moment": moment,
        "support_reactions": reactions,
        "max_shear_kN": float(np.max(np.abs(shear))),
        "max_moment_kNm": float(np.max(np.abs(moment))),
        "max_moment_position_m": float(x[int(np.argmax(np.abs(moment)))]),
        "force_equilibrium_error_kN": float(force_residual),
        "moment_equilibrium_error_kNm": float(moment_residual),
        "reaction_steps": [
            f"ΣFy = 0: R_A + R_B + ({total_force:.6g}) = 0",
            f"ΣM_A = 0: R_B × ({x2-x1:.6g}) + ({total_moment_about_a:.6g}) = 0",
            f"R_B = {r2:.6g} kN",
            f"R_A = {r1:.6g} kN",
        ],
    }
