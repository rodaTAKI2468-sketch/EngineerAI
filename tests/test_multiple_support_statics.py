import unittest

from multiple_support_statics import analyze_determinate_multiple_support_beam


class MultipleSupportStaticsTests(unittest.TestCase):
    def test_central_point_load_on_two_supports(self):
        result = analyze_determinate_multiple_support_beam(
            4.0,
            [{"position": 0.0, "type": "Pin"}, {"position": 4.0, "type": "Roller"}],
            [{"position": 2.0, "magnitude": -20.0}],
        )
        self.assertAlmostEqual(result["support_reactions"][0]["vertical_kN"], 10.0)
        self.assertAlmostEqual(result["support_reactions"][1]["vertical_kN"], 10.0)
        self.assertAlmostEqual(result["force_equilibrium_error_kN"], 0.0)
        self.assertAlmostEqual(result["moment_equilibrium_error_kNm"], 0.0)

    def test_full_span_udl(self):
        result = analyze_determinate_multiple_support_beam(
            6.0,
            [{"position": 0.0, "type": "Pin"}, {"position": 6.0, "type": "Roller"}],
            distributed_loads=[{"start": 0.0, "end": 6.0, "intensity": -4.0}],
        )
        self.assertAlmostEqual(result["support_reactions"][0]["vertical_kN"], 12.0)
        self.assertAlmostEqual(result["support_reactions"][1]["vertical_kN"], 12.0)
        self.assertAlmostEqual(result["force_equilibrium_error_kN"], 0.0)
        self.assertAlmostEqual(result["moment_equilibrium_error_kNm"], 0.0)

    def test_off_centre_point_load(self):
        result = analyze_determinate_multiple_support_beam(
            5.0,
            [{"position": 0.0, "type": "Pin"}, {"position": 5.0, "type": "Roller"}],
            [{"position": 2.0, "magnitude": -15.0}],
        )
        self.assertAlmostEqual(result["support_reactions"][0]["vertical_kN"], 9.0)
        self.assertAlmostEqual(result["support_reactions"][1]["vertical_kN"], 6.0)

    def test_three_supports_are_rejected_as_indeterminate(self):
        with self.assertRaisesRegex(ValueError, "statically indeterminate"):
            analyze_determinate_multiple_support_beam(
                8.0,
                [{"position": 0.0, "type": "Pin"},
                 {"position": 4.0, "type": "Roller"},
                 {"position": 8.0, "type": "Roller"}],
            )

    def test_fixed_support_is_rejected_in_statics_mode(self):
        with self.assertRaisesRegex(ValueError, "Fixed support"):
            analyze_determinate_multiple_support_beam(
                4.0,
                [{"position": 0.0, "type": "Fixed"}, {"position": 4.0, "type": "Roller"}],
            )


if __name__ == "__main__":
    unittest.main()
