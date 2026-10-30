import json
import unittest
from unittest.mock import patch
from app import recommendations, entities_from, seeds_from, QlooError, _score


def entity(uid, name, subtype="urn:entity:movie"):
    return {"entity_id": uid, "name": name, "subtype": subtype}


FIRST = "11111111-1111-1111-1111-111111111111"
SECOND = "22222222-2222-2222-2222-222222222222"
THIRD = "33333333-3333-3333-3333-333333333333"


class TestQlooAgent(unittest.TestCase):
    def test_invalid_category(self):
        with self.assertRaises(ValueError):
            recommendations("Black Panther", "invalid")

    def test_empty_interest(self):
        with self.assertRaises(ValueError):
            recommendations("", "music")

    def test_more_than_three_seeds(self):
        with self.assertRaises(ValueError):
            seeds_from("a,b,c,d")

    def test_no_key(self):
        with patch.dict("os.environ", {"QLOO_API_KEY": ""}):
            self.assertEqual(recommendations("Jazz", "music")["status"], "needs_api_key")

    def test_key_never_fabricates_results(self):
        with patch.dict("os.environ", {"QLOO_API_KEY": "test"}):
            with patch("app.qloo_get", return_value={"results": {"entities": []}}):
                output = recommendations("Unknown", "movies")
        self.assertEqual(output["status"], "interest_not_found")
        self.assertEqual(output["results"], [])

    def test_single_seed_live_workflow_mocked(self):
        seed = entity(FIRST, "Black Panther")
        pick = entity(SECOND, "Arrival")
        pick.update({"properties": {"description": "A sci-fi story"},
                     "query": {"affinity": 0.76}, "tags": [
                         {"name": "Science Fiction", "type": "urn:tag:genre:media"}]})
        with patch.dict("os.environ", {"QLOO_API_KEY": "dummy"}):
            with patch("app.qloo_get", side_effect=[
                {"results": {"entities": [seed]}},
                {"results": {"entities": [pick]}}
            ]) as remote:
                output = recommendations("Black Panther", "movies")
        self.assertEqual(output["status"], "ok")
        self.assertEqual(output["results"][0]["name"], "Arrival")
        self.assertEqual(output["results"][0]["affinity"], 0.76)
        self.assertEqual(len(output["steps"]), 2)
        self.assertEqual(remote.call_args_list[1].args[1]["signal.interests.entities"], FIRST)

    def test_cross_category_three_insight_calls(self):
        seed = entity(FIRST, "Interstellar")
        film = entity(SECOND, "Arrival")
        artist = entity(THIRD, "Artist X", "urn:entity:artist")
        with patch.dict("os.environ", {"QLOO_API_KEY": "dummy"}):
            with patch("app.qloo_get", side_effect=[
                {"results": {"entities": [seed]}},
                {"results": {"entities": []}},
                {"results": {"entities": [artist]}},
                {"results": {"entities": [film]}}
            ]) as remote:
                output = recommendations("Interstellar", "all")
        self.assertEqual(output["status"], "ok")
        self.assertEqual(len(output["results"]), 2)
        self.assertEqual(remote.call_count, 4)

    def test_seed_match_prefers_exact_name(self):
        seed = entity(FIRST, "Movie")
        other = entity(SECOND, "movie sequel")
        with patch.dict("os.environ", {"QLOO_API_KEY": "dummy"}):
            with patch("app.qloo_get", side_effect=[
                {"results": {"entities": [other, seed]}},
                {"results": {"entities": []}}
            ]) as remote:
                output = recommendations("MOVIE", "movies")
        self.assertEqual(output["resolved_interests"][0]["entity_id"], FIRST)
        self.assertEqual(output["status"], "no_results")

    def test_reject_bad_json_entity_shape(self):
        with self.assertRaises(QlooError):
            entities_from({"results": {"entities": "bad"}})

    def test_support_results_list(self):
        self.assertEqual(len(entities_from({"results": [entity(FIRST, "Movie")]})), 1)

    def test_affinity_is_not_a_probability(self):
        self.assertEqual(_score({"query": {"affinity": 0.5}}), 0.5)
        self.assertIsNone(_score({"query": {"affinity": 1.7}}))

    def test_location_validation(self):
        with self.assertRaises(ValueError):
            recommendations("Black Panther", "movies", "x" * 81)

    def test_qloo_key_not_leaked_in_no_result_payload(self):
        with patch.dict("os.environ", {"QLOO_API_KEY": "super-secret-test"}):
            with patch("app.qloo_get", return_value={"results": {"entities": []}}):
                output = recommendations("Unknown", "music")
        self.assertNotIn("super-secret-test", json.dumps(output))


if __name__ == "__main__":
    unittest.main()
