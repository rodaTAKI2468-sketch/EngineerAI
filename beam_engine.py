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
            # Replace the portion of this UDL to the left of each section
            # with its resultant acting at that portion's centroid.
            covered_length = np.clip(x - start, 0.0, end - start)
            centroid_arm = x - start - 0.5 * covered_length
            moment_diagram += intensity * covered_length * centroid_arm
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


def _format_equation_number(value: float) -> str:
    """Compact, readable number for worked equations."""
    if abs(value) < 1e-10:
        value = 0.0
    return f"{value:.4g}"


def _signed_terms(values: list[float], unit: str = "") -> str:
    """Format signed scalar terms with explicit plus/minus signs."""
    if not values:
        return f"0 {unit}".strip()
    parts = []
    for value in values:
        sign = "+" if value >= 0 else "−"
        parts.append(f"{sign} {abs(value):.4g}")
    joined = " ".join(parts)
    return f"{joined} {unit}".strip()


def _polynomial_expression(
    quadratic: float,
    linear: float,
    constant: float,
    variable: str = "x",
) -> str:
    """Format a quadratic/linear/constant expression for diagram sections."""
    terms: list[str] = []
    values = [
        (quadratic, f"{variable}²"),
        (linear, variable),
        (constant, ""),
    ]
    for coefficient, symbol in values:
        if abs(coefficient) < 1e-10:
            continue
        sign = "+" if coefficient > 0 else "−"
        magnitude = _format_equation_number(abs(coefficient))
        if symbol:
            term = f"{magnitude} {symbol}"
        else:
            term = magnitude
        if not terms:
            terms.append(term if coefficient > 0 else f"− {term}")
        else:
            terms.append(f"{sign} {term}")
    return " ".join(terms) if terms else "0"


