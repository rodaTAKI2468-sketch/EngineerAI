"""Cross-section properties and elastic beam stress calculations.

Units: dimensions in m, area in m^2, second moment in m^4,
forces in kN, moments in kN.m, stresses returned in MPa.
"""
from __future__ import annotations

import numpy as np


def rectangular_section(breadth_m: float, depth_m: float) -> dict:
    """Return area and bending properties for a rectangle.

    Breadth is the section dimension across the beam; depth is measured in
    the direction of bending and is cubed in I = b*h^3/12.
    """
    b, h = float(breadth_m), float(depth_m)
    if not np.isfinite(b) or not np.isfinite(h) or b <= 0 or h <= 0:
        raise ValueError("Rectangular breadth and depth must both be greater than zero.")
    area = b * h
    inertia = b * h**3 / 12.0
    c = h / 2.0
    return {
        "shape": "Rectangle", "area_m2": area, "inertia_m4": inertia,
        "c_m": c, "section_modulus_m3": inertia / c,
        "breadth_m": b, "depth_m": h, "shear_factor": 1.5,
    }


def custom_section(area_m2: float, inertia_m4: float, c_m: float) -> dict:
    """Return user-supplied area, I and extreme-fibre distance properties."""
    area, inertia, c = float(area_m2), float(inertia_m4), float(c_m)
    if not all(np.isfinite(v) and v > 0 for v in (area, inertia, c)):
        raise ValueError("Area A, second moment I and extreme-fibre distance c must be positive.")
    return {
        "shape": "User-defined", "area_m2": area, "inertia_m4": inertia,
        "c_m": c, "section_modulus_m3": inertia / c,
        "shear_factor": None,
    }


def calculate_beam_stresses(result: dict, section: dict) -> dict:
    """Calculate maximum elastic bending stress and transverse shear stress."""
    x = np.asarray(result["x"], dtype=float)
    moment = np.asarray(result["moment"], dtype=float)
    shear = np.asarray(result["shear"], dtype=float)
    if x.size == 0 or moment.size != x.size or shear.size != x.size:
        raise ValueError("Beam result arrays are empty or have inconsistent lengths.")
    if not all(np.all(np.isfinite(v)) for v in (x, moment, shear)):
        raise ValueError("Beam result contains non-finite shear or moment values.")

    mi = int(np.argmax(np.abs(moment)))
    vi = int(np.argmax(np.abs(shear)))
    m_max = float(abs(moment[mi]))
    v_max = float(abs(shear[vi]))
    sigma_mpa = (m_max * section["c_m"] / section["inertia_m4"]) * 1000.0
    average_tau_mpa = (v_max / section["area_m2"]) * 1000.0
    factor = section.get("shear_factor")
    tau_max_mpa = average_tau_mpa * factor if factor else average_tau_mpa
    return {
        "max_bending_stress_mpa": sigma_mpa,
        "max_shear_stress_mpa": tau_max_mpa,
        "average_shear_stress_mpa": average_tau_mpa,
        "max_moment_kNm": m_max,
        "max_moment_position_m": float(x[mi]),
        "max_shear_kN": v_max,
        "max_shear_position_m": float(x[vi]),
        "shear_method": "Maximum rectangular shear (1.5V/A)" if factor else "Average shear (V/A); shape-specific maximum needs Q and web thickness",
    }


def build_stress_steps(section: dict, stresses: dict) -> list[str]:
    """Build exam-style cross-section and stress calculation steps."""
    steps = [
        f"Cross-section: {section['shape']}.",
        f"Area: A = {section['area_m2']:.6g} m^2.",
        f"Second moment of area about the bending neutral axis: I = {section['inertia_m4']:.6g} m^4.",
        f"Extreme-fibre distance: c = {section['c_m']:.6g} m.",
        f"Section modulus: Z = I/c = {section['section_modulus_m3']:.6g} m^3.",
        f"Maximum bending moment: |M_max| = {stresses['max_moment_kNm']:.6g} kN.m at x = {stresses['max_moment_position_m']:.6g} m.",
        f"Maximum bending stress: sigma_max = M_max*c/I = {stresses['max_bending_stress_mpa']:.6g} MPa.",
        f"Maximum shear force: |V_max| = {stresses['max_shear_kN']:.6g} kN at x = {stresses['max_shear_position_m']:.6g} m.",
        f"Shear stress method: {stresses['shear_method']}.",
        f"Shear stress result: tau = {stresses['max_shear_stress_mpa']:.6g} MPa.",
    ]
    if section["shape"] == "Rectangle":
        steps.insert(1, f"Rectangle dimensions: breadth b = {section['breadth_m']:.6g} m; depth h = {section['depth_m']:.6g} m.")
        steps.insert(2, "For a rectangle: A = bh and I = bh^3/12. Use h (the depth in the bending direction) as the cubed dimension.")
    else:
        steps.insert(1, "Use the supplied A, I and c from the cross-section data. Area alone is not enough to calculate bending stress.")
    return steps
