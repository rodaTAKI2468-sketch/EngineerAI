import io
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from calculations import (
    calculate_reactions,
    calculate_shear_force,
    calculate_bending_moment,
    calculate_deflection
)

st.set_page_config(page_title="EngineerAI", layout="wide")

st.title("🏗️ EngineerAI")
st.write("Beam Analysis Tool")

beam_type = st.selectbox(
    "Beam type",
    ["S", "C"],
    format_func=lambda x:
        "Simply Supported" if x == "S" else "Cantilever"
)

beam_length = st.number_input(
    "Beam length (m)",
    min_value=0.1,
    value=5.0
)

E = st.number_input(
    "Young's modulus E (GPa)",
    min_value=1.0,
    value=200.0
)

I = st.number_input(
    "Second moment of area I (m⁴)",
    min_value=0.000001,
    value=0.0001,
    format="%.6f"
)

load = st.number_input(
    "Point load magnitude (kN)",
    value=20.0
)

position = st.number_input(
    "Load position from A (m)",
    min_value=0.0,
    max_value=beam_length,
    value=beam_length / 2
)

direction = st.selectbox(
    "Load direction",
    ["Down", "Up"]
)

if st.button("Analyze"):

    if direction == "Down":
        load = -load

    loads = [load]
    positions = [position]
    moments = []

    results = calculate_reactions(
        beam_type,
        beam_length,
        loads,
        positions,
        moments
    )

    if beam_type == "S":
        reaction_A, reaction_B = results
        fixed_moment = 0
    else:
        reaction_A, fixed_moment = results
        reaction_B = 0

    x = np.linspace(0, beam_length, 1000)

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
        E * 1e9,
        I
    )

    fig, axes = plt.subplots(3, 1, figsize=(10, 10))

    # Shear Force Diagram
    axes[0].step(x, V, where="post")
    axes[0].axhline(0, color="black")
    axes[0].grid(True)
    axes[0].set_xlim(0, beam_length)
    axes[0].set_ylabel("Shear Force (kN)")
    axes[0].set_title(
        f"Shear Force Diagram (Max |V| = {np.max(np.abs(V)):.2f} kN)"
    )

    # Bending Moment Diagram
    axes[1].plot(x, M)
    axes[1].fill_between(x, M, alpha=0.3)
    axes[1].axhline(0, color="black")
    axes[1].grid(True)
    axes[1].set_xlim(0, beam_length)
    axes[1].set_ylabel("Moment (kN·m)")
    axes[1].set_title(
        f"Bending Moment Diagram (Max |M| = {np.max(np.abs(M)):.2f} kN·m)"
    )

    # Deflection Diagram
    y_mm = y * 1000

    axes[2].plot(x, y_mm)
    axes[2].fill_between(x, y_mm, alpha=0.3)
    axes[2].axhline(0, color="black")
    axes[2].grid(True)
    axes[2].set_xlim(0, beam_length)
    axes[2].set_xlabel("Distance along beam (m)")
    axes[2].set_ylabel("Deflection (mm)")
    axes[2].set_title(
        f"Deflection Diagram (Maximum Deflection = {np.max(np.abs(y_mm)):.3f} mm)"
    )

    plt.tight_layout()

    st.pyplot(fig)

    buffer = io.BytesIO()

    fig.savefig(
        buffer,
        format="png",
        dpi=300,
        bbox_inches="tight"
    )

    buffer.seek(0)

    st.download_button(
        label="📥 Download Beam Report (PNG)",
        data=buffer,
        file_name="beam_analysis.png",
        mime="image/png"
    )

    plt.close(fig)