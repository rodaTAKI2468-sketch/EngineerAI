import numpy as np

from calculations import (
    calculate_reactions,
    calculate_shear_force,
    calculate_bending_moment
)

from validation import (
    validate_beam_length,
    validate_position,
    validate_direction
)

from plotting import plot_results


print("=== EngineerAI v1 ===")
print("Simply Supported Beam Analysis\n")

beam_length = float(input("Enter beam length (m): "))

while not validate_beam_length(beam_length):
    beam_length = float(
        input("Beam length must be greater than 0: ")
    )

num_loads = int(input("Enter number of point loads: "))

loads = []
positions = []

for i in range(num_loads):

    print(f"\n--- Load {i + 1} ---")

    magnitude = float(input("Load magnitude (kN): "))

    position = float(input("Distance from A (m): "))

    while not validate_position(position, beam_length):
        position = float(
            input("Invalid position. Enter again: ")
        )

    direction = input(
        "Direction (U for up, D for down): "
    ).upper()

    while not validate_direction(direction):
        direction = input(
            "Please enter U or D: "
        ).upper()

    if direction == "D":
        magnitude = -magnitude

    loads.append(magnitude)
    positions.append(position)

reaction_A, reaction_B = calculate_reactions(
    beam_length,
    loads,
    positions
)

x = np.linspace(0, beam_length, 1000)

V = calculate_shear_force(
    x,
    reaction_A,
    reaction_B,
    loads,
    positions,
    beam_length
)

M = calculate_bending_moment(
    x,
    reaction_A,
    loads,
    positions
)

print("\n=== Final Results ===")

print(f"Reaction at A = {reaction_A:.2f} kN")
print(f"Reaction at B = {reaction_B:.2f} kN")

plot_results(
    beam_length,
    loads,
    positions,
    reaction_A,
    reaction_B,
    x,
    V,
    M
)