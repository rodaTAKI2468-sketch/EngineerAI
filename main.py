import numpy as np

from calculations import (
    calculate_reactions,
    calculate_shear_force,
    calculate_bending_moment,
    calculate_deflection
)

from validation import (
    validate_beam_length,
    validate_position,
    validate_direction
)

from plotting import plot_results


print("=== EngineerAI ===\n")

beam_type = input(
    "Beam type (S for Simply Supported, C for Cantilever): "
).upper()

while beam_type not in ["S", "C"]:
    beam_type = input(
        "Please enter S or C: "
    ).upper()

print()

beam_length = float(input("Enter beam length (m): "))
E = float(input("Enter Young's modulus E (GPa): "))
I = float(input("Enter second moment of area I (m^4): "))

E *= 1e9



while not validate_beam_length(beam_length):
    beam_length = float(
        input("Beam length must be greater than 0: ")
    )

num_loads = int(input("Enter number of loads: "))

loads = []
positions = []

moments = []
moment_positions = []

for i in range(num_loads):

    print(f"\n--- Load {i + 1} ---")

    load_type = input(
        "Load type (P, UDL, or M for applied moment): "
    ).upper()

    while load_type not in ["P", "UDL", "M"]:
        load_type = input(
            "Please enter P, UDL, or M: "
        ).upper()

    if load_type == "P":

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

    elif load_type == "UDL":

        intensity = float(
            input("UDL intensity (kN/m): ")
        )

        start = float(
            input("Start position (m): ")
        )

        end = float(
            input("End position (m): ")
        )

        while start < 0 or end > beam_length or start >= end:

            print("Invalid UDL positions.")

            start = float(input("Start position (m): "))
            end = float(input("End position (m): "))

        direction = input(
            "Direction (U for up, D for down): "
        ).upper()

        while not validate_direction(direction):
            direction = input(
                "Please enter U or D: "
            ).upper()

        equivalent_load = intensity * (end - start)
        equivalent_position = start + (end - start) / 2

        if direction == "D":
            equivalent_load = -equivalent_load

        loads.append(equivalent_load)
        positions.append(equivalent_position)

    elif load_type == "M":

        moment = float(
            input("Moment magnitude (kN·m): ")
        )

        position = float(
            input("Moment position from A (m): ")
        )

        while not validate_position(position, beam_length):
            position = float(
                input("Invalid position. Enter again: ")
            )

        direction = input(
            "Direction (CW for clockwise, CCW for counterclockwise): "
        ).upper()

        while direction not in ["CW", "CCW"]:
            direction = input(
                "Please enter CW or CCW: "
            ).upper()

        if direction == "CW":
            moment = -moment

        moments.append(moment)
        moment_positions.append(position)


results = calculate_reactions(
    beam_type,
    beam_length,
    loads,
    positions,
    moments
)

x = np.linspace(0, beam_length, 10000)

if beam_type == "S":

    reaction_A, reaction_B = results
    fixed_moment = 0

    print("\n=== Final Results ===")
    print(f"Reaction at A = {reaction_A:.2f} kN")
    print(f"Reaction at B = {reaction_B:.2f} kN")

else:

    reaction_A, fixed_moment = results
    reaction_B = 0

    print("\n=== Final Results ===")
    print(f"Reaction force at support = {reaction_A:.2f} kN")
    print(f"Fixed-end moment = {fixed_moment:.2f} kN·m")


V = calculate_shear_force(
    x,
    beam_type,
    reaction_A,
    reaction_B,
    loads,
    positions,
    beam_length
)

M = calculate_bending_moment(
    x,
    beam_type,
    reaction_A,
    loads,
    positions,
    fixed_moment
)

y = calculate_deflection(
    x,
    beam_length,
    loads[0],
    positions[0],
    E,
    I
)

max_shear = np.max(np.abs(V))
max_shear_pos = x[np.argmax(np.abs(V))]

max_moment = np.max(np.abs(M))
max_moment_pos = x[np.argmax(np.abs(M))]

max_deflection = np.max(np.abs(y))
max_deflection_pos = x[np.argmax(np.abs(y))]

print("\n=== Maximum Values ===")

print(
    f"Maximum shear = {max_shear:.2f} kN "
    f"at x = {max_shear_pos:.2f} m"
)

print(
    f"Maximum moment = {max_moment:.2f} kN·m "
    f"at x = {max_moment_pos:.2f} m"
)

print(
    f"Maximum deflection = {max_deflection * 1000:.3f} mm "
    f"at x = {max_deflection_pos:.2f} m"
) 

plot_results(
    beam_length,
    loads,
    positions,
    reaction_A,
    reaction_B,
    x,
    V,
    M,
    y
)
