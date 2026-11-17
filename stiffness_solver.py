"""Euler-Bernoulli beam finite-element stiffness solver for multiple supports.

Units: kN, m, kN/m, kN.m, E in GPa and I in m^4.
Vertical displacement is positive upward internally; returned deflection is positive downward.
Applied couples are positive counter-clockwise.
"""
from __future__ import annotations

from typing import Any
import numpy as np


def _validate(length, youngs_modulus_gpa, second_moment_m4, supports,
              point_loads, distributed_loads, applied_moments):
    if not np.isfinite(length) or length <= 0:
        raise ValueError("Beam length must be greater than zero.")
    if not np.isfinite(youngs_modulus_gpa) or youngs_modulus_gpa <= 0:
        raise ValueError("Young's modulus E must be greater than zero.")
    if not np.isfinite(second_moment_m4) or second_moment_m4 <= 0:
        raise ValueError("Second moment of area I must be greater than zero.")
    if len(supports) < 2:
        raise ValueError("Enter at least two supports for multiple-support analysis.")
    tol = 1e-9
    seen = []
    for i, support in enumerate(supports, 1):
        x, kind = float(support["position"]), support["type"]
        if not np.isfinite(x) or x < -tol or x > length + tol:
            raise ValueError(f"Support {i} position must be between 0 and the beam length.")
        if kind not in {"Pin", "Roller", "Fixed"}:
            raise ValueError(f"Support {i} must be Pin, Roller or Fixed.")
        if any(abs(x - old) < tol for old in seen):
            raise ValueError("Two supports cannot occupy the same position.")
        seen.append(x)
    for i, load in enumerate(point_loads, 1):
        x, p = float(load["position"]), float(load["magnitude"])
        if not np.isfinite(x) or not np.isfinite(p) or x < -tol or x > length + tol:
            raise ValueError(f"Point load {i} must have a finite magnitude and a position on the beam.")
    for i, load in enumerate(distributed_loads, 1):
        a, b, q = float(load["start"]), float(load["end"]), float(load["intensity"])
        if not all(np.isfinite(v) for v in (a, b, q)) or a < -tol or b > length + tol or a >= b:
            raise ValueError(f"UDL {i} must satisfy 0 ≤ start < end ≤ beam length.")
    for i, load in enumerate(applied_moments, 1):
        x, m = float(load["position"]), float(load["magnitude"])
        if not np.isfinite(x) or not np.isfinite(m) or x < -tol or x > length + tol:
            raise ValueError(f"Applied moment {i} must have a finite magnitude and a position on the beam.")


def _element_stiffness(ei: float, le: float) -> np.ndarray:
    return (ei / le**3) * np.array([
        [12.0, 6.0*le, -12.0, 6.0*le],
        [6.0*le, 4.0*le**2, -6.0*le, 2.0*le**2],
        [-12.0, -6.0*le, 12.0, -6.0*le],
        [6.0*le, 2.0*le**2, -6.0*le, 4.0*le**2],
    ])


