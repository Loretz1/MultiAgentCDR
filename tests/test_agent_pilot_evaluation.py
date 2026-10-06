"""Check evaluation denominators and empty selections on known small examples."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluate_agent_pilot import selection_metrics, topk
from evaluate_agent_pilot import numerical_check
import math


class EvaluationMetricsTest(unittest.TestCase):
    def setUp(self):
        self.pool={(1,11),(1,12),(2,21),(2,22)}
        self.truth={(1,11),(1,13),(2,21),(2,23),(2,24)}

    def test_keeps_zero_selected_users_and_full_hidden_history(self):
        result=selection_metrics({(1,11)},self.pool,self.truth)
        self.assertEqual(result['users'],2)
        self.assertEqual(result['observed_match_rate'],1)
        self.assertEqual(result['candidate_hit_retention'],.5)
        self.assertEqual(result['hidden_history_recall_micro'],.2)
        self.assertEqual(result['hidden_history_recall_macro'],.25)
        self.assertEqual(result['user_hit_rate'],.5)

    def test_empty_selection_is_undefined_match_rate_and_zero_recall(self):
        result=selection_metrics(set(),self.pool,self.truth)
        self.assertIsNone(result['observed_match_rate'])
        self.assertEqual(result['candidate_hit_retention'],0)
        self.assertEqual(result['hidden_history_recall_micro'],0)
        self.assertEqual(result['user_hit_rate'],0)

    def test_fixed_budget_and_ties_are_per_user(self):
        records=[{'source_user_id':1,'target_item_id':12,'score':2},
                 {'source_user_id':1,'target_item_id':11,'score':2},
                 {'source_user_id':2,'target_item_id':21,'score':-2},
                 {'source_user_id':2,'target_item_id':22,'score':1}]
        self.assertEqual(topk(records,lambda r:r['score'],1),[(1,11),(2,22)])

    def test_equal_label_scores_follow_original_collector_order(self):
        scores={k:math.log(1/3) for k in ['C','B','A']}
        agent={'label_logprobs':scores,'label_probabilities':{k:1/3 for k in scores},
               'confidence':0,'prediction':'A','label_mass':1}
        numerical_check({'example':{'agents':{'semantic':agent}}})


if __name__=='__main__':unittest.main()
