import io

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from stiffness_solver import analyze_multiple_support_beam, build_stiffness_method_steps

st.set_page_config(page_title="EngineerAI | Multiple Supports", page_icon="🏗️", layout="wide")
st.title("Multiple-Support Beam Solver")
st.caption("Continuous beams • Statically indeterminate analysis • Euler–Bernoulli stiffness method")

with st.sidebar:
    st.header("Beam and material")
    length = st.number_input("Beam length, L (m)", 1.0, 100.0, 8.0, 0.5)
    youngs_modulus = st.number_input("Young's modulus, E (GPa)", 0.1, 1000.0, 200.0, 1.0)
    second_moment = st.number_input("Second moment of area, I (m⁴)", 1e-8, 1000.0, 1e-4, format="%.8f")
    st.caption("E and I are required because the stiffness method calculates deformation compatibility.")
    st.divider()
    st.subheader("Supports")
    support_count = st.number_input("Number of supports", 2, 8, 3, 1)
    supports = []
    default_positions = np.linspace(0.0, float(length), int(support_count)).tolist()
    for i in range(int(support_count)):
        with st.container(border=True):
            st.markdown(f"**Support {i+1}**")
            c1, c2 = st.columns(2)
            pos = c1.number_input(f"Position from A (m)", 0.0, float(length),
                                  float(default_positions[i]), 0.25, key=f"multi_support_pos_{i}")
            kind = c2.selectbox("Type", ["Roller", "Pin", "Fixed"],
                                index=2 if i == 0 else 0, key=f"multi_support_type_{i}")
            supports.append({"position": float(pos), "type": kind})
    st.divider()
    st.subheader("Loading")
    point_count = st.number_input("Point loads", 0, 12, 1, 1)
    point_loads = []
    for i in range(int(point_count)):
        c1, c2, c3 = st.columns(3)
        mag = c1.number_input(f"P{i+1} (kN)", 0.0, value=20.0 if i == 0 else 10.0, key=f"multi_p_mag_{i}")
        pos = c2.number_input(f"x{i+1} (m)", 0.0, float(length), float(length)*(i+1)/(int(point_count)+1), key=f"multi_p_pos_{i}")
        direction = c3.selectbox(f"Direction {i+1}", ["Down", "Up"], key=f"multi_p_dir_{i}")
        point_loads.append({"magnitude": mag if direction == "Up" else -mag, "position": float(pos)})
    udl_count = st.number_input("UDL segments", 0, 8, 1, 1)
    distributed_loads = []
    for i in range(int(udl_count)):
        c1, c2, c3 = st.columns(3)
        intensity = c1.number_input(f"w{i+1} (kN/m)", 0.0, value=5.0, key=f"multi_udl_mag_{i}")
        start = c2.number_input(f"Start {i+1} (m)", 0.0, float(length), 0.0, key=f"multi_udl_start_{i}")
        end = c3.number_input(f"End {i+1} (m)", 0.0, float(length), float(length), key=f"multi_udl_end_{i}")
        distributed_loads.append({"intensity": -intensity, "start": float(start), "end": float(end)})
    couple_count = st.number_input("Applied couples", 0, 8, 0, 1)
    applied_moments = []
    for i in range(int(couple_count)):
        c1, c2, c3 = st.columns(3)
        mag = c1.number_input(f"M{i+1} (kN·m)", 0.0, value=10.0, key=f"multi_m_mag_{i}")
        pos = c2.number_input(f"Position {i+1} (m)", 0.0, float(length), float(length)/2, key=f"multi_m_pos_{i}")
        direction = c3.selectbox(f"Rotation {i+1}", ["CCW", "CW"], key=f"multi_m_dir_{i}")
        applied_moments.append({"magnitude": mag if direction == "CCW" else -mag, "position": float(pos)})

st.subheader("Beam layout")
fig, ax = plt.subplots(figsize=(12, 2.6))
ax.plot([0, length], [0, 0], linewidth=5, solid_capstyle="round")
for i, support in enumerate(supports):
    x = support["position"]
    kind = support["type"]
    if kind == "Fixed":
        ax.plot([x, x], [-0.55, 0.55], linewidth=3)
        ax.fill_betweenx([-0.65, 0.65], x-0.16, x, hatch="////", facecolor="none", edgecolor="gray")
    else:
        ax.plot([x, x-0.22, x+0.22, x], [0, -0.38, -0.38, 0], linewidth=1.4)
        if kind == "Roller":
            ax.scatter([x], [-0.46], s=28, facecolors="none", edgecolors="black")
    ax.text(x, -0.85, f"{kind} S{i+1}", ha="center", fontsize=8)