def analyze_multiple_support_beam(
    beam_length: float,
    youngs_modulus_gpa: float,
    second_moment_m4: float,
    supports: list[dict[str, Any]],
    point_loads: list[dict[str, float]] | None = None,
    distributed_loads: list[dict[str, float]] | None = None,
    applied_moments: list[dict[str, float]] | None = None,
    max_element_length: float = 0.25,
    samples_per_element: int = 8,
) -> dict[str, Any]:
    """Solve a continuous beam with arbitrary vertical supports using beam elements.

    Support: {"position": m, "type": "Pin"|"Roller"|"Fixed"}
    Point load: {"position": m, "magnitude": signed kN}
    UDL: {"start": m, "end": m, "intensity": signed kN/m}
    Applied couple: {"position": m, "magnitude": signed kN.m}
    """
    point_loads = point_loads or []
    distributed_loads = distributed_loads or []
    applied_moments = applied_moments or []
    _validate(beam_length, youngs_modulus_gpa, second_moment_m4, supports,
              point_loads, distributed_loads, applied_moments)
    if max_element_length <= 0:
        raise ValueError("Maximum element length must be positive.")

    # Place nodes exactly at all supports and load discontinuities, then refine
    # the mesh so the displacement and internal-force curves are well resolved.
    events = [0.0, float(beam_length)]
    events.extend(float(s["position"]) for s in supports)
    events.extend(float(p["position"]) for p in point_loads)
    events.extend(float(m["position"]) for m in applied_moments)
    for load in distributed_loads:
        events.extend([float(load["start"]), float(load["end"])])
    sorted_events = sorted(events)
    base = []
    for event in sorted_events:
        if not base or abs(event - base[-1]) > 1e-9:
            base.append(event)
    nodes = [base[0]]
    for left, right in zip(base[:-1], base[1:]):
        count = max(1, int(np.ceil((right-left)/max_element_length)))
        nodes.extend(np.linspace(left, right, count+1)[1:].tolist())
    x_nodes = np.asarray(nodes, dtype=float)
    n = len(x_nodes)
    ndof = 2*n
    ei = float(youngs_modulus_gpa) * 1e6 * float(second_moment_m4)  # kN.m^2
    K = np.zeros((ndof, ndof), dtype=float)
    F = np.zeros(ndof, dtype=float)
    element_data = []

    for e in range(n-1):
        xa, xb = float(x_nodes[e]), float(x_nodes[e+1])
        le = xb-xa
        ke = _element_stiffness(ei, le)
        fe = np.zeros(4, dtype=float)
        q = sum(float(load["intensity"]) for load in distributed_loads
                if xa >= float(load["start"])-1e-9 and xb <= float(load["end"])+1e-9)
        if abs(q) > 0:
            fe += np.array([q*le/2.0, q*le**2/12.0, q*le/2.0, -q*le**2/12.0])
        dofs = np.array([2*e, 2*e+1, 2*(e+1), 2*(e+1)+1])
        K[np.ix_(dofs, dofs)] += ke
        F[dofs] += fe
        element_data.append({"dofs": dofs, "ke": ke, "fe": fe, "q": q, "length": le})

    def node_index(position):
        return int(np.argmin(np.abs(x_nodes-float(position))))

    for load in point_loads:
        F[2*node_index(load["position"])] += float(load["magnitude"])
    for load in applied_moments:
        F[2*node_index(load["position"])+1] += float(load["magnitude"])

    constrained = []
    for support in supports:
        idx = node_index(support["position"])
        constrained.append(2*idx)
        if support["type"] == "Fixed":
            constrained.append(2*idx+1)
    constrained = np.array(sorted(set(constrained)), dtype=int)
    free = np.setdiff1d(np.arange(ndof), constrained)
    displacement = np.zeros(ndof, dtype=float)
    if len(free):
        Kff = K[np.ix_(free, free)]
        try:
            displacement[free] = np.linalg.solve(Kff, F[free])
        except np.linalg.LinAlgError as exc:
            raise ValueError(
                "The support arrangement is unstable or insufficiently restrained. "
                "Add or reposition supports, or use a fixed support to restrain rotation."
            ) from exc
        if not np.all(np.isfinite(displacement)):
            raise ValueError("The stiffness solution is non-finite; check the support arrangement and input values.")

    reactions = K @ displacement - F
    support_reactions = []
    for support in sorted(supports, key=lambda s: float(s["position"])):
        idx = node_index(support["position"])
        item = {
            "position": float(support["position"]),
            "type": support["type"],
            "vertical_kN": float(reactions[2*idx]),
            "moment_kNm": float(reactions[2*idx+1]) if support["type"] == "Fixed" else 0.0,
        }
        support_reactions.append(item)

    # Recover element shear/moment from the left-end element actions and the
    # element's uniform load. Moment is positive sagging.
    xs, shears, moments, deflections = [], [], [], []
    for e, data in enumerate(element_data):
        le = data["length"]
        dofs = data["dofs"]
        de = displacement[dofs]
        end_actions = data["ke"] @ de - data["fe"]
        q = data["q"]
        s = np.linspace(0.0, le, max(3, int(samples_per_element)))
        v = end_actions[0] + q*s
        m = -end_actions[1] + end_actions[0]*s + 0.5*q*s**2
        # Cubic Hermite interpolation of vertical displacement.
        r = s/le
        h1 = 1-3*r**2+2*r**3
        h2 = le*(r-2*r**2+r**3)
        h3 = 3*r**2-2*r**3
        h4 = le*(-r**2+r**3)
        v_up = h1*de[0] + h2*de[1] + h3*de[2] + h4*de[3]
        start = x_nodes[e]
        if e:
            s, v, m, v_up = s[1:], v[1:], m[1:], v_up[1:]
        xs.extend((start+s).tolist())
        shears.extend(v.tolist())
        moments.extend(m.tolist())
        deflections.extend((-v_up*1000.0).tolist())  # mm, downward positive

    x = np.asarray(xs)
    shear = np.asarray(shears)
    moment = np.asarray(moments)
    deflection_mm = np.asarray(deflections)
    max_def_idx = int(np.argmax(np.abs(deflection_mm)))
    force_residual = float(sum(r["vertical_kN"] for r in support_reactions)
                           + sum(float(p["magnitude"]) for p in point_loads)
                           + sum(float(w["intensity"])*(float(w["end"])-float(w["start"])) for w in distributed_loads))
    moment_residual = float(sum(r["vertical_kN"]*r["position"] + r["moment_kNm"] for r in support_reactions)
                            + sum(float(p["magnitude"])*float(p["position"]) for p in point_loads)
                            + sum(float(w["intensity"])*(float(w["end"])-float(w["start"]))*0.5*(float(w["start"])+float(w["end"])) for w in distributed_loads)
                            + sum(float(m["magnitude"]) for m in applied_moments))
    return {
        "x": x, "shear": shear, "moment": moment, "deflection_mm": deflection_mm,
        "support_reactions": support_reactions,
        "displacements": displacement.reshape(-1, 2),
        "node_positions": x_nodes,
        "force_equilibrium_error_kN": force_residual,
        "moment_equilibrium_error_kNm": moment_residual,
        "max_deflection_mm": float(abs(deflection_mm[max_def_idx])),
        "max_deflection_position_m": float(x[max_def_idx]),
        "max_moment_kNm": float(np.max(np.abs(moment))),
        "max_shear_kN": float(np.max(np.abs(shear))),
        "element_count": len(element_data),
        "node_count": n,
        "ei_kNm2": ei,
    }


