"""Beam analysis engine for EngineerAI.

Sign convention:
- Upward forces are positive; downward forces are negative.
- Counter-clockwise applied couples are positive.
- Sagging bending moments are positive.
- Deflection is reported positive downward.
All inputs and output diagrams use kN, m, kN/m and kN.m unless noted.
"""
from __future__ import annotations

from typing import Any

import numpy as np


def _validate_inputs(
    beam_type: str,
    beam_length: float,
    youngs_modulus_gpa: float | None,
    second_moment_m4: float | None,
    point_loads: list[dict[str, float]],
    distributed_loads: list[dict[str, float]],
    applied_moments: list[dict[str, float]],
) -> None:
    if beam_type not in {"Simply supported", "Cantilever"}:
        raise ValueError("Choose a simply supported beam or a cantilever.")
    if not np.isfinite(beam_length) or beam_length <= 0:
        raise ValueError("Beam length must be greater than zero.")
    if (youngs_modulus_gpa is None) != (second_moment_m4 is None):
        raise ValueError("Enter both E and I to calculate deflection, or leave both blank for statics only.")
    if youngs_modulus_gpa is not None and (
        not np.isfinite(youngs_modulus_gpa) or youngs_modulus_gpa <= 0
    ):
        raise ValueError("Young's modulus must be greater than zero.")
    if second_moment_m4 is not None and (
        not np.isfinite(second_moment_m4) or second_moment_m4 <= 0
    ):
        raise ValueError("Second moment of area must be greater than zero.")

    tol = 1e-9
    for index, load in enumerate(point_loads, start=1):
        magnitude = float(load["magnitude"])
        position = float(load["position"])
        if not np.isfinite(magnitude):
            raise ValueError(f"Point load {index}: magnitude must be a finite number.")
        if not np.isfinite(position) or position < -tol or position > beam_length + tol:
            raise ValueError(f"Point load {index}: position must be between 0 and the beam length.")

    for index, load in enumerate(distributed_loads, start=1):
        intensity = float(load["intensity"])
        start = float(load["start"])
        end = float(load["end"])
        if not np.isfinite(intensity):
            raise ValueError(f"UDL {index}: intensity must be a finite number.")
        if not (np.isfinite(start) and np.isfinite(end)):
            raise ValueError(f"UDL {index}: start and end positions must be finite numbers.")
        if start < -tol or end > beam_length + tol or start >= end:
            raise ValueError(f"UDL {index}: require 0 ≤ start < end ≤ beam length.")

    for index, moment in enumerate(applied_moments, start=1):
        magnitude = float(moment["magnitude"])
        position = float(moment["position"])
        if not np.isfinite(magnitude):
            raise ValueError(f"Applied moment {index}: magnitude must be a finite number.")
        if not np.isfinite(position) or position < -tol or position > beam_length + tol:
            raise ValueError(f"Applied moment {index}: position must be between 0 and the beam length.")


def _load_resultants(
    point_loads: list[dict[str, float]],
    distributed_loads: list[dict[str, float]],
    applied_moments: list[dict[str, float]],
) -> tuple[float, float]:
    """Return total vertical force (kN) and total moment about A (kN.m)."""
    total_force = sum(float(load["magnitude"]) for load in point_loads)
    total_moment = sum(
        float(load["magnitude"]) * float(load["position"])
        for load in point_loads
    )

    for load in distributed_loads:
        intensity = float(load["intensity"])
        start = float(load["start"])
        end = float(load["end"])
        resultant = intensity * (end - start)
        centroid = (start + end) / 2.0
        total_force += resultant
        total_moment += resultant * centroid

    total_moment += sum(float(moment["magnitude"]) for moment in applied_moments)
    return total_force, total_moment


