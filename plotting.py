import matplotlib.pyplot as plt
import numpy as np


def plot_results(
    beam_length,
    loads,
    positions,
    reaction_A,
    reaction_B,
    x,
    V,
    M
):

    fig, axes = plt.subplots(3, 1, figsize=(12, 12))

    # Beam diagram
    axes[0].plot([0, beam_length], [0, 0], linewidth=6)

    axes[0].plot(0, 0, marker="^", markersize=15)
    axes[0].plot(beam_length, 0, marker="o", markersize=12)

    axes[0].text(0, -1.3, f"RA = {reaction_A:.2f} kN", ha="center")
    axes[0].text(beam_length, -1.3, f"RB = {reaction_B:.2f} kN", ha="center")

    for load, position in zip(loads, positions):

        if load < 0:

            axes[0].arrow(
                position, 1,
                0, -0.8,
                head_width=0.15,
                head_length=0.15,
                length_includes_head=True
            )

            axes[0].text(
                position,
                1.2,
                f"{abs(load):.1f} kN ↓",
                ha="center"
            )

        else:

            axes[0].arrow(
                position, -1,
                0, 0.8,
                head_width=0.15,
                head_length=0.15,
                length_includes_head=True
            )

            axes[0].text(
                position,
                -1.6,
                f"{load:.1f} kN ↑",
                ha="center"
            )

    axes[0].set_xlim(-0.5, beam_length + 0.5)
    axes[0].set_ylim(-2.5, 2.5)
    axes[0].set_title("Beam Diagram")
    axes[0].axis("off")

    # SFD
    axes[1].step(x, V, where="post")
    axes[1].axhline(0, color="black")

    axes[1].grid(True)
    axes[1].set_xlim(0, beam_length)

    axes[1].set_title("Shear Force Diagram")
    axes[1].set_ylabel("Shear Force (kN)")

    # BMD
    axes[2].plot(x, M)
    axes[2].fill_between(x, M, alpha=0.3)

    axes[2].axhline(0, color="black")

    axes[2].grid(True)
    axes[2].set_xlim(0, beam_length)

    axes[2].set_title(
        f"Bending Moment Diagram "
        f"(Max |M| = {np.max(np.abs(M)):.2f} kN·m)"
    )

    axes[2].set_xlabel("Distance along beam (m)")
    axes[2].set_ylabel("Moment (kN·m)")

    plt.tight_layout()
    plt.show()