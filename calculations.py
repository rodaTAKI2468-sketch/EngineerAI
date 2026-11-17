"""Compatibility helpers for the original EngineerAI command-line modules.

New application code should use beam_engine.analyze_beam directly.
"""
import numpy as np

from beam_engine import analyze_beam


def calculate_deflection(
    x,
    beam_length,
    load=None,
    position=None,
    E=None,
    I=None,
    beam_type="S",
    *,
    loads=None,
    positions=None,
    distributed_loads=None,
    applied_moments=None,
):
    """Calculate elastic deflection for one or more load cases.

    Backwards-compatible arguments:
      load: signed point load in kN (or a list of signed point loads)
      position: point-load position in m (or a list of positions)
      E: Young's modulus in Pa, preserving the original helper's convention
      I: second moment of area in m^4

    The optional beam_type accepts "S"/"Simply supported" or
    "C"/"Cantilever". Optional loads, positions, distributed_loads and
    applied_moments allow richer loading cases. The returned values are
    interpolated onto the x coordinates supplied by the caller.
    """
    x_values = np.asarray(x, dtype=float)
    if E is None or I is None:
        raise ValueError("Young's modulus E and second moment of area I are required.")
    if float(E) <= 0 or float(I) <= 0:
        raise ValueError("E and I must be greater than zero.")

    if loads is None:
        if load is None:
            point_load_values = []
        elif np.isscalar(load):
            point_load_values = [float(load)]
        else:
            point_load_values = [float(value) for value in load]
    else:
        point_load_values = [float(value) for value in loads]

    if positions is None:
        if position is None:
            point_positions = []
        elif np.isscalar(position):
            point_positions = [float(position)]
        else:
            point_positions = [float(value) for value in position]
    else:
        point_positions = [float(value) for value in positions]

    if len(point_load_values) != len(point_positions):
        raise ValueError("Each point load must have a corresponding position.")

    kind = {
        "S": "Simply supported",
        "C": "Cantilever",
        "Simply supported": "Simply supported",
        "Cantilever": "Cantilever",
    }.get(beam_type)
    if kind is None:
        raise ValueError("beam_type must be S, C, Simply supported or Cantilever.")

    point_load_data = [
        {"magnitude": value, "position": location}
        for value, location in zip(point_load_values, point_positions)
    ]
    result = analyze_beam(
        beam_type=kind,
        beam_length=float(beam_length),
        youngs_modulus_gpa=float(E) / 1e9,
        second_moment_m4=float(I),
        point_loads=point_load_data,
        distributed_loads=distributed_loads or [],
        applied_moments=applied_moments or [],
        samples=max(1401, int(x_values.size) * 2),
    )
    return np.interp(x_values, result["x"], result["deflection"])


def calculate_reactions(
    beam_type,
    beam_length,
    loads,
    positions,
    moments=None
):
    """Legacy point-load reaction helper; couples are summed as signed moments."""
    if moments is None:
        moments = []

    total_force = sum(loads)
    moment_about_A = sum(
        load * position
        for load, position in zip(loads, positions)
    ) + sum(moments)

    if beam_type in ("S", "Simply supported"):
        reaction_b = -moment_about_A / beam_length
        reaction_a = -(total_force + reaction_b)
        return reaction_a, reaction_b

    reaction_a = -total_force
    fixed_moment = -moment_about_A
    return reaction_a, fixed_moment


def calculate_shear_force(
    x,
    beam_type,
    reaction_A,
    reaction_B,
    loads,
    positions,
    beam_length
):
    """Legacy point-load shear helper."""
    V = np.full_like(x, reaction_A, dtype=float)

    for load_value, location in zip(loads, positions):
        V[x >= location] += load_value

    if beam_type in ("S", "Simply supported"):
        V[x >= beam_length] += reaction_B

    return V


def calculate_bending_moment(
    x,
    beam_type,
    reaction_A,
    loads,
    positions,
    fixed_moment=0
):
    """Legacy point-load bending-moment helper.

    For complete loading cases, including UDLs and applied couples, use
    beam_engine.analyze_beam instead.
    """
    M = np.zeros_like(x, dtype=float)

    for i, xi in enumerate(x):
        if beam_type in ("S", "Simply supported"):
            value = reaction_A * xi
            for load_value, location in zip(loads, positions):
                if xi >= location:
                    value += load_value * (xi - location)
        else:
            value = 0.0
            for load_value, location in zip(loads, positions):
                if xi <= location:
                    value += -load_value * (location - xi)
        M[i] = value

    return M
