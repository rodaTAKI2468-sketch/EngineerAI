import unittest

from beam_engine import analyze_beam


class BeamEngineTests(unittest.TestCase):
    def setUp(self):
        self.e_gpa = 200.0
        self.i_m4 = 1.0e-4

    def test_multiple_point_loads_on_simply_supported_beam(self):
        result = analyze_beam(
            "Simply supported",
            6.0,
            self.e_gpa,
            self.i_m4,
            point_loads=[
                {"magnitude": -10.0, "position": 2.0},
                {"magnitude": -20.0, "position": 5.0},
            ],
        )
        self.assertAlmostEqual(result["reaction_a_kN"], 10.0, places=8)
        self.assertAlmostEqual(result["reaction_b_kN"], 20.0, places=8)
        self.assertAlmostEqual(result["force_equilibrium_error_kN"], 0.0, places=8)
        self.assertAlmostEqual(result["moment_equilibrium_error_kNm"], 0.0, places=8)

    def test_full_span_udl_reactions_and_maximum_moment(self):
        result = analyze_beam(
            "Simply supported",
            4.0,
            self.e_gpa,
            self.i_m4,
            distributed_loads=[
                {"intensity": -2.0, "start": 0.0, "end": 4.0},
            ],
        )
        self.assertAlmostEqual(result["reaction_a_kN"], 4.0, places=8)
        self.assertAlmostEqual(result["reaction_b_kN"], 4.0, places=8)
        self.assertAlmostEqual(result["max_moment_kNm"], 4.0, delta=0.01)

    def test_cantilever_with_end_point_load_deflection(self):
        result = analyze_beam(
            "Cantilever",
            3.0,
            self.e_gpa,
            self.i_m4,
            point_loads=[{"magnitude": -10.0, "position": 3.0}],
        )
        expected_deflection_m = (
            10_000.0 * 3.0**3
            / (3.0 * (self.e_gpa * 1e9) * self.i_m4)
        )
        self.assertAlmostEqual(result["reaction_a_kN"], 10.0, places=8)
        self.assertAlmostEqual(result["fixed_moment_a_kNm"], 30.0, places=8)
        self.assertAlmostEqual(
            result["max_deflection_m"],
            expected_deflection_m,
            delta=expected_deflection_m * 0.002,
        )

    def test_central_point_load_simply_supported_deflection(self):
        result = analyze_beam(
            "Simply supported",
            4.0,
            self.e_gpa,
            self.i_m4,
            point_loads=[{"magnitude": -20.0, "position": 2.0}],
        )
        expected_deflection_m = (
            20_000.0 * 4.0**3
            / (48.0 * (self.e_gpa * 1e9) * self.i_m4)
        )
        self.assertAlmostEqual(
            result["max_deflection_m"],
            expected_deflection_m,
            delta=expected_deflection_m * 0.002,
        )

    def test_applied_couple_is_included_in_reactions(self):
        result = analyze_beam(
            "Simply supported",
            4.0,
            self.e_gpa,
            self.i_m4,
            applied_moments=[{"magnitude": 8.0, "position": 2.0}],
        )
        self.assertAlmostEqual(result["reaction_a_kN"], 2.0, places=8)
        self.assertAlmostEqual(result["reaction_b_kN"], -2.0, places=8)
        self.assertAlmostEqual(result["moment_equilibrium_error_kNm"], 0.0, places=8)

    def test_invalid_udl_interval_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_beam(
                "Simply supported",
                4.0,
                self.e_gpa,
                self.i_m4,
                distributed_loads=[
                    {"intensity": -3.0, "start": 3.0, "end": 2.0},
                ],
            )

    def test_exam_style_statics_does_not_require_material_or_section_data(self):
        result = analyze_beam(
            "Simply supported",
            6.0,
            point_loads=[
                {"magnitude": -10.0, "position": 2.0},
                {"magnitude": -20.0, "position": 5.0},
            ],
        )
        self.assertAlmostEqual(result["reaction_a_kN"], 10.0, places=8)
        self.assertAlmostEqual(result["reaction_b_kN"], 20.0, places=8)
        self.assertIsNone(result["deflection"])
        self.assertIsNone(result["max_deflection_m"])

    def test_deflection_requires_both_E_and_I_or_neither(self):
        with self.assertRaises(ValueError):
            analyze_beam(
                "Simply supported",
                4.0,
                youngs_modulus_gpa=200.0,
                point_loads=[{"magnitude": -10.0, "position": 2.0}],
            )

    def test_downward_udl_has_positive_sagging_moment_on_simply_supported_beam(self):
        result = analyze_beam(
            "Simply supported",
            4.0,
            distributed_loads=[{"intensity": -2.0, "start": 0.0, "end": 4.0}],
        )
        self.assertAlmostEqual(float(result["moment"].max()), 4.0, delta=0.01)

    def test_downward_udl_has_negative_hogging_moment_on_cantilever(self):
        result = analyze_beam(
            "Cantilever",
            4.0,
            distributed_loads=[{"intensity": -2.0, "start": 0.0, "end": 4.0}],
        )
        self.assertAlmostEqual(float(result["moment"].min()), -16.0, delta=0.02)


if __name__ == "__main__":
    unittest.main()
