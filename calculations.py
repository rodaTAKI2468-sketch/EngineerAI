import numpy as np


def calculate_reactions(
    beam_length,
    loads,
    positions,
    moments=None
):

    total_force = sum(loads)

    moment_about_A = sum(
        load * position
        for load, position in zip(loads, positions)
    )

    moment_sum = moment_about_A

    if moments:
        moment_sum += sum(moments)

    reaction_B = -moment_sum / beam_length
    reaction_A = -(total_force + reaction_B)

    return reaction_A, reaction_B


def calculate_shear_force(
    x,
    reaction_A,
    reaction_B,
    loads,
    positions,
    beam_length
):

    V = np.full_like(x, reaction_A)

    for load, position in zip(loads, positions):
        V[x >= position] += load

    V[x >= beam_length] += reaction_B

    return V


def calculate_bending_moment(
    x,
    reaction_A,
    loads,
    positions
):

    M = np.zeros_like(x)

    for i, xi in enumerate(x):

        moment = reaction_A * xi

        for load, position in zip(loads, positions):

            if xi >= position:
                moment += load * (xi - position)

        M[i] = moment

    return M