import unittest

from beam_engine import analyze_beam, build_worked_solution


class WorkedSolutionTests(unittest.TestCase):
    def test_simply_supported_solution_shows_equilibrium_and_piecewise_diagrams(self):
        point_loads = [{"magnitude": -20.0, "position": 2.0}]
        distributed_loads = [
            {"intensity": -5.0, "start": 0.0, "end": 5.0}
        ]
        results = analyze_beam(
            "Simply supported",
            5.0,
            point_loads=point_loads,
            distributed_loads=distributed_loads,
        )
        solution = build_worked_solution(
            "Simply supported",
            5.0,
            point_loads,
            distributed_loads,
            [],
            results,
        )

        self.assertAlmostEqual(results["reaction_a_kN"], 24.5, places=8)
        self.assertAlmostEqual(results["reaction_b_kN"], 20.5, places=8)
        self.assertIn("ΣFy = 0", solution["reaction_steps"][0])
        self.assertIn("ΣM_A = 0", solution["reaction_steps"][1])
        self.assertIn("R_B", solution["reaction_steps"][2])
        self.assertIn("W_1", solution["udl_steps"][0]["equivalent_force"])
        self.assertEqual(len(solution["intervals"]), 2)
        self.assertIn("V(x)", solution["intervals"][0]["shear_equation"])
        self.assertIn("M(x)", solution["intervals"][1]["moment_equation"])

    def test_cantilever_solution_shows_fixed_end_actions(self):
        point_loads = [{"magnitude": -10.0, "position": 3.0}]
        results = analyze_beam(
            "Cantilever",
            3.0,
            point_loads=point_loads,
        )
        solution = build_worked_solution(
            "Cantilever",
            3.0,
            point_loads,
            [],
            [],
            results,
        )

        self.assertAlmostEqual(results["reaction_a_kN"], 10.0, places=8)
        self.assertAlmostEqual(results["fixed_moment_a_kNm"], 30.0, places=8)
        self.assertIn("M_A", solution["reaction_steps"][1])
        self.assertIn("30", solution["reaction_steps"][3])
        self.assertIn("fixed support A", solution["support_note"])

    def test_applied_couple_is_included_in_equilibrium_and_bmd_note(self):
        couples = [{"magnitude": 8.0, "position": 2.0}]
        results = analyze_beam("Simply supported", 4.0, applied_moments=couples)
        solution = build_worked_solution(
            "Simply supported",
            4.0,
            [],
            [],
            couples,
            results,
        )
        self.assertIn("+ 8", solution["reaction_steps"][1])
        self.assertIn("vertical jump", solution["applied_moment_note"])


if __name__ == "__main__":
    unittest.main()
