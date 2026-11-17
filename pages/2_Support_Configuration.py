import io

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.patches import Circle, Polygon, Rectangle

from support_config import SUPPORT_TYPES, analyze_support_configuration, classify_supports

st.set_page_config(page_title="EngineerAI | Support Configuration", page_icon="🏗️", layout="wide")
st.title("Support Configuration System")
st.caption("Choose each end support independently • Transverse beam analysis")

with st.sidebar:
    st.header("Beam and supports")
    length = st.number_input("Beam length, L (m)", 0.1, 100.0, 5.0, 0.5)
    c1, c2 = st.columns(2)
    support_a = c1.selectbox("Support at A", SUPPORT_TYPES, index=0)
    support_b = c2.selectbox("Support at B", SUPPORT_TYPES, index=1)
    st.divider()
    st.subheader("Loading")
    point_loads = []
    p_count = st.number_input("Point loads", 0, 12, 1, key="cfg_p_count")
    for i in range(int(p_count)):
        c1, c2, c3 = st.columns([1, 1, 1])
        mag = c1.number_input(f"P{i+1} (kN)", 0.0, value=20.0, key=f"cfg_p_mag_{i}")
        pos = c2.number_input(f"x{i+1} (m)", 0.0, float(length), float(length)/2, key=f"cfg_p_pos_{i}")
        direction = c3.selectbox(f"Direction {i+1}", ["Down", "Up"], key=f"cfg_p_dir_{i}")
        point_loads.append({"magnitude": mag if direction == "Up" else -mag, "position": pos})

    udls = []
    w_count = st.number_input("UDL segments", 0, 8, 0, key="cfg_w_count")
    for i in range(int(w_count)):
        c1, c2, c3 = st.columns(3)
        intensity = c1.number_input(f"w{i+1} (kN/m)", 0.0, value=5.0, key=f"cfg_w_mag_{i}")
        start = c2.number_input(f"Start {i+1} (m)", 0.0, float(length), 0.0, key=f"cfg_w_start_{i}")
        end = c3.number_input(f"End {i+1} (m)", 0.0, float(length), float(length), key=f"cfg_w_end_{i}")
        udls.append({"intensity": -intensity, "start": start, "end": end})

    couples = []
    m_count = st.number_input("Applied couples", 0, 8, 0, key="cfg_m_count")
    for i in range(int(m_count)):
        c1, c2, c3 = st.columns(3)
        mag = c1.number_input(f"M{i+1} (kN·m)", 0.0, value=10.0, key=f"cfg_m_mag_{i}")
        pos = c2.number_input(f"Position {i+1} (m)", 0.0, float(length), float(length)/2, key=f"cfg_m_pos_{i}")
        direction = c3.selectbox(f"Rotation {i+1}", ["CCW", "CW"], key=f"cfg_m_dir_{i}")
        couples.append({"magnitude": mag if direction == "CCW" else -mag, "position": pos})

classification = classify_supports(support_a, support_b)
st.subheader("Live support arrangement")
fig, ax = plt.subplots(figsize=(11, 2.4))
ax.plot([0, length], [0, 0], linewidth=5, solid_capstyle="round")
def draw_support(x, kind, label):
    if kind == "Fixed":
        ax.add_patch(Rectangle((x-0.22, -0.65), 0.22, 1.3, fill=False, hatch="////", linewidth=1.5))
    elif kind == "Pin":
        ax.add_patch(Polygon([[x, -0.08], [x-0.28, -0.55], [x+0.28, -0.55]], fill=False, linewidth=1.5))
        ax.plot([x-0.4, x+0.4], [-0.65, -0.65], linewidth=1)
    elif kind == "Roller":
        ax.add_patch(Polygon([[x, -0.08], [x-0.28, -0.48], [x+0.28, -0.48]], fill=False, linewidth=1.5))
        ax.add_patch(Circle((x, -0.58), 0.07, fill=False))
        ax.plot([x-0.4, x+0.4], [-0.72, -0.72], linewidth=1)
    ax.text(x, -0.9, f"{label}: {kind}", ha="center", fontsize=9)
draw_support(0, support_a, "A")
draw_support(float(length), support_b, "B")
for i, load in enumerate(point_loads):
    x = load["position"]
    sign = 1 if load["magnitude"] < 0 else -1
    ax.annotate("", xy=(x, 0.08*sign), xytext=(x, 0.9*sign), arrowprops={"arrowstyle":"-|>", "lw":1.6})
    ax.text(x, 1.0*sign, f"P{i+1}={abs(load['magnitude']):g} kN", ha="center", fontsize=8)
