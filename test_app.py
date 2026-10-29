import unittest
from unittest.mock import patch

from app import recommendations, entities_from, QlooError


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

    def test_live_workflow_is_mocked_without_network(self):
        seed = {"entity_id": "11111111-1111-1111-1111-111111111111", "name": "Jazz"}
        pick = {"entity_id": "22222222-2222-2222-2222-222222222222",
                "name": "Artist B", "subtype": "urn:entity:artist",
                "properties": {"description": "A musician"}}
        with patch.dict("os.environ", {"QLOO_API_KEY": "dummy"}):
            with patch("app.qloo_get", side_effect=[
                {"results": {"entities": [seed]}}, {"results": {"entities": [pick]}}
            ]) as mocked:
                response = recommendations("Jazz", "music")
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["results"][0]["name"], "Artist B")
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(mocked.call_args_list[1].args[1]["signal.interests.entities"], seed["entity_id"])

    def test_no_match(self):
        with patch.dict("os.environ", {"QLOO_API_KEY": "dummy"}):
            with patch("app.qloo_get", return_value={"results": {"entities": []}}):
                self.assertEqual(recommendations("Unknown", "movies")["status"], "interest_not_found")

    def test_invalid_payload(self):
        with self.assertRaises(QlooError):
            entities_from({"results": {"entities": "invalid"}})


if __name__ == "__main__":
    unittest.main()
