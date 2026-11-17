import unittest

from support_config import classify_supports, analyze_support_configuration


class SupportConfigurationTests(unittest.TestCase):
    def test_pin_pin_is_determinate_for_transverse_beam_model(self):
        self.assertEqual(classify_supports("Pin", "Pin")["status"], "determinate")

    def test_pin_roller_is_determinate(self):
        self.assertEqual(classify_supports("Pin", "Roller")["status"], "determinate")

    def test_fixed_free_and_free_fixed_are_determinate(self):
        self.assertEqual(classify_supports("Fixed", "Free")["status"], "determinate")
        self.assertEqual(classify_supports("Free", "Fixed")["status"], "determinate")

    def test_free_pin_is_unstable(self):
        self.assertEqual(classify_supports("Free", "Pin")["status"], "unstable")

    def test_free_free_is_unstable(self):
        self.assertEqual(classify_supports("Free", "Free")["status"], "unstable")

    def test_fixed_pin_requires_stiffness_analysis(self):
        self.assertEqual(classify_supports("Fixed", "Pin")["status"], "indeterminate")

    def test_fixed_fixed_requires_stiffness_analysis(self):
        self.assertEqual(classify_supports("Fixed", "Fixed")["status"], "indeterminate")

    def test_pin_pin_reactions_and_diagrams(self):
        result = analyze_support_configuration(
            "Pin", "Pin", 6.0,
            point_loads=[{"magnitude": -12.0, "position": 3.0}],
        )
        self.assertAlmostEqual(result["reaction_a_kN"], 6.0)
        self.assertAlmostEqual(result["reaction_b_kN"], 6.0)
        self.assertAlmostEqual(float(result["moment"].max()), 18.0, delta=0.05)

    def test_free_fixed_reactions_and_hogging_moment(self):
        result = analyze_support_configuration(
            "Free", "Fixed", 4.0,
            point_loads=[{"magnitude": -10.0, "position": 0.0}],
        )
        self.assertAlmostEqual(result["reaction_b_kN"], 10.0)
        self.assertAlmostEqual(result["fixed_moment_b_kNm"], 40.0)
        self.assertAlmostEqual(float(result["moment"].min()), -40.0, delta=0.1)

    def test_indeterminate_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_support_configuration("Fixed", "Pin", 5.0)


if __name__ == "__main__":
    unittest.main()
