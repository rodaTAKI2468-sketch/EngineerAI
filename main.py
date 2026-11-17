"""EngineerAI command-line beam analysis.

For the interactive Streamlit interface, run: streamlit run app.py
"""
import matplotlib.pyplot as plt

from beam_engine import analyze_beam


def ask_number(prompt, minimum=None, maximum=None):
    while True:
        try:
            value = float(input(prompt))
        except ValueError:
            print("Please enter a valid number.")
            continue

        if minimum is not None and value < minimum:
            print(f"Value must be at least {minimum}.")
            continue
        if maximum is not None and value > maximum:
            print(f"Value must not exceed {maximum}.")
            continue
        return value


def ask_count(prompt, maximum=20):
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print("Please enter a whole number.")
            continue
        if 0 <= value <= maximum:
            return value
        print(f"Enter a number between 0 and {maximum}.")


def ask_direction(prompt, choices):
    choices_upper = [choice.upper() for choice in choices]
    while True:
        value = input(prompt).strip().upper()
        if value in choices_upper:
            return value
        print("Choose one of: " + ", ".join(choices_upper))


def main():
    print("\n=== EngineerAI | Beam Analysis ===\n")
    support = ask_direction(
        "Beam type (S = simply supported, C = cantilever): ",
        ["S", "C"],
    )
    beam_type = "Simply supported" if support == "S" else "Cantilever"

    beam_length = ask_number("Beam length, L (m): ", minimum=0.1)

    while True:
        deflection_choice = input(
            "Calculate elastic deflection? (Y/N, default N): "
        ).strip().upper()
        if deflection_choice in {"", "Y", "N"}:
            break
        print("Please enter Y or N.")

    include_deflection = deflection_choice == "Y"

    youngs_modulus = None
    second_moment = None
    if include_deflection:
        print("\nDeflection requires both E and I.")
        youngs_modulus = ask_number("Young's modulus, E (GPa): ", minimum=0.1)
        second_moment = ask_number("Second moment of area, I (m^4): ", minimum=1e-12)

    point_loads = []
    print("\n--- Point loads ---")
    for index in range(ask_count("Number of point loads: ", maximum=20)):
        print(f"Point load P{index + 1}")
        magnitude = ask_number("  Magnitude (kN): ", minimum=0.0)
        position = ask_number(
            f"  Position from A (0 to {beam_length:g} m): ",
            minimum=0.0,
            maximum=beam_length,
        )
        direction = ask_direction("  Direction (U = up, D = down): ", ["U", "D"])
        if direction == "D":
            magnitude = -magnitude
        point_loads.append({"magnitude": magnitude, "position": position})

    distributed_loads = []
    print("\n--- Uniformly distributed loads (UDLs) ---")
    for index in range(ask_count("Number of UDL segments: ", maximum=12)):
        print(f"UDL {index + 1}")
        intensity = ask_number("  Intensity (kN/m): ", minimum=0.0)
        start = ask_number(
            f"  Start position (0 to {beam_length:g} m): ",
            minimum=0.0,
            maximum=beam_length,
        )
        end = ask_number(
            f"  End position (greater than start and up to {beam_length:g} m): ",
            minimum=0.0,
            maximum=beam_length,
        )
        while end <= start:
            print("  End position must be greater than start position.")
            end = ask_number(
                f"  End position (greater than {start:g} m): ",
                minimum=0.0,
                maximum=beam_length,
            )
        direction = ask_direction("  Direction (U = up, D = down): ", ["U", "D"])
        if direction == "D":
            intensity = -intensity
        distributed_loads.append(
            {"intensity": intensity, "start": start, "end": end}
        )

    applied_moments = []
    print("\n--- Applied moments ---")
    for index in range(ask_count("Number of applied moments: ", maximum=12)):
        print(f"Applied moment M{index + 1}")
        magnitude = ask_number("  Magnitude (kN.m): ", minimum=0.0)
        position = ask_number(
            f"  Position from A (0 to {beam_length:g} m): ",
            minimum=0.0,
            maximum=beam_length,
        )
        direction = ask_direction(
            "  Rotation (CCW or CW): ",
            ["CCW", "CW"],
        )
        if direction == "CW":
            magnitude = -magnitude
        applied_moments.append({"magnitude": magnitude, "position": position})

    results = analyze_beam(
        beam_type=beam_type,
        beam_length=beam_length,
        youngs_modulus_gpa=youngs_modulus,
        second_moment_m4=second_moment,
        point_loads=point_loads,
        distributed_loads=distributed_loads,
        applied_moments=applied_moments,
    )

    print("\n=== Support reactions ===")
    print(f"Reaction at A: {results['reaction_a_kN']:.3f} kN")
    if beam_type == "Simply supported":
        print(f"Reaction at B: {results['reaction_b_kN']:.3f} kN")
    else:
        print(f"Fixed-end moment at A: {results['fixed_moment_a_kNm']:.3f} kN.m")

    print("\n=== Maximum values ===")
    print(
        f"Maximum absolute shear: {results['max_shear_kN']:.3f} kN "
        f"at x = {results['max_shear_position_m']:.3f} m"
    )
    print(
        f"Maximum absolute moment: {results['max_moment_kNm']:.3f} kN.m "
        f"at x = {results['max_moment_position_m']:.3f} m"
    )
    if results["deflection"] is not None:
        print(
            f"Maximum absolute deflection: {results['max_deflection_m'] * 1000:.4f} mm "
            f"at x = {results['max_deflection_position_m']:.3f} m"
        )
    else:
        print("Deflection skipped: E and I were not requested.")

    print("\n=== Equilibrium residuals (should be close to zero) ===")
    print(f"Sum of vertical forces: {results['force_equilibrium_error_kN']:.3e} kN")
    print(f"Moment about A: {results['moment_equilibrium_error_kNm']:.3e} kN.m")

    x = results["x"]
    has_deflection = results["deflection"] is not None
    figure, axes = plt.subplots(
        3 if has_deflection else 2,
        1,
        figsize=(10, 9 if has_deflection else 7),
        sharex=True,
    )
    axes = list(axes)

    axes[0].step(x, results["shear"], where="post")
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].fill_between(x, results["shear"], 0, step="post", alpha=0.2)
    axes[0].set_ylabel("Shear (kN)")
    axes[0].set_title("Shear Force Diagram")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(x, results["moment"])
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].fill_between(x, results["moment"], 0, alpha=0.2)
    axes[1].set_ylabel("Moment (kN.m)")
    axes[1].set_title("Bending Moment Diagram")
    axes[1].grid(True, alpha=0.3)

    if has_deflection:
        deflection_mm = results["deflection"] * 1000.0
        axes[2].plot(x, deflection_mm)
        axes[2].axhline(0, color="black", linewidth=0.8)
        axes[2].fill_between(x, deflection_mm, 0, alpha=0.2)
        axes[2].set_ylabel("Deflection (mm)")
        axes[2].set_title("Elastic Deflection (positive downward)")
        axes[2].grid(True, alpha=0.3)
        axes[2].invert_yaxis()

    axes[-1].set_xlabel("Distance from A (m)")
    figure.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
