import unittest
from unittest.mock import patch
from app import recommendations

class TestRecommendations(unittest.TestCase):
    def test_invalid_category(self):
        with self.assertRaises(ValueError):
            recommendations("jazz", "invalid")
    def test_empty_interest(self):
        with self.assertRaises(ValueError):
            recommendations("", "music")
    def test_no_key(self):
        with patch.dict("os.environ", {"QLOO_API_KEY": ""}):
            self.assertEqual(recommendations("jazz", "music")["status"], "needs_api_key")
    def test_key_does_not_fake_results(self):
        with patch.dict("os.environ", {"QLOO_API_KEY": "test"}):
            self.assertEqual(recommendations("jazz", "music")["status"], "needs_entity_resolution")

if __name__ == "__main__":
    unittest.main()
