import unittest
from agent_tools import normalise_activity, normalise_category

class AgentToolTests(unittest.TestCase):
    def test_normalises_activity(self):
        self.assertEqual(normalise_activity(" sports period "), "Sports period")
        self.assertEqual(normalise_activity("cricket"), "Sports period")
    def test_normalises_category(self):
        self.assertEqual(normalise_category(" Very poor "), "Very Poor")

if __name__ == "__main__": unittest.main()
