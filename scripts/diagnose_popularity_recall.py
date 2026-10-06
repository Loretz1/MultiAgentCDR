"""CPU-only Popularity Top100: freeze visible-only candidates before evaluation.

Main score is visible target interaction count; distinct visible target users
is an explicitly separate sensitivity check. All users share the same Top100.
No G/text model, LLM, internal validation, or formal test data is accessed.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import platform
import time
import numpy as np
import pandas as pd
from agent_pipeline_common import ROOT, complete_stage, load_bundle, read_json, rows, sha256, stable_top, stage, utc_now, verify_files, write_json
from diagnose_candidate_recall import summarize, source_asin_item_sets

BUNDLE=ROOT/'CDRec/data/agent_evidence/cloth_to_sports/server_bundle_v2'
DATA=ROOT/'CDRec/data/agent_evidence/cloth_to_sports/v2'
PILOT=ROOT/'doc/experiments/2026-10-06_featurize_real/artifacts/MultiAgentCDR/runs/pilot_v1/inputs_prompt_dev/agent_inputs.jsonl'
BASELINES=ROOT/'doc/experiments/2026-10-06_candidate_recall'
OUT=ROOT/'doc/experiments/2026-10-06_popularity_recall'
K=100
MODES=('interaction_count','distinct_users')


def visible_counts(target, item_count):
    target=np.asarray(target,dtype=np.int64)
    if target.ndim!=2 or target.shape[1]!=2 or np.any(target<=0) or (len(target) and target[:,1].max()>item_count):
        raise ValueError('Invalid visible target interaction IDs')
    events=np.bincount(target[:,1],minlength=item_count+1)
    unique=np.unique(target,axis=0)
    users=np.bincount(unique[:,1],minlength=item_count+1)
    return events,users


def global_top(counts,k):
    if k<=0 or k>=len(counts):raise ValueError('K exceeds eligible target catalog')
    return [item for item,_ in stable_top(counts[1:],np.arange(1,len(counts)),k)]


def settings():
    return {'script_sha256':sha256(Path(__file__)),
        'dependency_sha256':{name:sha256(ROOT/'scripts'/name) for name in ('agent_pipeline_common.py','diagnose_candidate_recall.py')},
        'legacy_pilot_input_sha256':sha256(PILOT),'group':'prompt_dev','k':K,
        'cohorts':['legacy_pilot_20','all_dev_156'],'modes':list(MODES),'primary_mode':'interaction_count',
        'popularity_scope':'visible_target_training_only;dev_and_val_target_histories_removed',
        'ranking':'count_desc_then_target_item_id_asc','candidate_policy':'standard_catalog;no_source_ASIN_filter;all_users_share_same_list',
        'item_eligibility':'all_benchmark_target_item_IDs;ID_zero_excluded',
        'source_ASIN_use':'stratification_only;does_not_change_candidates',
        'generation_reads_hidden_feedback':False,'evaluation_labels':'internal_prompt_dev_only',
        'internal_prompt_val_read':False,'formal_evaluation_read':False,'llm_calls':0,'gpu_used':False,
        'full_agent_evidence_constructed':False}


def write_csv(path, records):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)


def prepare():
    started=time.monotonic()
    manifest,groups,source,target,bundle_hash=load_bundle(BUNDLE)
    config=settings()
    with stage(OUT,'popularity_top100_candidates',bundle_hash,config) as run:
        if not run:
            print('Existing visible-only candidate package verified.',flush=True);return
        users=sorted(groups['prompt_dev'])
        pilot=sorted({r['source_user_id'] for r in rows(PILOT)})
        assert len(users)==156 and len(pilot)==20 and set(pilot)<=set(users)
        assert not set(target[:,0]) & set(groups['prompt_dev']+groups['prompt_val'])
        mapping=read_json(BUNDLE/'id_mapping.json')
        seen=source_asin_item_sets(source,mapping,users)
        counts,distinct=visible_counts(target,manifest['counts']['target_items'])
        tops={'interaction_count':global_top(counts,K),'distinct_users':global_top(distinct,K)}
        meta={r['item_id']:r for r in rows(BUNDLE/'target_catalog.jsonl') if r['item_id'] in set.union(*(set(v) for v in tops.values()))}
        write_json(OUT/'global_top100.json',{'schema':'popularity_candidate_list_v1','k':K,'primary_mode':'interaction_count',
            'rankings':tops,'same_list_for_all_users':True,'hidden_feedback_read':False,
            'bundle_sha256':bundle_hash,'count_definitions':{'interaction_count':'number of visible target training rows',
                'distinct_users':'number of unique visible (target_user,target_item) pairs'}})
        catalog_rows=[]
        for mode in MODES:
            for rank,item in enumerate(tops[mode],1):
                catalog_rows.append({'mode':mode,'rank':rank,'target_item_id':item,'asin':mapping['tgt']['id2item'][item],
                    'title':meta.get(item,{}).get('title',''),'visible_interactions':int(counts[item]),'distinct_visible_users':int(distinct[item])})
        write_csv(OUT/'top100_items.csv',catalog_rows)
        candidate_list_hash=sha256(OUT/'global_top100.json')
        records=[]
        with (OUT/'candidate_pairs.jsonl').open('w',encoding='utf-8',newline='\n') as stream:
            for user in users:
                r={'user_id':user,'in_legacy_pilot_20':user in pilot,'source_seen_target_items':sorted(seen[user]),'rankings':tops}
                records.append(r)
                for rank,item in enumerate(tops['interaction_count'],1):
                    pair={'pair_id':f'cloth_sports:prompt_dev:{user}:{item}','source_user_id':user,'target_item_id':item,
                        'retrieval':{'method':'popularity_interaction_count','rank':rank,'score':int(counts[item])},
                        'provenance':{'group':'prompt_dev','bundle_sha256':bundle_hash,'candidate_list_sha256':candidate_list_hash}}
                    stream.write(json.dumps(pair,separators=(',',':'))+'\n')
        with (OUT/'rankings.jsonl').open('w',encoding='utf-8',newline='\n') as stream:
            for r in records:stream.write(json.dumps(r,separators=(',',':'))+'\n')
        assert len({tuple(r['rankings']['interaction_count']) for r in records})==1
        for mode,score in (('interaction_count',counts),('distinct_users',distinct)):
            assert len(tops[mode])==len(set(tops[mode]))==K
            # Independent Python counting/sort check, separate from numpy producer.
            raw=Counter(int(item) for _,item in target) if mode=='interaction_count' else Counter(item for _,item in set(map(tuple,target.tolist())))
            expected=sorted(range(1,len(counts)),key=lambda item:(-raw[item],item))[:K]
            assert tops[mode]==expected
        write_json(OUT/'generation_audit.json',{'state':'passed','users':len(users),'pilot_users':pilot,
            'target_catalog_items':manifest['counts']['target_items'],'visible_target_rows':len(target),
            'unique_visible_target_user_item_pairs':int(distinct.sum()),'duplicate_visible_rows':int(counts.sum()-distinct.sum()),
            'main_candidate_pairs':len(users)*K,'distinct_candidate_lists':1,
            'main_vs_distinct_user_top100_overlap':len(set(tops[MODES[0]]) & set(tops[MODES[1]])),
            'main_vs_distinct_user_order_identical':tops[MODES[0]]==tops[MODES[1]],
            'minimum_main_top100_visible_count':int(counts[tops[MODES[0]][-1]]),
            'independent_counter_and_sort_check':True,'hidden_feedback_read':False,'llm_calls':0,'gpu_used':False,
            'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__},
            'elapsed_seconds':round(time.monotonic()-started,3)})
        complete_stage(OUT,['global_top100.json','top100_items.csv','candidate_pairs.jsonl','rankings.jsonl','generation_audit.json'],
            users=len(users),pilot_users=len(pilot),main_candidate_pairs=len(users)*K,hidden_feedback_read=False)
        print('Frozen shared Popularity Top100: 156 users, 15600 pairs; no hidden feedback read.',flush=True)


def evaluate():
    started=time.monotonic()
    manifest=read_json(OUT/'manifest.json');verify_files(OUT,manifest)
    request=read_json(OUT/'request.json')
    assert manifest['state']=='complete' and request==manifest['request'] and request['config']==settings()
    records=list(rows(OUT/'rankings.jsonl'));users=[r['user_id'] for r in records]
    assert len(users)==len(set(users))==156
    label_path=DATA/'hidden_feedback/prompt_dev.pkl'
    hidden=pd.read_pickle(label_path)
    assert list(hidden.columns)==['user','item'] and set(hidden['user'])==set(users)
    raw_rows=len(hidden);hidden=hidden.drop_duplicates(['user','item'])
    truth={u:set() for u in users}
    for user,item in hidden[['user','item']].itertuples(index=False,name=None):truth[int(user)].add(int(item))
    seen={r['user_id']:set(r['source_seen_target_items']) for r in records}
    cohorts={'legacy_pilot_20':[r['user_id'] for r in records if r['in_legacy_pilot_20']], 'all_dev_156':users}
    metrics=[];per_user=[]
    for cohort,selected_users in cohorts.items():
        for mode in MODES:
            selected={r['user_id']:set(r['rankings'][mode]) for r in records if r['user_id'] in selected_users}
            details=summarize(selected,{u:truth[u] for u in selected_users},seen)
            metadata={'cohort':cohort,'method':'popularity_'+mode,'policy':'standard','k':K,'primary':mode=='interaction_count'}
            per_user.extend({**metadata,**r} for r in details.pop('per_user'))
            metrics.append({**metadata,**details})
    write_csv(OUT/'aggregate_metrics.csv',metrics);write_csv(OUT/'per_user_metrics.csv',per_user)
    top=read_json(OUT/'global_top100.json');rank_lookup={mode:{item:rank for rank,item in enumerate(ids,1)} for mode,ids in top['rankings'].items()}
    traces=[{'user_id':u,'target_item_id':item,'same_asin_source_history':int(item in seen[u]),
             'interaction_count_rank':rank_lookup['interaction_count'].get(item),'distinct_users_rank':rank_lookup['distinct_users'].get(item)}
            for u in users for item in sorted(truth[u])]
    write_csv(OUT/'observed_history_evaluation_only.csv',traces)
    # Existing G/text/RRF results are joined only after this candidate list is frozen.
    baseline_manifest=read_json(BASELINES/'evaluation_manifest.json');verify_files(BASELINES,baseline_manifest)
    assert baseline_manifest['label_source']['sha256']==sha256(label_path),'Comparison uses different hidden history'
    baselines=list(csv.DictReader((BASELINES/'per_user_metrics.csv').open(encoding='utf-8-sig',newline='')))
    comparisons=list(metrics)
    for cohort,selected_users in cohorts.items():
        for method in ('semantic','g','rrf'):
            rr=[r for r in baselines if r['policy']=='standard' and r['method']==method and int(r['k'])==K and int(r['user_id']) in selected_users]
            assert {int(r['user_id']) for r in rr}==set(selected_users)
            def total(key):return sum(int(r[key]) for r in rr)
            candidates=total('candidates');hits=total('observed_hits');known=total('hidden_interactions')
            novel_hits=total('different_asin_hits');novel_known=total('different_asin_hidden_interactions')
            comparisons.append({'cohort':cohort,'method':method,'policy':'standard','k':K,'primary':False,
                'users':len(rr),'candidates':candidates,'observed_hits':hits,'observed_match_rate':hits/candidates if candidates else None,
                'hidden_interactions':known,'recall_micro':hits/known if known else None,
                'different_asin_hits':novel_hits,'different_asin_hidden_interactions':novel_known,
                'different_asin_recall_micro':novel_hits/novel_known if novel_known else None,
                'users_with_hit':sum(int(r['observed_hits'])>0 for r in rr),'user_hit_rate':sum(int(r['observed_hits'])>0 for r in rr)/len(rr)})
    columns=('cohort','method','k','users','candidates','observed_hits','observed_match_rate','hidden_interactions','recall_micro',
        'different_asin_hits','different_asin_hidden_interactions','different_asin_recall_micro','users_with_hit','user_hit_rate')
    write_csv(OUT/'comparison_top100.csv',[{key:r[key] for key in columns} for r in comparisons])
    # Independent intersection/count audit of all four cohort/mode rows.
    for result in metrics:
        selected_users=cohorts[result['cohort']];mode=result['method'].removeprefix('popularity_');chosen=set(top['rankings'][mode])
        direct=[r for r in traces if r['user_id'] in selected_users and r['target_item_id'] in chosen]
        assert result['observed_hits']==len(direct)
        assert result['same_asin_hits']==sum(r['same_asin_source_history'] for r in direct)
        assert result['different_asin_hits']==sum(not r['same_asin_source_history'] for r in direct)
    result={'state':'complete','completed_at':utc_now(),'users':156,'pilot_users':20,'primary_mode':'interaction_count',
        'k':K,'metrics':metrics,'comparison':[{key:r[key] for key in columns} for r in comparisons],
        'label_source':{'path':str(label_path.relative_to(ROOT)),'sha256':sha256(label_path)},
        'hidden_rows_before_deduplication':raw_rows,'hidden_interactions':len(hidden),
        'candidate_manifest_sha256':sha256(OUT/'manifest.json'),'ranking_frozen_before_label_read':True,
        'internal_prompt_val_read':False,'formal_evaluation_read':False,'llm_calls':0,'gpu_used':False,
        'agent_feedback_collected':False,'unobserved_is_negative_preference':False,
        'evaluation_seconds':round(time.monotonic()-started,3)}
    write_json(OUT/'results.json',result)
    names=['results.json','aggregate_metrics.csv','per_user_metrics.csv','comparison_top100.csv','observed_history_evaluation_only.csv']
    write_json(OUT/'evaluation_manifest.json',{'state':'complete','completed_at':result['completed_at'],
        'candidate_manifest_sha256':result['candidate_manifest_sha256'],'files':{name:{'sha256':sha256(OUT/name),'bytes':(OUT/name).stat().st_size} for name in names}})
    write_json(OUT/'verification.json',{'state':'passed','checks':['visible-only popularity independently counted and sorted',
        'one shared Top100 for all users','156/20 cohorts match archived users','frozen ranking before label read',
        'four aggregate rows independently checked against observed-history traces','comparison label source matches'],
        'metrics_rows':len(metrics),'comparison_rows':len(comparisons),'internal_prompt_val_read':False,'formal_evaluation_read':False})
    for r in metrics:print(json.dumps(r,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','evaluate'))
    args=parser.parse_args();(prepare if args.command=='prepare' else evaluate)()
