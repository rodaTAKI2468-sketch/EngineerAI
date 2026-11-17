import io

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from stiffness_solver import analyze_multiple_support_beam, build_stiffness_method_steps
from multiple_support_statics import analyze_determinate_multiple_support_beam
from section_properties import rectangular_section, custom_section, calculate_beam_stresses, build_stress_steps

st.set_page_config(page_title="EngineerAI | Multiple Supports", page_icon="🏗️", layout="wide")
st.title("Multiple-Support Beam Solver")
st.caption("Continuous beams • Statically indeterminate analysis • Euler–Bernoulli stiffness method")

with st.sidebar:
    st.header("Beam and material")
    length = st.number_input("Beam length, L (m)", 1.0, 100.0, 8.0, 0.5)
    analysis_mode = st.radio("Analysis mode", ["Exam / statics (determinate; no E required)", "Stiffness / deflection (indeterminate; requires E and I)"], index=0)
    st.subheader("Beam cross-section")
    section_input = st.radio("How are the section properties given?", ["Rectangle: enter breadth and depth", "Given properties: enter A, I and c"], key="multi_section_input")
    if section_input == "Rectangle: enter breadth and depth":
        b_col, h_col = st.columns(2)
        breadth = b_col.number_input("Breadth, b (mm)", min_value=1.0, value=100.0, step=5.0, key="multi_breadth_mm")
        depth = h_col.number_input("Depth, h (mm)", min_value=1.0, value=200.0, step=5.0, key="multi_depth_mm")
        section = rectangular_section(float(breadth)/1000.0, float(depth)/1000.0)
        st.caption("Breadth b is across the section. Depth h is in the bending direction and is cubed in I = bh³/12.")
    else:
        a_col, i_col, c_col = st.columns(3)
        area_given = a_col.number_input("Area, A (mm²)", min_value=0.1, value=20000.0, format="%.2f", key="multi_area_mm2")
        inertia_given = i_col.number_input("Second moment, I (mm⁴)", min_value=0.1, value=66666666.7, format="%.2f", key="multi_custom_i_mm4")
        c_given = c_col.number_input("Extreme-fibre distance, c (mm)", min_value=0.1, value=100.0, format="%.2f", key="multi_custom_c_mm")
        section = custom_section(float(area_given)*1e-6, float(inertia_given)*1e-12, float(c_given)/1000.0)
        st.caption("For bending stress, area alone is insufficient: you also need I about the bending neutral axis and c to the outermost fibre.")
    if analysis_mode == "Stiffness / deflection (indeterminate; requires E and I)":
        youngs_modulus = st.number_input("Young's modulus, E (GPa)", 0.1, 1000.0, 200.0, 1.0)
        second_moment = section["inertia_m4"]
        st.caption(f"Using section I = {second_moment:.6g} m⁴ in the stiffness analysis.")
    else:
        youngs_modulus = None
        second_moment = section["inertia_m4"]
        st.caption("Exam/statics mode calculates reactions, SFD, BMD and stresses without E. It is limited to determinate two-simple-support beams.")
    st.divider()
    st.subheader("Supports")
    support_count = st.number_input("Number of supports", 2, 8, 2 if analysis_mode == "Exam / statics (determinate; no E required)" else 3, 1, key=f"multi_support_count_{analysis_mode}")
    supports = []
    default_positions = np.linspace(0.0, float(length), int(support_count)).tolist()
    for i in range(int(support_count)):
        with st.container(border=True):
            st.markdown(f"**Support {i+1}**")
            c1, c2 = st.columns(2)
            pos = c1.number_input(f"Position from A (m)", 0.0, float(length),
                                  float(default_positions[i]), 0.25, key=f"multi_support_pos_{i}")
            support_options = ["Roller", "Pin"] if analysis_mode == "Exam / statics (determinate; no E required)" else ["Roller", "Pin", "Fixed"]
            kind = c2.selectbox("Type", support_options,
                                index=1 if i == 0 else 0, key=f"multi_support_type_{analysis_mode}_{i}")
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
        if analysis_mode == "Exam / statics (determinate; no E required)":
            result = analyze_determinate_multiple_support_beam(
                float(length), supports, point_loads, distributed_loads, applied_moments
            )
        else:
            result = analyze_multiple_support_beam(
                float(length), float(youngs_modulus), float(second_moment), supports,
                point_loads, distributed_loads, applied_moments
            )
    except (ValueError, KeyError, TypeError, np.linalg.LinAlgError) as exc:
        st.error(str(exc))
    else:
        stiffness_mode = analysis_mode == "Stiffness / deflection (indeterminate; requires E and I)"
        if stiffness_mode:
            st.success(f"Stiffness analysis completed: {result['node_count']} nodes and {result['element_count']} elements.")
        else:
            st.success("Exam-style statics analysis completed without E or I.")
        st.subheader("Support reactions")
        rows = []
        for reaction in result["support_reactions"]:
            rows.append({
                "Support": f"{reaction['type']} at x = {reaction['position']:.3f} m",
                "Vertical reaction (kN)": reaction["vertical_kN"],
                "Reaction moment (kN·m)": reaction["moment_kNm"],
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        c1.metric("Maximum |V|", f"{result['max_shear_kN']:.3f} kN")
        c2.metric("Maximum |M|", f"{result['max_moment_kNm']:.3f} kN·m")
        if stiffness_mode:
            st.metric("Maximum deflection", f"{result['max_deflection_mm']:.3f} mm")
            st.caption(f"Maximum deflection at x = {result['max_deflection_position_m']:.3f} m (downward positive).")

        stress_result = calculate_beam_stresses(result, section)
        st.subheader("Beam stress analysis")
        st.caption("Elastic bending stress uses σ = Mc/I. Rectangular maximum transverse shear uses τmax = 1.5V/A; for a user-defined section the displayed shear stress is the average V/A.")
        sc1, sc2 = st.columns(2)
        sc1.metric("Maximum bending stress, σmax", f"{stress_result['max_bending_stress_mpa']:.3f} MPa")
        shear_label = "Maximum shear stress, τmax" if section.get("shear_factor") else "Average shear stress, τavg"
        sc2.metric(shear_label, f"{stress_result['max_shear_stress_mpa']:.3f} MPa")
        st.write(f"Maximum bending stress occurs at x = {stress_result['max_moment_position_m']:.3f} m; maximum shear stress is based on V at x = {stress_result['max_shear_position_m']:.3f} m.")
        st.write(f"Section properties: A = {section['area_m2']:.6g} m², I = {section['inertia_m4']:.6g} m⁴, c = {section['c_m']:.6g} m, Z = {section['section_modulus_m3']:.6g} m³.")

        tabs = st.tabs(["Shear force diagram", "Bending moment diagram"] + (["Deflection"] if stiffness_mode else []))
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
        if stiffness_mode:
            with tabs[2]:
                fig, ax = plt.subplots(figsize=(10, 3.8))
                ax.plot(result["x"], result["deflection_mm"], linewidth=2)
                ax.axhline(0, color="black", linewidth=0.8)
                ax.set_ylabel("Deflection (mm, downward +)")
                ax.set_xlabel("Distance from A (m)")
                ax.grid(True, alpha=0.25)
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

        if stiffness_mode:
            st.subheader("Step-by-step stiffness-method solution")
            for step in build_stiffness_method_steps(result, supports, point_loads,
                                                      distributed_loads, applied_moments,
                                                      float(youngs_modulus), float(second_moment)):
                st.write(step)
        else:
            st.subheader("Step-by-step exam solution")
            st.markdown("**Sign convention:** upward forces and counter-clockwise applied couples are positive.")
            for step in result["reaction_steps"]:
                st.code(step)
            st.write("Convert each UDL into an equivalent point load: W = wL, acting at the centre of the loaded length.")
            st.write("Construct the SFD from left to right: reactions and point loads cause vertical jumps; a UDL causes a linear change in shear.")
            st.write("Construct the BMD by taking moments of all forces to the left of each section. Applied couples cause a moment jump.")
            st.info("This mode calculates reactions, SFD, BMD and elastic stresses without E. Deflection cannot be calculated without EI.")
        st.subheader("Step-by-step cross-section and stress solution")
        for step in build_stress_steps(section, stress_result):
            st.write(step)
        st.warning("Stress results use linear-elastic beam theory. Verify the section orientation, material limits, local effects and applicable design standards independently.")
