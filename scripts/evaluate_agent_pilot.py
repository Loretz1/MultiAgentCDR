"""Frozen-pilot development diagnostics; observed matches are not preference truth.

Prepare reads visible inputs/outputs only. Evaluate additionally reads only the
internal prompt_dev feedback. No vLLM call, retraining, or prompt modification.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from agent_pipeline_common import ROOT, read_json, rows, sha256, utc_now, write_json
from collect_agent_feedback import ROLES

RUN = ROOT / 'doc/experiments/2026-10-06_featurize_real/artifacts/MultiAgentCDR/runs/pilot_v1'
DATA = ROOT / 'CDRec/data/agent_evidence/cloth_to_sports/v2'
OUT = ROOT / 'doc/experiments/2026-10-06_agent_evaluation'
REVIEW_USERS = [42, 1365, 1773, 1991, 2174]


def read_pilot():
    inputs = list(rows(RUN / 'inputs_prompt_dev/agent_inputs.jsonl'))
    outputs = list(rows(RUN / 'feedback_v5.jsonl'))
    assert len(inputs) == len(outputs) == 200
    ids = {r['pair_id']: r for r in inputs}
    feedback = {r['pair_id']: r for r in outputs}
    assert len(ids) == len(feedback) == 200 and set(ids) == set(feedback)
    assert len({r['source_user_id'] for r in inputs}) == 20
    groups = read_json(DATA / 'folds/prompt/users.json')
    assert {r['source_user_id'] for r in inputs} <= set(groups['prompt_dev'])
    for r in inputs:
        a = feedback[r['pair_id']]
        assert a['source_user_id'] == r['source_user_id']
        assert a['target_item_id'] == r['target_item_id']
        assert a['prompt_version'] == 'four_evidence_v5_short_reason'
        assert set(a['agents']) == set(ROLES)
        assert not r['provenance'].get('hidden_feedback_read', False)
    return inputs, feedback


def request():
    return {'input_sha256': sha256(RUN/'inputs_prompt_dev/agent_inputs.jsonl'),
            'feedback_sha256': sha256(RUN/'feedback_v5.jsonl'),
            'script_sha256': sha256(Path(__file__)), 'review_users': REVIEW_USERS,
            'group': 'prompt_dev', 'source_version': 'v2',
            'feedback_read_policy': 'internal_prompt_dev_only;prompt_val_and_formal_evaluation_unread',
            'purpose': 'exploratory_development_diagnostics;not_final_accuracy_or_recommendation_performance',
            'review_type': 'AI_assistant_evidence_review;not_independent_human_gold_labels',
            'sampling': 'purposive_five_users_frozen_before_target_match_computation',
            'ranking': 'score_desc_then_target_item_id_asc', 'top_k': 5,
            'label_argmax_tie_break': 'A_then_B_then_C;matches_original_collector',
            'descriptive_label_groups': ['A','B','C','A_or_B'],
            'selection_rules': ['A_only', 'A_or_B', 'pA_top5_per_user', 'pA_minus_pC_top5_per_user',
                                'g_top5_per_user', 'semantic_top5_per_user',
                                'multi_role_A_count_at_least2', 'multi_role_AB_count_at_least3',
                                'all_four_nonC', 'all_four_A'],
            'nonmatch_meaning': 'not_observed_in_hidden_target_history;not_dislike_or_ABC_C_gold'}


def compact(r, role):
    e = r['evidence'][role]
    keys = {'semantic': ['similarity', 'rank', 'ranking_items', 'matched_total', 'matched_concepts',
                         'unmatched_total', 'positive_history_items', 'related_positive_history'],
            'collaborative': ['g_raw', 'rank', 'ranking_items', 'rank_percentile',
                              'source_history_length', 'candidate_visible_train_users'],
            'overlap': ['actual_neighbors', 'direct_support_users', 'indirect_support_users',
                        'union_support_users', 'union_support_rate'],
            'popularity_bias': ['distinct_train_users', 'popularity_percentile', 'global_support_rate',
                                'local_support_users', 'local_group_size', 'local_support_rate',
                                'relative_support', 'exposure_available']}[role]
    return {k: e[k] for k in keys}


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs, feedback = read_pilot()
    selection = [r for r in inputs if r['source_user_id'] in REVIEW_USERS]
    assert len(selection) == 50
    req = request()
    existing = OUT / 'evaluation_request.json'
    if existing.exists():
        assert read_json(existing) == req, 'Frozen evaluation configuration changed'
    write_json(existing, req)
    write_json(OUT/'review_selection.json', {'users': REVIEW_USERS,
               'pair_ids': [r['pair_id'] for r in selection], 'selection_uses_hidden_feedback': False,
               'reason': 'diagnostic coverage: dense overlap, generic semantic match, weak/local support and low popularity'})
    with (OUT/'review_inputs.jsonl').open('w', encoding='utf-8') as f:
        for r in selection:
            f.write(json.dumps({'input': r, 'output': feedback[r['pair_id']]}, ensure_ascii=False)+'\n')
    with (OUT/'review_compact.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['pair_id','user_id','item_id','role','evidence',
                                              'prediction','reasoning','confidence'])
        writer.writeheader()
        for r in selection:
            for role in ROLES:
                a = feedback[r['pair_id']]['agents'][role]
                writer.writerow({'pair_id':r['pair_id'], 'user_id':r['source_user_id'],
                                 'item_id':r['target_item_id'],'role':role,
                                 'evidence':json.dumps(compact(r,role),ensure_ascii=False),
                                 **{k:a[k] for k in ['prediction','reasoning','confidence']}})
    write_json(OUT/'status.json', {'state':'prepared_before_target_matching', 'prepared_at':utc_now(),
                                  'cases':50, 'role_reviews':200})
    print('Prepared 50 cases / 200 role records without target labels', flush=True)


def wilson(hits, n):
    if not n:
        return None
    z = 1.959963984540054
    p = hits / n
    denom = 1 + z*z/n
    centre = (p + z*z/(2*n)) / denom
    margin = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return [max(0,centre-margin), min(1,centre+margin)]


def selection_metrics(selected, candidates, truth):
    """Return fixed-candidate observed matches, retaining zero-selected users."""
    selected, candidates = set(selected), set(candidates)
    assert selected <= candidates
    selected_hits = selected & truth
    candidate_hits = candidates & truth
    users = sorted({u for u,i in candidates})
    positive_users = {u for u,i in truth}
    assert set(users) <= positive_users
    per_user=[]
    for u in users:
        chosen={i for uid,i in selected if uid==u}
        positives={i for uid,i in truth if uid==u}
        hit=len(chosen&positives)
        pool={i for uid,i in candidates if uid==u}
        per_user.append({'user_id':u,'selected':len(chosen),'observed_hits':hit,
                         'total_hidden_interactions':len(positives),
                         'candidate_observed_hits':len(pool&positives),
                         'candidate_hit_retention':hit/len(pool&positives) if pool&positives else None,
                         'hidden_history_recall':hit/len(positives), 'has_hit':int(hit>0)})
    n = len(selected)
    return {'selected':n, 'observed_hits':len(selected_hits),
            'observed_match_rate':len(selected_hits)/n if n else None,
            'wilson95_descriptive_only_ignores_user_clustering':wilson(len(selected_hits),n),
            'candidate_hit_retention':len(selected_hits)/len(candidate_hits) if candidate_hits else None,
            'hidden_history_recall_micro':len(selected_hits)/len(truth) if truth else None,
            'hidden_history_recall_macro':float(np.mean([p['hidden_history_recall'] for p in per_user])),
            'users_with_selection':len({u for u,i in selected}),
            'users_with_hit':sum(p['has_hit'] for p in per_user),
            'user_hit_rate':sum(p['has_hit'] for p in per_user)/len(users), 'users':len(users),
            'per_user':per_user}


def topk(inputs, value, k=5):
    per_user=defaultdict(list)
    for r in inputs: per_user[r['source_user_id']].append(r)
    selected=[]
    for user, items in sorted(per_user.items()):
        ranked=sorted(items,key=lambda r:(-float(value(r)),r['target_item_id']))
        selected.extend((user,r['target_item_id']) for r in ranked[:k])
    return selected


def numerical_check(feedback):
    for r in feedback.values():
        for a in r['agents'].values():
            scores=a['label_logprobs']
            m=max(scores.values());w={k:math.exp(v-m) for k,v in scores.items()}
            p={k:v/sum(w.values()) for k,v in w.items()}
            assert set(p)=={'A','B','C'}
            for label in p: assert math.isclose(p[label],a['label_probabilities'][label],abs_tol=1e-12)
            conf=1+sum(v*math.log(v) for v in p.values() if v)/math.log(3)
            assert math.isclose(conf,a['confidence'],abs_tol=1e-12)
            assert a['prediction']==max(('A','B','C'),key=p.get)
            assert math.isclose(sum(math.exp(v) for v in scores.values()),a['label_mass'],abs_tol=1e-12)


def evaluate():
    assert read_json(OUT/'evaluation_request.json')==request()
    inputs, feedback = read_pilot()
    numerical_check(feedback)
    # Read only the declared development feedback; no directory traversal of labels.
    hidden_path=DATA/'hidden_feedback/prompt_dev.pkl'
    hidden=pd.read_pickle(hidden_path)
    assert list(hidden.columns)==['user','item']
    users={r['source_user_id'] for r in inputs}
    mapping_path=RUN.parents[1]/'bundle/id_mapping.json'
    mapping=read_json(mapping_path)
    for uid in users: assert mapping['src']['id2user'][uid]==mapping['tgt']['id2user'][uid]
    hidden=hidden.loc[hidden['user'].isin(users),['user','item']].drop_duplicates()
    truth=set(map(tuple,hidden.to_numpy(dtype=int)))
    candidates={(r['source_user_id'],r['target_item_id']) for r in inputs}
    assert len(candidates)==200 and {u for u,i in truth}==users
    def pair(r): return r['source_user_id'],r['target_item_id']
    def agent(r, role): return feedback[r['pair_id']]['agents'][role]
    selections={'all_candidates':candidates}
    for role in ROLES:
        for labels,name in [({'A'},'A_only'),({'A','B'},'A_or_B'),({'B'},'B_only'),({'C'},'C_only')]:
            selections[role+'_'+name]={pair(r) for r in inputs if agent(r,role)['prediction'] in labels}
        selections[role+'_pA_top5']=topk(inputs,lambda r:agent(r,role)['label_probabilities']['A'])
        selections[role+'_pA_minus_pC_top5']=topk(inputs,lambda r:agent(r,role)['label_probabilities']['A']-agent(r,role)['label_probabilities']['C'])
    selections['g_top5']=topk(inputs,lambda r:r['evidence']['collaborative']['g_raw'])
    selections['semantic_top5']=topk(inputs,lambda r:r['evidence']['semantic']['similarity'])
    selections['multi_A_at_least2']={pair(r) for r in inputs if sum(agent(r,k)['prediction']=='A' for k in ROLES)>=2}
    selections['multi_AB_at_least3']={pair(r) for r in inputs if sum(agent(r,k)['prediction']!='C' for k in ROLES)>=3}
    selections['all_four_nonC']={pair(r) for r in inputs if all(agent(r,k)['prediction']!='C' for k in ROLES)}
    selections['all_four_A']={pair(r) for r in inputs if all(agent(r,k)['prediction']=='A' for k in ROLES)}
    selections={name:set(chosen) for name,chosen in selections.items()}
    scores={name:selection_metrics(s,candidates,truth) for name,s in selections.items()}
    same_asin=set()
    # Original source-side training only, read here to stratify known cross-domain ASIN overlap.
    # Candidate provenance audit uses the portable source interaction bundle, reconstructed
    # from the original visible source training table to avoid profile-schema assumptions.
    benchmark=Path(read_json(DATA/'manifest.json')['benchmark_directory'])
    source_path=benchmark/'train_src.pkl'
    source=pd.read_pickle(source_path)
    seen=defaultdict(set)
    for uid,item in source.loc[source['user'].isin(users),['user','item']].itertuples(index=False,name=None):
        seen[int(uid)].add(mapping['src']['id2item'][int(item)])
    for r in inputs:
        if mapping['tgt']['id2item'][r['target_item_id']] in seen[r['source_user_id']]:same_asin.add(pair(r))
    strat={}
    for name,pool in [('same_asin',same_asin),('different_asin',candidates-same_asin)]:
        strat[name]={'candidate_count':len(pool),'observed_hits':len(pool&truth),
                     'observed_match_rate':len(pool&truth)/len(pool) if pool else None,
                     'rules':{rule:{'selected':len(chosen&pool),'observed_hits':len(chosen&pool&truth),
                               'observed_match_rate':len(chosen&pool&truth)/len(chosen&pool) if chosen&pool else None}
                              for rule,chosen in selections.items()}}
    subsets={}
    for name,subset_users in [('review_5_users',set(REVIEW_USERS)),('remaining_15_users',users-set(REVIEW_USERS))]:
        pool={p for p in candidates if p[0] in subset_users}
        positives={p for p in truth if p[0] in subset_users}
        subsets[name]={rule:selection_metrics({p for p in chosen if p[0] in subset_users},pool,positives)
                       for rule,chosen in selections.items()}
    request_files={'hidden_prompt_dev':hidden_path,'mapping':mapping_path,'visible_source_train':source_path}
    result={'state':'complete','evaluated_at':utc_now(),'scope':'20_prompt_dev_users;200_candidates',
            'users':len(users),'candidates':len(candidates),'total_hidden_interactions':len(truth),
            'candidate_observed_hits':len(candidates&truth),'candidate_recall_ceiling':len(candidates&truth)/len(truth),
            'numerical_checks':800,
            'exact_argmax_ties':{role:sum(sum(v==max(a['label_probabilities'].values()) for v in a['label_probabilities'].values())>1
                                  for a in [r['agents'][role] for r in feedback.values()]) for role in ROLES},
            'metrics':scores,'same_asin_strata':strat,'subsets':subsets,
            'label_sources':{k:{'path':str(p.relative_to(ROOT)),'sha256':sha256(p)} for k,p in request_files.items()},
            'formal_validation_test_read':False,'internal_prompt_val_read':False,
            'nonmatches_are_negative_preferences':False,'human_gold_accuracy_evaluated':False,
            'ranking_metrics_are_full_catalog':False,'selection_rules_are_exploratory':True,
            'missing_reasoning_flags_are_not_proof_of_correctness':True}
    write_json(OUT/'evaluation_results.json',result)
    label_rows=[]
    for r in inputs:
        item={'pair_id':r['pair_id'],'user_id':r['source_user_id'],'item_id':r['target_item_id'],
              'observed_hidden_interaction':int(pair(r) in truth),'same_asin_source_history':int(pair(r) in same_asin),
              'review_sample':int(r['source_user_id'] in REVIEW_USERS)}
        for role in ROLES:
            a=agent(r,role)
            item.update({role+'_prediction':a['prediction'],role+'_pA':a['label_probabilities']['A'],
                         role+'_confidence':a['confidence']})
        label_rows.append(item)
    with (OUT/'observed_matches_evaluation_only.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(label_rows[0]));writer.writeheader();writer.writerows(label_rows)
    print(json.dumps({k:v for k,v in result.items() if k not in ['metrics','subsets','same_asin_strata']},ensure_ascii=False),flush=True)
    for name,m in scores.items():print(name,m['selected'],m['observed_hits'],m['observed_match_rate'],m['candidate_hit_retention'],flush=True)
    write_json(OUT/'status.json',{'state':'target_matching_complete_review_pending','evaluated_at':utc_now()})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','evaluate'])
    args=parser.parse_args()
    (prepare if args.stage=='prepare' else evaluate)()
