"""Post-analysis provenance check of shared-ASIN development matches only."""
from collections import defaultdict
import csv
import json

import pandas as pd

from agent_pipeline_common import read_json, rows, sha256, write_json
from evaluate_agent_pilot import DATA, OUT, RUN


def main():
    mapping=read_json(RUN.parents[1]/'bundle/id_mapping.json')
    with (OUT/'observed_matches_evaluation_only.csv').open(encoding='utf-8-sig') as f:
        selected=list(csv.DictReader(f))
    users={int(r['user_id']) for r in selected}
    cases={}
    for r in selected:
        if r['same_asin_source_history']=='1':
            uid=int(r['user_id']);item=int(r['item_id']);asin=mapping['tgt']['id2item'][item]
            cases[uid,asin]={'pair_id':r['pair_id'],'source_user_id':uid,'target_item_id':item,'asin':asin,
                             'source_reviews':[],'target_reviews':[]}
    source_path=DATA/'full/train_src_reviews.jsonl'
    target_path=DATA/'hidden_feedback/prompt_dev_reviews.jsonl'
    dev_records=[]
    for side,path in [('source_reviews',source_path),('target_reviews',target_path)]:
        for r in rows(path):
            if r['user_id'] not in users: continue
            domain='src' if side=='source_reviews' else 'tgt'
            assert r['raw_user_id']==mapping[domain]['id2user'][r['user_id']]
            assert r['raw_item_id']==mapping[domain]['id2item'][r['item_id']]
            key=r['user_id'],r['raw_item_id']
            if key in cases:cases[key][side].append(r)
            if side=='target_reviews':dev_records.append(r)
    hidden_path=DATA/'hidden_feedback/prompt_dev.pkl'
    df=pd.read_pickle(hidden_path)
    expected=set(map(tuple,df.loc[df['user'].isin(users),['user','item']].to_numpy(dtype=int)))
    actual={(r['user_id'],r['item_id']) for r in dev_records}
    assert expected==actual
    outputs=[]
    for case in cases.values():
        comparisons=[]
        for a in case['source_reviews']:
            for b in case['target_reviews']:
                comparisons.append({'same_raw_user':a['raw_user_id']==b['raw_user_id'],
                    'same_asin':a['raw_item_id']==b['raw_item_id'],
                    'same_time':a['unixReviewTime']==b['unixReviewTime'],
                    'same_rating':a['overall']==b['overall'],
                    'same_review_text':a.get('reviewText')==b.get('reviewText'),
                    'same_summary':a.get('summary')==b.get('summary'),
                    'source_record_id':a['record_id'],'target_record_id':b['record_id'],
                    'rating':a['overall']})
        outputs.append({k:v for k,v in case.items() if k not in ['source_reviews','target_reviews']}|
                       {'comparisons':comparisons})
    fields=['same_raw_user','same_asin','same_time','same_rating','same_review_text','same_summary']
    rating_by_pair={(r['user_id'],r['item_id']):r['overall'] for r in dev_records}
    matching=[r for r in selected if r['observed_hidden_interaction']=='1']
    result={'scope':'shared_ASIN_candidate_provenance;only_source_train_and_internal_prompt_dev',
            'analysis_status':'post_hoc_provenance_audit;not_preregistered_new_model_selection',
            'candidate_count':len(outputs),
            'identical_review_in_both_domains':sum(any(all(c[k] for k in fields) for c in r['comparisons']) for r in outputs),
            'independent_pkl_vs_review_join_verified':len(expected),
            'all_observed_matches':len(matching),
            'observed_matches_with_rating_at_least4':sum(rating_by_pair[int(r['user_id']),int(r['item_id'])]>=4 for r in matching),
            'matching_ratings':[{k:r[k] for k in ['pair_id','same_asin_source_history']}|
                               {'rating':rating_by_pair[int(r['user_id']),int(r['item_id'])]} for r in matching],
            'source_hashes':{str(p.relative_to(DATA)):sha256(p) for p in [source_path,target_path,hidden_path]},
            'cases':outputs}
    write_json(OUT/'duplicate_review_audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['cases','matching_ratings']},ensure_ascii=False),flush=True)


if __name__=='__main__':main()