def build_stiffness_method_steps(result: dict[str, Any], supports: list[dict[str, Any]],
                                point_loads: list[dict[str, float]],
                                distributed_loads: list[dict[str, float]],
                                applied_moments: list[dict[str, float]],
                                youngs_modulus_gpa: float, second_moment_m4: float) -> list[str]:
    """Human-readable outline of the assembled stiffness-method solution."""
    steps = [
        "1. Discretise the beam: place nodes at supports, point loads, applied couples and UDL boundaries, then subdivide each span.",
        "2. Define two degrees of freedom at every node: vertical displacement v and rotation θ.",
        "3. For each element of length Lₑ, form the Euler–Bernoulli stiffness matrix: kₑ = (EI/Lₑ³) [[12, 6Lₑ, −12, 6Lₑ], [6Lₑ, 4Lₑ², −6Lₑ, 2Lₑ²], [−12, −6Lₑ, 12, −6Lₑ], [6Lₑ, 2Lₑ², −6Lₑ, 4Lₑ²]].",
        "4. Convert distributed loads on each element into consistent nodal loads and add point loads/couples to their corresponding nodes.",
        "5. Assemble the global stiffness matrix K and load vector F. Apply support boundary conditions: Pin/Roller restrain vertical displacement; Fixed restrains vertical displacement and rotation.",
        "6. Solve the free degrees of freedom: K_ff d_f = F_f. Recover support actions from R = Kd − F.",
        f"7. Material/section stiffness: E = {youngs_modulus_gpa:g} GPa, I = {second_moment_m4:.6g} m⁴, EI = {result['ei_kNm2']:.6g} kN·m².",
        f"8. Numerical model: {result['node_count']} nodes and {result['element_count']} beam elements. Deflection is reported in mm, positive downward.",
    ]
    steps.append(
        "9. Equilibrium check: ΣFy residual = "
        f"{result['force_equilibrium_error_kN']:.3e} kN; ΣM_A residual = "
        f"{result['moment_equilibrium_error_kNm']:.3e} kN·m."
    )
    return steps
