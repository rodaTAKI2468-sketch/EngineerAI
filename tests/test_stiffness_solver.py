import unittest
import numpy as np

from stiffness_solver import analyze_multiple_support_beam


class MultipleSupportStiffnessTests(unittest.TestCase):
    E = 200.0
    I = 1.0e-4

    def solve(self, length, supports, points=None, udls=None, moments=None):
        return analyze_multiple_support_beam(
            length, self.E, self.I, supports,
            points or [], udls or [], moments or [], max_element_length=0.1,
        )

    def test_simply_supported_central_point_load_benchmark(self):
        result = self.solve(
            4.0, [{"position": 0.0, "type": "Pin"}, {"position": 4.0, "type": "Roller"}],
            points=[{"position": 2.0, "magnitude": -20.0}],
        )
        self.assertAlmostEqual(result["support_reactions"][0]["vertical_kN"], 10.0, places=6)
        self.assertAlmostEqual(result["support_reactions"][1]["vertical_kN"], 10.0, places=6)
        exact_mm = 20_000.0 * 4.0**3 / (48.0 * (200e9) * self.I) * 1000.0
        self.assertAlmostEqual(result["max_deflection_mm"], exact_mm, delta=exact_mm*0.01)

    def test_fixed_fixed_full_span_udl_benchmark(self):
        result = self.solve(
            4.0, [{"position": 0.0, "type": "Fixed"}, {"position": 4.0, "type": "Fixed"}],
            udls=[{"start": 0.0, "end": 4.0, "intensity": -10.0}],
        )
        self.assertAlmostEqual(result["support_reactions"][0]["vertical_kN"], 20.0, delta=0.05)
        self.assertAlmostEqual(result["support_reactions"][1]["vertical_kN"], 20.0, delta=0.05)
        self.assertAlmostEqual(abs(result["support_reactions"][0]["moment_kNm"]), 13.333333, delta=0.08)
        self.assertAlmostEqual(abs(result["support_reactions"][1]["moment_kNm"]), 13.333333, delta=0.08)
        self.assertAlmostEqual(result["force_equilibrium_error_kN"], 0.0, places=6)
        self.assertAlmostEqual(result["moment_equilibrium_error_kNm"], 0.0, places=5)

    def test_three_support_continuous_beam(self):
        result = self.solve(
            8.0,
            [{"position": 0.0, "type": "Pin"},
             {"position": 4.0, "type": "Roller"},
             {"position": 8.0, "type": "Roller"}],
            udls=[{"start": 0.0, "end": 8.0, "intensity": -5.0}],
        )
        reactions = [r["vertical_kN"] for r in result["support_reactions"]]
        self.assertAlmostEqual(sum(reactions), 40.0, delta=0.05)
        self.assertAlmostEqual(result["force_equilibrium_error_kN"], 0.0, places=5)
        self.assertGreater(reactions[1], 0.0)

    def test_propped_cantilever_benchmark(self):
        result = self.solve(
            4.0, [{"position": 0.0, "type": "Fixed"}, {"position": 4.0, "type": "Roller"}],
            points=[{"position": 4.0, "magnitude": -10.0}],
        )
        reactions = result["support_reactions"]
        self.assertAlmostEqual(reactions[1]["vertical_kN"], 3.75, delta=0.03)
        self.assertAlmostEqual(reactions[0]["vertical_kN"], 6.25, delta=0.03)
        self.assertAlmostEqual(reactions[0]["moment_kNm"], 5.0, delta=0.04)

    def test_duplicate_support_positions_are_rejected(self):
        with self.assertRaises(ValueError):
            self.solve(4.0, [{"position": 1.0, "type": "Pin"},
                             {"position": 1.0, "type": "Roller"}])

    def test_unstable_structure_is_reported(self):
        with self.assertRaises(ValueError):
            self.solve(4.0, [{"position": 0.0, "type": "Pin"},
                             {"position": 4.0, "type": "Pin"}],
                       points=[{"position": 2.0, "magnitude": -1.0}]) if False else self.solve(
                           4.0, [{"position": 0.0, "type": "Pin"},
                                 {"position": 4.0, "type": "Pin"}],
                           points=[{"position": 2.0, "magnitude": -1.0}]
                       )


if __name__ == "__main__":
    unittest.main()
