import unittest
from datetime import date, datetime
from forecast import find_safest_two_hour_window, is_in_window
def hour(value, aqi): return {"time": value, "aqi": aqi, "category": "Moderate"}
class ForecastTests(unittest.TestCase):
    def test_school_hours_and_future_only(self):
        result = find_safest_two_hour_window([hour("2026-10-10T06:00",1),hour("2026-10-10T07:00",1),hour("2026-10-10T08:00",80),hour("2026-10-10T09:00",70)], date(2026,10,10), datetime(2026,10,10,7,15))
        self.assertEqual(result["start"], "2026-10-10T08:00:00")
    def test_none_and_nonconsecutive_ignored(self):
        self.assertIsNone(find_safest_two_hour_window([hour("2026-10-11T07:00",None),hour("2026-10-11T08:00",5),hour("2026-10-11T10:00",5)], date(2026,10,11), datetime(2026,10,10)))
    def test_end_is_consistent(self):
        result = find_safest_two_hour_window([hour("2026-10-11T07:00",20),hour("2026-10-11T08:00",30)], date(2026,10,11), datetime(2026,10,10))
        self.assertEqual(result["end"], "2026-10-11T09:00:00")
    def test_datetime_window_highlight(self):
        window={"start":"2026-10-11T07:00:00","end":"2026-10-11T09:00:00"}
        self.assertTrue(is_in_window("2026-10-11T08:00",window))
        self.assertFalse(is_in_window("2026-10-11T09:00",window))
if __name__ == "__main__": unittest.main()
