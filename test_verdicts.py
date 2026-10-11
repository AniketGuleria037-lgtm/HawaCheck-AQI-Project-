import unittest
from verdicts import ACTIVITY_RULES, AQI_LEVELS, get_activity_verdict
class VerdictTests(unittest.TestCase):
    def test_every_activity_and_category(self):
        for activity, rules in ACTIVITY_RULES.items():
            for category, level in AQI_LEVELS.items():
                expected = "Move indoors" if level >= rules["indoors_at"] else "Modify" if level >= rules["modify_at"] else "Go ahead"
                self.assertEqual(get_activity_verdict(category, activity)["verdict"], expected)
                self.assertEqual(get_activity_verdict(category, activity, True)["verdict"], {"Go ahead":"Modify", "Modify":"Move indoors", "Move indoors":"Move indoors"}[expected])
if __name__ == "__main__": unittest.main()
