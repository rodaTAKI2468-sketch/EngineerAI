import io

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle

from beam_engine import analyze_beam


st.set_page_config(
    page_title="EngineerAI | Beam Lab",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem; padding-bottom: 2.5rem;}
      [data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.20);
        padding: 0.8rem 1rem;
        border-radius: 0.7rem;
      }
      .hero {
        padding: 1.2rem 1.4rem;
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 0.9rem;
        margin-bottom: 1rem;
      }
      .muted {opacity: 0.72;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏗️ EngineerAI")
st.caption("Exam-style beam analysis • Reactions • SFD • BMD • Optional deflection")

with st.sidebar:
    st.header("Beam setup")
    beam_type = st.selectbox(
        "Support condition",
        ["Simply supported", "Cantilever (fixed-free)"],
        help="A simply supported beam has a pin at A and a roller at B. "
             "A cantilever is fixed at A and free at the other end.",
    )
    engine_beam_type = (
        "Simply supported"
        if beam_type == "Simply supported"
        else "Cantilever"
    )

    beam_length = st.number_input(
        "Beam length, L (m)",
        min_value=0.1,
        max_value=100.0,
        value=5.0,
        step=0.5,
    )

    st.divider()
    calculate_deflection = st.checkbox(
        "Calculate elastic deflection",
        value=False,
        help="Turn this on only when the question provides Young's modulus E and second moment of area I.",
    )
    if calculate_deflection:
        st.subheader("Material and section")
        youngs_modulus = st.number_input(
            "Young's modulus, E (GPa)",
            min_value=0.1,
            max_value=1000.0,
            value=200.0,
            step=1.0,
            help="Enter the value supplied by the question or material data.",
        )
        second_moment = st.number_input(
            "Second moment of area, I (m⁴)",
            min_value=0.00000001,
            max_value=1000.0,
            value=0.0001,
            format="%.8f",
            step=0.00001,
            help="Enter I in m⁴ for the beam's bending axis.",
        )
    else:
        youngs_modulus = None
        second_moment = None
        st.caption("Exam mode: E and I are not needed for reactions, SFD or BMD.")

st.markdown(
    """
    <div class="hero">
      <strong>Build your loading case</strong><br>
      <span class="muted">Add as many point loads, UDL segments and applied couples as needed.
      Positive directions are upward for forces and counter-clockwise for couples.</span>
    </div>
    """,
    unsafe_allow_html=True,
)

load_tab, note_tab = st.tabs(["Loading", "Sign convention & assumptions"])

with load_tab:
    st.subheader("1. Point loads")
    point_count = st.number_input(
        "Number of point loads",
        min_value=0,
        max_value=12,
        value=1,
        step=1,
        key="point_count",
    )
    point_loads = []

    for index in range(int(point_count)):
        with st.container(border=True):
            st.markdown(f"**Point load P{index + 1}**")
            c1, c2, c3 = st.columns([1.2, 1.0, 1.0])
            magnitude = c1.number_input(
                "Magnitude (kN)",
                min_value=0.0,
                value=20.0 if index == 0 else 10.0,
                step=1.0,
                key=f"point_magnitude_{index}",
            )
            position = c2.number_input(
                "Position from A (m)",
                min_value=0.0,
                max_value=float(beam_length),
                value=min(float(beam_length), float(beam_length) * (index + 1) / (point_count + 1)),
                step=0.1,
                key=f"point_position_{index}",
            )
            direction = c3.selectbox(
                "Direction",
                ["Down", "Up"],
                key=f"point_direction_{index}",
            )
            signed_magnitude = -magnitude if direction == "Down" else magnitude
            point_loads.append(
                {"magnitude": signed_magnitude, "position": position}
            )

    st.subheader("2. Uniformly distributed loads (UDLs)")
    udl_count = st.number_input(
        "Number of UDL segments",
        min_value=0,
        max_value=8,
        value=0,
        step=1,
        key="udl_count",
    )
    distributed_loads = []

    for index in range(int(udl_count)):
        with st.container(border=True):
            st.markdown(f"**UDL {index + 1}**")
            c1, c2, c3, c4 = st.columns([1.0, 1.0, 1.0, 1.0])
            intensity = c1.number_input(
                "Intensity (kN/m)",
                min_value=0.0,
                value=5.0,
                step=0.5,
                key=f"udl_intensity_{index}",
            )
            start = c2.number_input(
                "Start (m)",
                min_value=0.0,
                max_value=float(beam_length),
                value=0.0,
                step=0.1,
                key=f"udl_start_{index}",
            )
            end = c3.number_input(
                "End (m)",
                min_value=0.0,
                max_value=float(beam_length),
                value=float(beam_length),
                step=0.1,
                key=f"udl_end_{index}",
            )
            direction = c4.selectbox(
                "Direction",
                ["Down", "Up"],
                key=f"udl_direction_{index}",
            )
            signed_intensity = -intensity if direction == "Down" else intensity
            distributed_loads.append(
                {"intensity": signed_intensity, "start": start, "end": end}
            )

    st.subheader("3. Applied moments / couples")
    couple_count = st.number_input(
        "Number of applied moments",
        min_value=0,
        max_value=8,
        value=0,
        step=1,
        key="couple_count",
    )
    applied_moments = []

    for index in range(int(couple_count)):
        with st.container(border=True):
            st.markdown(f"**Applied moment M{index + 1}**")
            c1, c2, c3 = st.columns([1.0, 1.0, 1.0])
            magnitude = c1.number_input(
                "Magnitude (kN·m)",
                min_value=0.0,
                value=10.0,
                step=1.0,
                key=f"couple_magnitude_{index}",
            )
            position = c2.number_input(
                "Position from A (m)",
                min_value=0.0,
                max_value=float(beam_length),
                value=float(beam_length) / 2.0,
                step=0.1,
                key=f"couple_position_{index}",
            )
            direction = c3.selectbox(
                "Rotation",
                ["Counter-clockwise", "Clockwise"],
                key=f"couple_direction_{index}",
            )
            signed_magnitude = (
                magnitude if direction == "Counter-clockwise" else -magnitude
            )
            applied_moments.append(
                {"magnitude": signed_magnitude, "position": position}
            )

with note_tab:
    st.markdown(
        """
        **Force convention**
        - Upward force: positive.
        - Downward force: negative.
        - Counter-clockwise applied moment: positive.
        - Clockwise applied moment: negative.

        **Analysis assumptions**
        - Linear-elastic Euler–Bernoulli beam theory.
        - Small deflections and constant E and I along the beam.
        - Ideal pin/roller or perfectly fixed support conditions.
        - UDLs are uniform over each entered interval.

        Deflection is obtained by numerically integrating the complete
        bending-moment distribution. It is not restricted to a central
        point-load case. Results are educational analysis outputs and
        should be independently checked before use in a real design.
        """
    )


def draw_beam(
    ax,
    length: float,
    beam_kind: str,
    points: list[dict[str, float]],
    udls: list[dict[str, float]],
    couples: list[dict[str, float]],
) -> None:
    """Draw a live schematic of the beam, supports and applied loads."""
    ax.plot([0, length], [0, 0], linewidth=5, solid_capstyle="round", zorder=3)

    if beam_kind == "Simply supported":
        pin = Polygon(
            [[0, -0.10], [-0.28, -0.62], [0.28, -0.62]],
            closed=True,
            fill=False,
            linewidth=1.8,
            zorder=4,
        )
        roller = Polygon(
            [[length, -0.10], [length - 0.28, -0.55], [length + 0.28, -0.55]],
            closed=True,
            fill=False,
            linewidth=1.8,
            zorder=4,
        )
        ax.add_patch(pin)
        ax.add_patch(roller)
        ax.add_patch(Circle((length, -0.66), 0.07, fill=False, linewidth=1.4))
        ax.add_patch(Circle((length - 0.16, -0.66), 0.07, fill=False, linewidth=1.4))
        ax.plot([-0.4, 0.4], [-0.78, -0.78], linewidth=1.2)
        ax.plot([length - 0.4, length + 0.4], [-0.78, -0.78], linewidth=1.2)
        ax.text(0, -0.98, "A • Pin", ha="center", va="top", fontsize=9)
        ax.text(length, -0.98, "B • Roller", ha="center", va="top", fontsize=9)
    else:
        ax.add_patch(
            Rectangle(
                (-0.24, -0.75),
                0.24,
                1.5,
                fill=False,
                hatch="////",
                linewidth=1.4,
                zorder=2,
            )
        )
        ax.text(0, -0.98, "A • Fixed", ha="center", va="top", fontsize=9)
        ax.text(length, -0.25, "Free end", ha="center", va="top", fontsize=9)

    arrow_height = 0.95
    label_offset = 0.12
    for index, load in enumerate(points):
        position = float(load["position"])
        magnitude = float(load["magnitude"])
        upward = magnitude > 0
        start_y, end_y = (
            (-arrow_height, -0.10) if upward else (arrow_height, 0.10)
        )
        ax.annotate(
            "",
            xy=(position, end_y),
            xytext=(position, start_y),
            arrowprops={"arrowstyle": "-|>", "lw": 1.8},
            zorder=5,
        )
        label_y = start_y - label_offset if upward else start_y + label_offset
        label = f"P{index + 1} = {abs(magnitude):g} kN"
        ax.text(position, label_y, label, ha="center", va="center", fontsize=8)

    for index, load in enumerate(udls):
        start = float(load["start"])
        end = float(load["end"])
        intensity = float(load["intensity"])
        if end <= start:
            continue
        upward = intensity > 0
        top_y = -0.90 if upward else 0.90
        bottom_y = -0.10 if upward else 0.10
        xs = np.linspace(start, end, 9)
        ax.plot([start, end], [top_y, top_y], linewidth=1.2)
        for position in xs:
            ax.annotate(
                "",
                xy=(position, bottom_y),
                xytext=(position, top_y),
                arrowprops={"arrowstyle": "-|>", "lw": 1.0},
                zorder=4,
            )
        ax.text(
            (start + end) / 2,
            top_y + 0.12,
            f"w{index + 1} = {abs(intensity):g} kN/m",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    for index, couple in enumerate(couples):
        position = float(couple["position"])
        magnitude = float(couple["magnitude"])
        if magnitude == 0:
            continue
        radius = max(length * 0.035, 0.18)
        sign = 1 if magnitude > 0 else -1
        arc = FancyArrowPatch(
            (position - radius, 0.55 * sign),
            (position + radius, 0.55 * sign),
            connectionstyle=f"arc3,rad={0.9 * sign}",
            arrowstyle="-|>",
            mutation_scale=11,
            linewidth=1.4,
        )
        ax.add_patch(arc)
        rotation = "CCW" if magnitude > 0 else "CW"
        ax.text(
            position,
            1.12 * sign,
            f"M{index + 1} = {abs(magnitude):g} kN·m ({rotation})",
            ha="center",
            va="center",
            fontsize=8,
        )

    ax.annotate(
        "",
        xy=(length, -1.35),
        xytext=(0, -1.35),
        arrowprops={"arrowstyle": "<->", "lw": 1.0},
    )
    ax.text(length / 2, -1.48, f"L = {length:g} m", ha="center", va="top", fontsize=9)
    ax.set_xlim(-max(length * 0.07, 0.5), length + max(length * 0.07, 0.5))
    ax.set_ylim(-1.8, 1.65)
    ax.set_aspect("auto")
    ax.axis("off")
    ax.set_title(
        "Simply supported beam" if beam_kind == "Simply supported"
        else "Cantilever beam (fixed-free)",
        loc="left",
        fontsize=12,
        fontweight="bold",
        pad=8,
    )


st.subheader("Live beam diagram")
beam_fig, beam_ax = plt.subplots(figsize=(11, 2.8))
draw_beam(
    beam_ax,
    float(beam_length),
    engine_beam_type,
    point_loads,
    distributed_loads,
    applied_moments,
)
beam_fig.tight_layout()
st.pyplot(beam_fig, use_container_width=True)
plt.close(beam_fig)

run_analysis = st.button("⚙️ Analyze beam", type="primary", use_container_width=True)

if run_analysis:
    try:
        results = analyze_beam(
            beam_type=engine_beam_type,
            beam_length=float(beam_length),
            youngs_modulus_gpa=(
                float(youngs_modulus) if youngs_modulus is not None else None
            ),
            second_moment_m4=(
                float(second_moment) if second_moment is not None else None
            ),
            point_loads=point_loads,
            distributed_loads=distributed_loads,
            applied_moments=applied_moments,
        )
    except (ValueError, KeyError, TypeError) as error:
        st.error(f"Unable to analyze this loading case: {error}")
    else:
        st.divider()
        st.header("Analysis results")

        reaction_col1, reaction_col2, reaction_col3 = st.columns(3)
        reaction_col1.metric("Vertical reaction at A", f'{results["reaction_a_kN"]:.3f} kN')
        if engine_beam_type == "Simply supported":
            reaction_col2.metric("Vertical reaction at B", f'{results["reaction_b_kN"]:.3f} kN')
        else:
            reaction_col2.metric("Fixed-end moment at A", f'{results["fixed_moment_a_kNm"]:.3f} kN·m')
        reaction_col3.metric("Maximum |shear|", f'{results["max_shear_kN"]:.3f} kN')

        result_col1, result_col2 = st.columns(2)
        result_col1.metric(
            "Maximum |bending moment|",
            f'{results["max_moment_kNm"]:.3f} kN·m',
            help=f'At x = {results["max_moment_position_m"]:.3f} m from A.',
        )
        if results["deflection"] is not None:
            result_col2.metric(
                "Maximum |deflection|",
                f'{results["max_deflection_m"] * 1000:.4f} mm',
                help=f'At x = {results["max_deflection_position_m"]:.3f} m from A.',
            )
        else:
            result_col2.info("Deflection not calculated. Enable it in the sidebar and enter E and I when provided.")

        x = results["x"]
        shear = results["shear"]
        moment = results["moment"]
        has_deflection = results["deflection"] is not None
        diagram_count = 3 if has_deflection else 2
        diagrams_fig, axes = plt.subplots(
            diagram_count,
            1,
            figsize=(11, 10 if has_deflection else 7),
            sharex=True,
        )
        axes = np.atleast_1d(axes)

        axes[0].step(x, shear, where="post", linewidth=1.8)
        axes[0].axhline(0, color="black", linewidth=0.8)
        axes[0].fill_between(x, shear, 0, step="post", alpha=0.18)
        axes[0].set_ylabel("Shear (kN)")
        axes[0].set_title("Shear Force Diagram (SFD)", loc="left")
        axes[0].grid(True, alpha=0.3)

        axes[1].plot(x, moment, linewidth=1.8)
        axes[1].axhline(0, color="black", linewidth=0.8)
        axes[1].fill_between(x, moment, 0, alpha=0.18)
        axes[1].set_ylabel("Moment (kN·m)")
        axes[1].set_title("Bending Moment Diagram (BMD)", loc="left")
        axes[1].grid(True, alpha=0.3)

        if has_deflection:
            deflection_mm = results["deflection"] * 1000.0
            axes[2].plot(x, deflection_mm, linewidth=1.8)
            axes[2].axhline(0, color="black", linewidth=0.8)
            axes[2].fill_between(x, deflection_mm, 0, alpha=0.18)
            axes[2].set_ylabel("Deflection (mm)")
            axes[2].set_title("Elastic Deflection Curve (positive downward)", loc="left")
            axes[2].grid(True, alpha=0.3)
            axes[2].invert_yaxis()

        axes[-1].set_xlabel("Distance from A, x (m)")
        for axis in axes:
            axis.set_xlim(0, float(beam_length))
        diagrams_fig.tight_layout()
        st.pyplot(diagrams_fig, use_container_width=True)

        report_buffer = io.BytesIO()
        diagrams_fig.savefig(
            report_buffer,
            format="png",
            dpi=240,
            bbox_inches="tight",
        )
        report_buffer.seek(0)
        plt.close(diagrams_fig)

        st.download_button(
            "📥 Download analysis diagrams (PNG)",
            data=report_buffer,
            file_name="engineerai_beam_analysis.png",
            mime="image/png",
        )

        st.subheader("Equilibrium check")
        eq1, eq2 = st.columns(2)
        eq1.metric(
            "ΣFy residual",
            f'{results["force_equilibrium_error_kN"]:.3e} kN',
        )
        eq2.metric(
            "ΣMA residual",
            f'{results["moment_equilibrium_error_kNm"]:.3e} kN·m',
        )
        st.caption(
            "Residuals close to zero indicate that the calculated support "
            "reactions satisfy static equilibrium."
        )

        with st.expander("Show calculation method"):
            st.markdown(
                """
                **1. Replace each UDL with its resultant**

                For a UDL of intensity w acting from a to b:

                - Resultant force: W = w(b − a)
                - Resultant location: x̄ = (a + b)/2

                **2. Apply static equilibrium**

                - ΣFy = 0
                - ΣMA = 0

                **3. Build the shear-force and bending-moment functions**

                Each point load, UDL segment and applied couple is included
                at its actual position along the beam.

                **4. Elastic deflection (optional)**

                When E and I are supplied, Euler–Bernoulli beam theory
                integrates EI(d²y/dx²) = −M(x) with the appropriate support
                boundary conditions. They are not required for reactions,
                SFD or BMD.
                """
            )

        if has_deflection:
            st.info(
                "Deflection values use the positive-downward convention and are a numerical Euler–Bernoulli estimate. "
                "Check the assumed E, I, boundary conditions and units before using results for design."
            )
        else:
            st.success(
                "Exam-style statics analysis complete. Reactions, SFD and BMD "
                "were calculated without assuming material or section properties."
            )
else:
    st.info(
        "Enter the beam and loading. For exam-style statics, E and I are not required. "
        "Enable elastic deflection only when the question provides both values."
    )

st.divider()
st.caption("EngineerAI • Learning and analysis tool for engineering students")
