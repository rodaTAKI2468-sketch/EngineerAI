import numpy as np


def calculate_reactions(
    beam_type,
    beam_length,
    loads,
    positions,
    moments=None
):

    if moments is None:
        moments = []

    total_force = sum(loads)

    moment_about_A = sum(
        load * position
        for load, position in zip(loads, positions)
    )

    applied_moments = sum(moments)

    if beam_type == "S":

        reaction_B = -(moment_about_A + applied_moments) / beam_length

        reaction_A = -(total_force + reaction_B)

        return reaction_A, reaction_B

    elif beam_type == "C":

        reaction_A = -total_force

        fixed_moment = -(moment_about_A + applied_moments)

        return reaction_A, fixed_moment


def calculate_shear_force(
    x,
    beam_type,
    reaction_A,
    reaction_B,
    loads,
    positions,
    beam_length
):

    V = np.full_like(x, reaction_A)

    for load, position in zip(loads, positions):
        V[x >= position] += load

    if beam_type == "S":
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

    M = np.zeros_like(x)

    for i, xi in enumerate(x):

        moment = fixed_moment + reaction_A * xi

        for load, position in zip(loads, positions):

            if xi >= position:
                moment += load * (xi - position)

        M[i] = moment

    return M