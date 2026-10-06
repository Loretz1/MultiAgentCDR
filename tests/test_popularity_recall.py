from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_popularity_recall import visible_counts,global_top,summarize


class PopularityRecallTests(unittest.TestCase):
    def test_repeated_events_and_independent_users_are_different_statistics(self):
        events,users=visible_counts(np.array([[1,1],[1,1],[1,1],[2,2],[3,2]]),3)
        self.assertEqual(events.tolist(),[0,3,2,0])
        self.assertEqual(users.tolist(),[0,1,2,0])
        self.assertEqual(global_top(events,1),[1])
        self.assertEqual(global_top(users,1),[2])

    def test_ties_and_ineligible_zero_ID_and_invalid_ids(self):
        self.assertEqual(global_top(np.array([999,5,5,2]),2),[1,2])
        with self.assertRaises(ValueError):visible_counts(np.array([[1,0]]),3)
        with self.assertRaises(ValueError):visible_counts(np.array([[1,4]]),3)
        with self.assertRaises(ValueError):global_top(np.array([0,1,2]),3)

    def test_shared_candidates_still_have_user_specific_hits_and_asin_strata(self):
        result=summarize({1:{10,20},2:{10,20}}, {1:{10,30},2:{40}}, {1:{10},2:set()})
        self.assertEqual(result['candidates'],4)
        self.assertEqual(result['observed_hits'],1)
        self.assertEqual(result['observed_match_rate'],.25)
        self.assertAlmostEqual(result['recall_micro'],1/3)
        self.assertEqual(result['users_with_hit'],1)
        self.assertEqual(result['same_asin_hits'],1)
        self.assertEqual(result['different_asin_hidden_interactions'],2)
        self.assertEqual(result['different_asin_hits'],0)
        self.assertEqual(result['per_user'][1]['observed_hits'],0)


if __name__=='__main__':unittest.main()
