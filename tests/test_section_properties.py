import unittest

import numpy as np

from section_properties import (
    rectangular_section, custom_section, calculate_beam_stresses, build_stress_steps,
)


class SectionPropertiesTests(unittest.TestCase):
    def test_rectangle_properties(self):
        section = rectangular_section(0.10, 0.20)
        self.assertAlmostEqual(section["area_m2"], 0.02)
        self.assertAlmostEqual(section["inertia_m4"], 0.10 * 0.20**3 / 12)
        self.assertAlmostEqual(section["c_m"], 0.10)

    def test_bending_and_rectangular_shear_stress(self):
        section = rectangular_section(0.10, 0.20)
        result = {
            "x": np.array([0.0, 1.0, 2.0]),
            "moment": np.array([0.0, 10.0, -5.0]),
            "shear": np.array([2.0, -4.0, 1.0]),
        }
        stresses = calculate_beam_stresses(result, section)
        expected_sigma = 10.0 * 0.10 / section["inertia_m4"] * 1000.0
        expected_tau = 1.5 * 4.0 / section["area_m2"] * 1000.0
        self.assertAlmostEqual(stresses["max_bending_stress_mpa"], expected_sigma)
        self.assertAlmostEqual(stresses["max_shear_stress_mpa"], expected_tau)
        self.assertIn("h^3", " ".join(build_stress_steps(section, stresses)))

    def test_custom_section_uses_average_shear(self):
        section = custom_section(0.02, 6.0e-5, 0.10)
        result = {"x": np.array([0.0, 1.0]), "moment": np.array([0.0, 5.0]),
                  "shear": np.array([0.0, 2.0])}
        stresses = calculate_beam_stresses(result, section)
        self.assertAlmostEqual(stresses["max_shear_stress_mpa"], 2.0 / 0.02 * 1000.0)
        self.assertIn("Average shear", stresses["shear_method"])

    def test_invalid_rectangle_is_rejected(self):
        with self.assertRaises(ValueError):
            rectangular_section(0.0, 0.2)


if __name__ == "__main__":
    unittest.main()
