import unittest
from aqi import PM10_BREAKPOINTS, PM25_BREAKPOINTS, calculate_aqi, calculate_sub_index

class AQITests(unittest.TestCase):
    def test_former_gap_has_aqi(self): self.assertIsNotNone(calculate_aqi(pm25=30.5)["aqi"])
    def test_each_boundary_above_is_supported(self):
        for points in (PM25_BREAKPOINTS, PM10_BREAKPOINTS):
            for _, high, _, _ in points[:-1]: self.assertIsNotNone(calculate_sub_index(high + .1, points))
    def test_values_above_maximum_cap(self):
        self.assertEqual(calculate_sub_index(999, PM25_BREAKPOINTS), 500); self.assertEqual(calculate_sub_index(999, PM10_BREAKPOINTS), 500)
    def test_mixed_former_gap(self):
        result = calculate_aqi(pm25=30.5, pm10=50)
        self.assertEqual(result["aqi"], max(result["pm25_sub_index"], result["pm10_sub_index"]))
if __name__ == "__main__": unittest.main()