for i, load in enumerate(udls):
    xs = np.linspace(load["start"], load["end"], 8)
    if load["end"] > load["start"]:
        ax.plot([load["start"], load["end"]], [0.85, 0.85], linewidth=1)
        for x in xs:
            ax.annotate("", xy=(x, 0.08), xytext=(x, 0.85), arrowprops={"arrowstyle":"-|>", "lw":0.9})
        ax.text((load["start"]+load["end"])/2, 0.95, f"w{i+1}={abs(load['intensity']):g} kN/m", ha="center", fontsize=8)
ax.set_xlim(-0.6, length+0.6)
ax.set_ylim(-1.2, 1.5)
ax.axis("off")
ax.set_title(f"A: {support_a}  |  B: {support_b}", loc="left")
fig.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close(fig)

if classification["status"] == "unstable":
    st.error("Unstable structure — no valid static beam solution.")
    st.write(classification["reason"])
elif classification["status"] == "indeterminate":
    st.warning("Statically indeterminate — equilibrium alone cannot determine all reactions.")
    st.write(classification["reason"])
    st.info("A future stiffness-method solver will require E and I (and, where relevant, section variation and support settlement).")
else:
    st.success("Statically determinate for transverse beam loading.")
    st.write(classification["reason"])
    st.caption("Model scope: vertical loads, vertical reactions and bending. Axial/horizontal restraint compatibility is not solved. A pin–pin arrangement is treated as determinate only for this transverse beam model.")
    if st.button("Analyze beam", type="primary", use_container_width=True):
        try:
            result = analyze_support_configuration(support_a, support_b, float(length), point_loads, udls, couples)
        except (ValueError, KeyError, TypeError) as exc:
            st.error(str(exc))
        else:
            st.subheader("Support reactions")
            cols = st.columns(4)
            cols[0].metric("Vertical reaction at A", f"{result['reaction_a_kN']:.3f} kN")
            cols[1].metric("Vertical reaction at B", f"{result['reaction_b_kN']:.3f} kN")
            cols[2].metric("Fixing moment at A", f"{result['fixed_moment_a_kNm']:.3f} kN·m")
            cols[3].metric("Fixing moment at B", f"{result['fixed_moment_b_kNm']:.3f} kN·m")
            st.caption(result["support_explanation"])
            fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
            axes[0].step(result["x"], result["shear"], where="post")
            axes[0].axhline(0, color="black", linewidth=0.8)
            axes[0].set_ylabel("Shear (kN)")
            axes[0].set_title("Shear Force Diagram (SFD)", loc="left")
            axes[0].grid(True, alpha=0.25)
            axes[1].plot(result["x"], result["moment"])
            axes[1].axhline(0, color="black", linewidth=0.8)
            axes[1].set_ylabel("Moment (kN·m)")
            axes[1].set_xlabel("Distance from A (m)")
            axes[1].set_title("Bending Moment Diagram (BMD)", loc="left")
            axes[1].grid(True, alpha=0.25)
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
            buffer = io.BytesIO()
            fig.savefig(buffer, format="png", dpi=220, bbox_inches="tight")
            buffer.seek(0)
            plt.close(fig)
            st.download_button("Download SFD/BMD (PNG)", buffer, "engineerai_support_beam.png", "image/png")

            st.subheader("Step-by-step solution")
            worked = result["worked_solution"]
            st.markdown("**1. Identify support restraints**")
            st.write(worked["support_note"])
            st.markdown("**2. Convert UDLs to equivalent point loads**")
            if worked["udl_steps"]:
                for step in worked["udl_steps"]:
                    st.write(step["label"])
                    st.code(step["equivalent_force"] + "\n" + step["centroid"])
            else:
                st.write("No UDLs were entered.")
            st.markdown("**3. Solve support reactions using equilibrium**")
            st.code("\n".join(worked["reaction_steps"]))
            st.markdown("**4. SFD and BMD**")
            if worked["intervals"]:
                for i, section in enumerate(worked["intervals"], 1):
                    st.markdown(f"Interval {i}: {section['start']:.3g} < x < {section['end']:.3g} m")
                    st.code(section["shear_equation"] + "\n" + section["moment_equation"])
            else:
                st.write("The mirrored cantilever solution is expressed from the fixed end B; the diagram above is shown in A-to-B coordinates.")
            st.write(worked["boundary_note"])
            st.write(worked["applied_moment_note"])
            st.caption("Check equilibrium residuals and independently verify results before engineering use.")
