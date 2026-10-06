"""Recall diagnostics: denominators, exclusion, RRF and missing profiles."""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_candidate_recall import candidate_ids, fuse, ranked_ids, summarize, source_asin_item_sets


class RecallDiagnosticsTest(unittest.TestCase):
    def test_recall_uses_full_histories_and_keeps_zero_hit_users(self):
        r=summarize({1:{11,12},2:{21}}, {1:{11,13},2:{22,23}}, {1:{11},2:set()})
        self.assertEqual(r['observed_hits'],1)
        self.assertEqual(r['recall_micro'],.25)
        self.assertEqual(r['recall_macro'],.25)
        self.assertEqual(r['users_with_hit'],1)
        self.assertEqual(r['different_asin_hidden_interactions'],3)
        self.assertEqual(r['different_asin_recall_micro'],0)
        self.assertEqual(len(r['per_user']),2)

    def test_no_novel_truth_and_empty_recall_are_undefined_where_needed(self):
        r=summarize({1:set()},{1:{11}},{1:{11}})
        self.assertIsNone(r['observed_match_rate'])
        self.assertIsNone(r['different_asin_recall_micro'])
        self.assertIsNone(r['different_asin_recall_macro'])
        self.assertEqual(r['recall_micro'],0)

    def test_rrf_favors_agreement_and_breaks_ties_by_item_id(self):
        self.assertEqual(fuse([3,2],[3,1]),[3,1,2])
        r={'semantic':[3,2], 'g':[3,1], 'rrf':[3,1,2]}
        self.assertEqual(candidate_ids(r,'rrf',2),{3,1})
        self.assertEqual(candidate_ids(r,'union',2),{1,2,3})

    def test_exclusion_before_topk_refills_budget_and_empty_profile_stays_empty(self):
        scores=np.asarray([0,9,8,7],dtype=np.float32)
        self.assertEqual(ranked_ids(scores,np.asarray([2,3]),2),[2,3])
        self.assertEqual(ranked_ids(scores,np.asarray([],dtype=int),2),[])

    def test_asin_mapping_uses_domain_maps_and_current_users_only(self):
        mapping={'src':{'id2item':[None,'X','Y']},'tgt':{'item2id':{'X':7,'Z':8}}}
        seen=source_asin_item_sets(np.asarray([[1,1],[1,2],[2,1]]),mapping,[1])
        self.assertEqual(seen,{1:{7}})


if __name__ == '__main__':unittest.main()