for i, load in enumerate(point_loads):
    x = load["position"]
    down = load["magnitude"] < 0
    ax.annotate("", xy=(x, -0.05 if down else 0.05), xytext=(x, -0.8 if down else 0.8),
                arrowprops={"arrowstyle": "-|>", "lw": 1.4})
    ax.text(x, -1.0 if down else 0.95, f"P{i+1}={abs(load['magnitude']):g}", ha="center", fontsize=8)
for i, load in enumerate(distributed_loads):
    if load["end"] > load["start"]:
        for x in np.linspace(load["start"], load["end"], 9):
            ax.annotate("", xy=(x, -0.04), xytext=(x, 0.55),
                        arrowprops={"arrowstyle": "-|>", "lw": 0.8})
        ax.text((load["start"]+load["end"])/2, 0.62, f"w{i+1}={abs(load['intensity']):g} kN/m", ha="center", fontsize=8)
ax.set_xlim(-0.5, float(length)+0.5)
ax.set_ylim(-1.25, 1.25)
ax.axis("off")
fig.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close(fig)

if st.button("Analyse multiple-support beam", type="primary", use_container_width=True):
    try:
        result = analyze_multiple_support_beam(
            float(length), float(youngs_modulus), float(second_moment), supports,
            point_loads, distributed_loads, applied_moments
        )
    except (ValueError, KeyError, TypeError, np.linalg.LinAlgError) as exc:
        st.error(str(exc))
    else:
        st.success(f"Analysis completed: {result['node_count']} nodes and {result['element_count']} elements.")
        st.subheader("Support reactions")
        rows = []
        for reaction in result["support_reactions"]:
            rows.append({
                "Support": f"{reaction['type']} at x = {reaction['position']:.3f} m",
                "Vertical reaction (kN)": reaction["vertical_kN"],
                "Reaction moment (kN·m)": reaction["moment_kNm"],
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Maximum |V|", f"{result['max_shear_kN']:.3f} kN")
        c2.metric("Maximum |M|", f"{result['max_moment_kNm']:.3f} kN·m")
        c3.metric("Maximum deflection", f"{result['max_deflection_mm']:.3f} mm")
        st.caption(f"Maximum deflection at x = {result['max_deflection_position_m']:.3f} m (downward positive).")

        tabs = st.tabs(["Shear force diagram", "Bending moment diagram", "Deflection"])
        with tabs[0]:
            fig, ax = plt.subplots(figsize=(10, 3.8))
            ax.plot(result["x"], result["shear"], linewidth=2)
            ax.axhline(0, color="black", linewidth=0.8)
            ax.set_ylabel("Shear (kN)")
            ax.set_xlabel("Distance from A (m)")
            ax.grid(True, alpha=0.25)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        with tabs[1]:
            fig, ax = plt.subplots(figsize=(10, 3.8))
            ax.plot(result["x"], result["moment"], linewidth=2)
            ax.axhline(0, color="black", linewidth=0.8)
            ax.set_ylabel("Moment (kN·m)")
            ax.set_xlabel("Distance from A (m)")
            ax.grid(True, alpha=0.25)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        with tabs[2]:
            fig, ax = plt.subplots(figsize=(10, 3.8))
            ax.plot(result["x"], result["deflection_mm"], linewidth=2)
            ax.axhline(0, color="black", linewidth=0.8)
            ax.set_ylabel("Deflection (mm, downward +)")
            ax.set_xlabel("Distance from A (m)")
            ax.grid(True, alpha=0.25)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

        st.subheader("Step-by-step stiffness-method solution")
        for step in build_stiffness_method_steps(result, supports, point_loads,
                                                  distributed_loads, applied_moments,
                                                  float(youngs_modulus), float(second_moment)):
            st.write(step)
        st.warning("Educational analysis only. Verify results independently before using them for design.")