def _cumulative_trapezoid(values: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Small NumPy-only cumulative trapezoidal integration helper."""
    result = np.zeros_like(x, dtype=float)
    if len(x) > 1:
        increments = 0.5 * (values[:-1] + values[1:]) * np.diff(x)
        result[1:] = np.cumsum(increments)
    return result


def analyze_beam(
    beam_type: str,
    beam_length: float,
    youngs_modulus_gpa: float | None = None,
    second_moment_m4: float | None = None,
    point_loads: list[dict[str, float]] | None = None,
    distributed_loads: list[dict[str, float]] | None = None,
    applied_moments: list[dict[str, float]] | None = None,
    samples: int = 1401,
) -> dict[str, Any]:
    """Calculate reactions, SFD, BMD and elastic deflection.

    Load dictionaries:
      point load: {"magnitude": signed_kN, "position": m}
      UDL: {"intensity": signed_kN_per_m, "start": m, "end": m}
      couple: {"magnitude": signed_kN_m, "position": m}

    Negative force/intensity means downward. Positive couple means CCW.
    """
    point_loads = point_loads or []
    distributed_loads = distributed_loads or []
    applied_moments = applied_moments or []

    _validate_inputs(
        beam_type,
        beam_length,
        youngs_modulus_gpa,
        second_moment_m4,
        point_loads,
        distributed_loads,
        applied_moments,
    )

    total_force, total_moment_a = _load_resultants(
        point_loads, distributed_loads, applied_moments
    )

    if beam_type == "Simply supported":
        reaction_b = -total_moment_a / beam_length
        reaction_a = -total_force - reaction_b
        fixed_moment_a = 0.0
    else:
        reaction_a = -total_force
        reaction_b = 0.0
        fixed_moment_a = -total_moment_a

    # Include every load boundary in the evaluation grid so jumps and
    # changes in distributed loading are represented in the diagrams.
    x_parts = [np.linspace(0.0, beam_length, max(int(samples), 101))]
    event_positions: list[float] = []
    for load in point_loads:
        event_positions.append(float(load["position"]))
    for load in distributed_loads:
        event_positions.extend([float(load["start"]), float(load["end"])])
    for moment in applied_moments:
        event_positions.append(float(moment["position"]))

    eps = max(beam_length * 1e-9, 1e-10)
    for position in event_positions:
        x_parts.append(np.array([position]))
        if any(abs(float(moment["position"]) - position) < 1e-10 for moment in applied_moments):
            x_parts.append(np.array([max(0.0, position - eps), min(beam_length, position + eps)]))

    x = np.unique(np.concatenate(x_parts))
    x.sort()

    # Shear force: reaction plus all vertical loads to the left of the cut.
    shear = np.full_like(x, reaction_a, dtype=float)
    for load in point_loads:
        shear += float(load["magnitude"]) * (x >= float(load["position"]))

    for load in distributed_loads:
        start = float(load["start"])
        end = float(load["end"])
        covered_length = np.clip(x - start, 0.0, end - start)
        shear += float(load["intensity"]) * covered_length

    if beam_type == "Simply supported":
        # The right support reaction closes the shear diagram at x = L.
        shear += reaction_b * (x >= beam_length)

    # Bending moment. A concentrated applied couple creates a moment jump.
    moment_diagram = np.zeros_like(x, dtype=float)
    if beam_type == "Simply supported":
        moment_diagram += reaction_a * x
        for load in point_loads:
            distance = np.maximum(x - float(load["position"]), 0.0)
            moment_diagram += float(load["magnitude"]) * distance
        for load in distributed_loads:
            start = float(load["start"])
            end = float(load["end"])
            intensity = float(load["intensity"])
            # Downward UDLs are negative, but produce positive sagging BM
            # on a simply supported beam.
            moment_diagram -= 0.5 * intensity * (
                np.maximum(x - start, 0.0) ** 2
                - np.maximum(x - end, 0.0) ** 2
            )
        for applied in applied_moments:
            moment_diagram -= float(applied["magnitude"]) * (
                x >= float(applied["position"])
            )
    else:
        # For a cantilever, use the loads to the right of each section.
        for load in point_loads:
            distance = np.maximum(float(load["position"]) - x, 0.0)
            moment_diagram += float(load["magnitude"]) * distance
        for load in distributed_loads:
            start = float(load["start"])
            end = float(load["end"])
            intensity = float(load["intensity"])
            distance_to_end = np.maximum(end - x, 0.0)
            distance_to_start = np.maximum(start - x, 0.0)
            # Cantilever internal moment is negative (hogging) for a
            # downward UDL, matching the point-load sign convention.
            moment_diagram += 0.5 * intensity * (
                distance_to_end**2 - distance_to_start**2
            )
        for applied in applied_moments:
            moment_diagram -= float(applied["magnitude"]) * (
                x <= float(applied["position"])
            )

    # Deflection is optional: static equilibrium, SFD and BMD do not
    # depend on Young's modulus E or second moment of area I.
    deflection = None
    if youngs_modulus_gpa is not None and second_moment_m4 is not None:
        # Euler-Bernoulli beam equation: y'' = -M / (E I).
        # M is in kN.m, so convert to N.m and apply support boundary conditions.
        e_pa = float(youngs_modulus_gpa) * 1e9
        curvature = -(moment_diagram * 1000.0) / (e_pa * float(second_moment_m4))
        slope_raw = _cumulative_trapezoid(curvature, x)
        deflection_raw = _cumulative_trapezoid(slope_raw, x)

        if beam_type == "Simply supported":
            deflection = deflection_raw - (x / beam_length) * deflection_raw[-1]
        else:
            # Fixed end at A: y(0) = 0 and slope(0) = 0.
            deflection = deflection_raw

        max_deflection_index = int(np.argmax(np.abs(deflection)))
        max_deflection_m = float(abs(deflection[max_deflection_index]))
        max_deflection_position_m = float(x[max_deflection_index])
    else:
        max_deflection_m = None
        max_deflection_position_m = None

    max_shear_index = int(np.argmax(np.abs(shear)))
    max_moment_index = int(np.argmax(np.abs(moment_diagram)))

    # Equilibrium residuals provide a quick numerical verification.
    if beam_type == "Simply supported":
        force_residual = reaction_a + reaction_b + total_force
        moment_residual = reaction_b * beam_length + total_moment_a
    else:
        force_residual = reaction_a + total_force
        moment_residual = fixed_moment_a + total_moment_a

    return {
        "x": x,
        "shear": shear,
        "moment": moment_diagram,
        "deflection": deflection,
        "reaction_a_kN": float(reaction_a),
        "reaction_b_kN": float(reaction_b),
        "fixed_moment_a_kNm": float(fixed_moment_a),
        "total_force_kN": float(total_force),
        "total_moment_a_kNm": float(total_moment_a),
        "max_shear_kN": float(abs(shear[max_shear_index])),
        "max_shear_position_m": float(x[max_shear_index]),
        "max_moment_kNm": float(abs(moment_diagram[max_moment_index])),
        "max_moment_position_m": float(x[max_moment_index]),
        "max_deflection_m": max_deflection_m,
        "max_deflection_position_m": max_deflection_position_m,
        "force_equilibrium_error_kN": float(force_residual),
        "moment_equilibrium_error_kNm": float(moment_residual),
    }