def build_worked_solution(
    beam_type: str,
    beam_length: float,
    point_loads: list[dict[str, float]] | None,
    distributed_loads: list[dict[str, float]] | None,
    applied_moments: list[dict[str, float]] | None,
    results: dict[str, Any],
) -> dict[str, Any]:
    """Create transparent equilibrium and section-equation steps for the UI.

    The section equations use the same sign convention and expressions as
    analyze_beam. SFD and BMD expressions are supplied for each interval
    between a load/support event, so their polynomial form is valid there.
    """
    point_loads = point_loads or []
    distributed_loads = distributed_loads or []
    applied_moments = applied_moments or []

    udl_resultants: list[dict[str, float]] = []
    load_force_terms = [float(load["magnitude"]) for load in point_loads]
    load_moment_terms = [
        float(load["magnitude"]) * float(load["position"])
        for load in point_loads
    ]

    for load in distributed_loads:
        intensity = float(load["intensity"])
        start = float(load["start"])
        end = float(load["end"])
        resultant = intensity * (end - start)
        centroid = 0.5 * (start + end)
        udl_resultants.append(
            {
                "intensity": intensity,
                "start": start,
                "end": end,
                "resultant": resultant,
                "centroid": centroid,
            }
        )
        load_force_terms.append(resultant)
        load_moment_terms.append(resultant * centroid)

    for couple in applied_moments:
        load_moment_terms.append(float(couple["magnitude"]))

    total_force = float(results["total_force_kN"])
    total_load_moment = float(results["total_moment_a_kNm"])
    reaction_a = float(results["reaction_a_kN"])
    reaction_b = float(results["reaction_b_kN"])
    fixed_moment_a = float(results["fixed_moment_a_kNm"])

    if beam_type == "Simply supported":
        force_equation = (
            "ΣFy = 0:  R_A + R_B "
            + _signed_terms(load_force_terms, "kN")
            + " = 0"
        )
        moment_terms: list[str] = []
        for load in point_loads:
            p = float(load["magnitude"])
            position = float(load["position"])
            sign = "+" if p >= 0 else "−"
            moment_terms.append(
                f"{sign} {abs(p):.4g}({position:.4g})"
            )
        for udl in udl_resultants:
            w_total = udl["resultant"]
            centroid = udl["centroid"]
            sign = "+" if w_total >= 0 else "−"
            moment_terms.append(
                f"{sign} {abs(w_total):.4g}({centroid:.4g})"
            )
        for couple in applied_moments:
            value = float(couple["magnitude"])
            sign = "+" if value >= 0 else "−"
            moment_terms.append(f"{sign} {abs(value):.4g}")
        moment_equation = (
            f"ΣM_A = 0:  R_B({beam_length:.4g}) "
            + (" ".join(moment_terms) if moment_terms else "")
            + " = 0"
        )
        reaction_steps = [
            force_equation,
            moment_equation,
            (
                f"R_B = −({_format_equation_number(total_load_moment)})"
                f" / {_format_equation_number(beam_length)}"
                f" = {_format_equation_number(reaction_b)} kN"
            ),
            (
                f"R_A = −({_format_equation_number(total_force)})"
                f" − ({_format_equation_number(reaction_b)})"
                f" = {_format_equation_number(reaction_a)} kN"
            ),
        ]
        support_note = (
            "At the pin at A, the vertical reaction is R_A. "
            "At the roller at B, the vertical reaction is R_B. "
            "There is no support moment at either ideal simple support."
        )
    else:
        force_equation = (
            "ΣFy = 0:  R_A "
            + _signed_terms(load_force_terms, "kN")
            + " = 0"
        )
        moment_terms = []
        for load in point_loads:
            p = float(load["magnitude"])
            position = float(load["position"])
            sign = "+" if p >= 0 else "−"
            moment_terms.append(
                f"{sign} {abs(p):.4g}({position:.4g})"
            )
        for udl in udl_resultants:
            w_total = udl["resultant"]
            centroid = udl["centroid"]
            sign = "+" if w_total >= 0 else "−"
            moment_terms.append(
                f"{sign} {abs(w_total):.4g}({centroid:.4g})"
            )
        for couple in applied_moments:
            value = float(couple["magnitude"])
            sign = "+" if value >= 0 else "−"
            moment_terms.append(f"{sign} {abs(value):.4g}")
        moment_equation = (
            "ΣM_A = 0:  M_A "
            + (" ".join(moment_terms) if moment_terms else "")
            + " = 0"
        )
        reaction_steps = [
            force_equation,
            moment_equation,
            (
                f"R_A = −({_format_equation_number(total_force)})"
                f" = {_format_equation_number(reaction_a)} kN"
            ),
            (
                f"M_A = −({_format_equation_number(total_load_moment)})"
                f" = {_format_equation_number(fixed_moment_a)} kN·m"
            ),
        ]
        support_note = (
            "At the fixed support A, the beam develops a vertical reaction R_A "
            "and a fixing moment M_A. The free end has no support reaction."
        )

    # Event positions split the beam into intervals with a fixed active-load set.
    events = [0.0, float(beam_length)]
    events.extend(float(load["position"]) for load in point_loads)
    for load in distributed_loads:
        events.extend([float(load["start"]), float(load["end"])])
    events.extend(float(moment["position"]) for moment in applied_moments)
    events = sorted(events)
    unique_events: list[float] = []
    for event in events:
        if not unique_events or abs(event - unique_events[-1]) > 1e-9:
            unique_events.append(event)

    intervals: list[dict[str, Any]] = []
    for left, right in zip(unique_events[:-1], unique_events[1:]):
        if right - left <= 1e-10:
            continue
        middle = 0.5 * (left + right)

        # Shear is linear on each interval: V(x) = v1*x + v0.
        v1 = 0.0
        v0 = reaction_a
        active_point_labels = []
        for index, load in enumerate(point_loads, start=1):
            position = float(load["position"])
            magnitude = float(load["magnitude"])
            if middle > position:
                v0 += magnitude
                active_point_labels.append(f"P{index}")
        for load in distributed_loads:
            intensity = float(load["intensity"])
            start = float(load["start"])
            end = float(load["end"])
            if middle >= end:
                v0 += intensity * (end - start)
            elif middle > start:
                v1 += intensity
                v0 -= intensity * start

        # Bending moment is quadratic at most on each interval.
        m2 = 0.0
        m1 = 0.0
        m0 = 0.0
        if beam_type == "Simply supported":
            m1 += reaction_a
            for load in point_loads:
                position = float(load["position"])
                magnitude = float(load["magnitude"])
                if middle > position:
                    m1 += magnitude
                    m0 -= magnitude * position
            for load in distributed_loads:
                intensity = float(load["intensity"])
                start = float(load["start"])
                end = float(load["end"])
                if middle >= end:
                    resultant = intensity * (end - start)
                    centroid = 0.5 * (start + end)
                    m1 += resultant
                    m0 -= resultant * centroid
                elif middle > start:
                    m2 += 0.5 * intensity
                    m1 -= intensity * start
                    m0 += 0.5 * intensity * start**2
            for couple in applied_moments:
                if middle > float(couple["position"]):
                    m0 -= float(couple["magnitude"])
        else:
            for load in point_loads:
                position = float(load["position"])
                magnitude = float(load["magnitude"])
                if middle < position:
                    m1 -= magnitude
                    m0 += magnitude * position
            for load in distributed_loads:
                intensity = float(load["intensity"])
                start = float(load["start"])
                end = float(load["end"])
                if middle < start:
                    resultant = intensity * (end - start)
                    centroid = 0.5 * (start + end)
                    m1 -= resultant
                    m0 += resultant * centroid
                elif middle < end:
                    m2 += 0.5 * intensity
                    m1 -= intensity * end
                    m0 += 0.5 * intensity * end**2
            for couple in applied_moments:
                if middle < float(couple["position"]):
                    m0 -= float(couple["magnitude"])

        intervals.append(
            {
                "start": left,
                "end": right,
                "shear_equation": (
                    f"V(x) = {_polynomial_expression(0.0, v1, v0)} kN"
                ),
                "moment_equation": (
                    f"M(x) = {_polynomial_expression(m2, m1, m0)} kN·m"
                ),
                "shear_slope": v1,
                "shear_constant": v0,
                "moment_quadratic": m2,
                "moment_linear": m1,
                "moment_constant": m0,
            }
        )

    point_load_steps = [
        {
            "label": f"Point load P{index}",
            "equation": (
                f"P_{index} = {_format_equation_number(float(load['magnitude']))} kN "
                f"at x = {_format_equation_number(float(load['position']))} m "
                f"({'upward' if float(load['magnitude']) >= 0 else 'downward'})"
            ),
        }
        for index, load in enumerate(point_loads, start=1)
    ]

    udl_steps = []
    for index, udl in enumerate(udl_resultants, start=1):
        udl_steps.append(
            {
                "label": f"UDL {index}",
                "equivalent_force": (
                    f"W_{index} = w(b − a) = "
                    f"({_format_equation_number(udl['intensity'])})"
                    f"({_format_equation_number(udl['end'])} − "
                    f"{_format_equation_number(udl['start'])})"
                    f" = {_format_equation_number(udl['resultant'])} kN"
                ),
                "centroid": (
                    f"x̄_{index} = (a + b)/2 = "
                    f"({_format_equation_number(udl['start'])} + "
                    f"{_format_equation_number(udl['end'])})/2"
                    f" = {_format_equation_number(udl['centroid'])} m from A"
                ),
            }
        )

    couple_steps = [
        {
            "label": f"Applied couple {index}",
            "equation": (
                f"M_{index} = {_format_equation_number(float(couple['magnitude']))} kN·m "
                f"({'CCW, positive' if float(couple['magnitude']) >= 0 else 'CW, negative'})"
            ),
        }
        for index, couple in enumerate(applied_moments, start=1)
    ]

    if beam_type == "Simply supported":
        boundary_note = (
            f"At B (x = {beam_length:g} m), the shear diagram has a jump of "
            f"R_B = {_format_equation_number(reaction_b)} kN and returns to zero. "
            "The bending moment is zero at both ideal simple supports unless an "
            "applied end couple is specified."
        )
    else:
        boundary_note = (
            "At the free end, the internal shear and bending moment return to zero "
            "when no end force or end couple is applied. The fixed-end actions occur at A."
        )

    applied_moment_note = (
        "At an applied couple, the BMD has a vertical jump equal to −M "
        "(with CCW positive); the SFD does not jump because a pure couple adds no vertical force."
        if applied_moments
        else "There are no applied concentrated couples, so the BMD is continuous at load points."
    )

    return {
        "support_note": support_note,
        "reaction_steps": reaction_steps,
        "point_load_steps": point_load_steps,
        "udl_steps": udl_steps,
        "couple_steps": couple_steps,
        "intervals": intervals,
        "boundary_note": boundary_note,
        "applied_moment_note": applied_moment_note,
        "total_force_kN": total_force,
        "total_load_moment_kNm": total_load_moment,
    }
