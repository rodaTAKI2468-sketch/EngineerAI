import unittest

import numpy as np

from calculations import calculate_deflection


class DeflectionCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.e_pa = 200e9
        self.i_m4 = 1e-4

    def test_off_centre_point_load_is_not_silently_ignored(self):
        x = np.linspace(0.0, 4.0, 801)
        y = calculate_deflection(
            x,
            4.0,
            load=-20.0,
            position=1.0,
            E=self.e_pa,
            I=self.i_m4,
            beam_type="S",
        )
        self.assertAlmostEqual(float(y[0]), 0.0, places=10)
        self.assertAlmostEqual(float(y[-1]), 0.0, places=10)
        self.assertGreater(float(np.max(y)), 0.0)

    def test_multiple_point_loads_are_included(self):
        x = np.linspace(0.0, 5.0, 1001)
        y_two_loads = calculate_deflection(
            x,
            5.0,
            loads=[-10.0, -20.0],
            positions=[1.0, 4.0],
            E=self.e_pa,
            I=self.i_m4,
            beam_type="S",
        )
        y_one_load = calculate_deflection(
            x,
            5.0,
            load=-10.0,
            position=1.0,
            E=self.e_pa,
            I=self.i_m4,
            beam_type="S",
        )
        self.assertAlmostEqual(float(y_two_loads[0]), 0.0, places=10)
        self.assertAlmostEqual(float(y_two_loads[-1]), 0.0, places=10)
        self.assertGreater(float(np.max(y_two_loads)), float(np.max(y_one_load)))

    def test_cantilever_with_off_centre_load_deflects_after_the_load(self):
        x = np.linspace(0.0, 4.0, 801)
        y = calculate_deflection(
            x,
            4.0,
            load=-10.0,
            position=1.5,
            E=self.e_pa,
            I=self.i_m4,
            beam_type="C",
        )
        self.assertAlmostEqual(float(y[0]), 0.0, places=10)
        self.assertGreater(float(y[-1]), 0.0)


if __name__ == "__main__":
    unittest.main()
