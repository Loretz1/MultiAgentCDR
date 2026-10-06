"""CPU-only candidate recall diagnostics; generation never reads target holdouts.

prepare freezes the experiment and generates rankings from archived vectors.
evaluate reads only internal prompt_dev interactions after rankings are complete.
No model loading, retraining, LLM calls, or changes to the original benchmark.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import platform
import time

import numpy as np
import pandas as pd

from agent_pipeline_common import (
    ROOT, complete_stage, load_bundle, read_json, rows, save_arrays, sha256,
    stable_top, stage, utc_now, verify_files, write_json,
)
from export_agent_evidence import artifact_vectors, recall

BUNDLE = ROOT / 'CDRec/data/agent_evidence/cloth_to_sports/server_bundle_v2'
DATA = ROOT / 'CDRec/data/agent_evidence/cloth_to_sports/v2'
PILOT = ROOT / 'doc/experiments/2026-10-06_featurize_real/artifacts/MultiAgentCDR/runs/pilot_v1'
OUT = ROOT / 'doc/experiments/2026-10-06_candidate_recall'
BUDGETS = (10, 50, 100, 200)
METHODS = ('semantic', 'g', 'rrf', 'union')
POLICIES = ('standard', 'exclude_source_asin')
RRF_DEPTH = 200
RRF_CONSTANT = 60


def settings():
    return {
        'script_sha256': sha256(Path(__file__)),
        'dependency_sha256': {name: sha256(ROOT / 'scripts' / name) for name in
                              ['agent_pipeline_common.py', 'export_agent_evidence.py', 'encode_agent_text.py']},
        'group': 'prompt_dev', 'user_limit': None, 'budgets': list(BUDGETS),
        'methods': list(METHODS), 'policies': list(POLICIES),
        'rrf_depth_per_method': RRF_DEPTH, 'rrf_constant': RRF_CONSTANT,
        'rrf_budget_meaning': 'K_total_pairs_per_user;fixed_200_per_method_pool_for_all_K',
        'union_budget_meaning': 'each_method_TopK_union;up_to_2K_pairs_per_user;not_equal_budget',
        'ranking': 'score_desc_then_item_id_asc;RRF_desc_then_item_id_asc',
        'exclude_source_asin': 'source_visible_history_only;filter_before_topK_and_RRF',
        'zero_semantic_profile': 'empty_semantic_recall;G_still_available',
        'generation_reads_hidden_feedback': False,
        'evaluation_labels': 'internal_prompt_dev_only',
        'formal_test_and_internal_validation_read': False,
        'hidden_interaction_is_preference_gold': False,
        'diagnostic_only': True, 'llm_calls': 0, 'gpu_used': False,
        'legacy_audit': '20_pilot_users;Top50_per_method_RRF_then10;before_hidden_feedback',
    }


def fuse(semantic_ids, g_ids, constant=RRF_CONSTANT):
    scores = defaultdict(float)
    for records in (semantic_ids, g_ids):
        for rank, item in enumerate(records, 1):
            scores[int(item)] += 1 / (constant + rank)
    return sorted(scores, key=lambda item: (-scores[item], item))


def candidate_ids(rankings, method, k):
    if method == 'union':
        return set(rankings['semantic'][:k]) | set(rankings['g'][:k])
    return set(rankings[method][:k])


def ranked_ids(scores, eligible, limit):
    return [item for item, _ in stable_top(scores[eligible], eligible, limit)]


def source_asin_item_sets(source, mapping, users):
    target_lookup = mapping['tgt']['item2id']
    result = {int(user): set() for user in users}
    for user, item in source:
        if int(user) in result:
            asin = mapping['src']['id2item'][int(item)]
            target_item = target_lookup.get(asin)
            if target_item is not None:
                result[int(user)].add(int(target_item))
    return result


def summarize(selection, truth, source_seen):
    """Observed-history coverage, retaining users with zero chosen items or hits."""
    selected_count = hits = same_selected = same_hits = 0
    same_truth = sum(len(items & source_seen[u]) for u, items in truth.items())
    total_truth = sum(map(len, truth.values()))
    per_user = []
    for user in sorted(truth):
        chosen = set(selection[user]); known = truth[user]; seen = source_seen[user]
        hit = len(chosen & known); novel_truth = known - seen
        novelty_hits = len(chosen & novel_truth)
        selected_count += len(chosen); hits += hit
        same_selected += len(chosen & seen); same_hits += len(chosen & known & seen)
        per_user.append({
            'user_id': user, 'candidates': len(chosen), 'observed_hits': hit,
            'hidden_interactions': len(known), 'hidden_history_recall': hit / len(known) if known else None,
            'different_asin_candidates': len(chosen - seen), 'different_asin_hits': novelty_hits,
            'different_asin_hidden_interactions': len(novel_truth),
            'different_asin_recall': novelty_hits / len(novel_truth) if novel_truth else None,
            'same_asin_candidates': len(chosen & seen), 'same_asin_hits': len(chosen & known & seen),
        })
    novel_total = total_truth - same_truth; novel_hits = hits - same_hits
    recalls = [r['hidden_history_recall'] for r in per_user if r['hidden_history_recall'] is not None]
    novel_recalls = [r['different_asin_recall'] for r in per_user if r['different_asin_recall'] is not None]
    return {
        'users': len(truth), 'candidates': selected_count, 'observed_hits': hits,
        'observed_match_rate': hits / selected_count if selected_count else None,
        'hidden_interactions': total_truth, 'recall_micro': hits / total_truth if total_truth else None,
        'recall_macro': float(np.mean(recalls)) if recalls else None,
        'users_with_hit': sum(r['observed_hits'] > 0 for r in per_user),
        'user_hit_rate': sum(r['observed_hits'] > 0 for r in per_user) / len(truth),
        'same_asin_candidates': same_selected, 'same_asin_hits': same_hits,
        'same_asin_hidden_interactions': same_truth,
        'same_asin_recall_micro': same_hits / same_truth if same_truth else None,
        'different_asin_candidates': selected_count - same_selected,
        'different_asin_hits': novel_hits, 'different_asin_hidden_interactions': novel_total,
        'different_asin_recall_micro': novel_hits / novel_total if novel_total else None,
        'different_asin_recall_macro': float(np.mean(novel_recalls)) if novel_recalls else None,
        'different_asin_users_with_truth': len(novel_recalls),
        'per_user': per_user,
    }


def prepare():
    started = time.monotonic()
    manifest, groups, source, _, bundle_hash = load_bundle(BUNDLE)
    config = settings()
    config['encoder_manifest_sha256'] = sha256(PILOT / 'encoder/manifest.json')
    config['g_manifest_sha256'] = sha256(PILOT / 'g/manifest.json')
    with stage(OUT, 'candidate_recall_rankings', bundle_hash, config) as run:
        if not run:
            print('Existing frozen rankings verified; generation skipped.', flush=True)
            return
        # request.json is persisted before scoring; no hidden labels are read here.
        text, _ = artifact_vectors(PILOT / 'encoder', 'bge_text', bundle_hash)
        model, _ = artifact_vectors(PILOT / 'g', 'emcdr_g', bundle_hash)
        users = sorted(groups['prompt_dev'])
        assert len(users) == len(set(users)) == 156
        counts = manifest['counts']; target_ids = np.arange(1, counts['target_items'] + 1)
        assert text['source_users'].shape == (counts['source_users'] + 1, text['target_items'].shape[1])
        assert text['target_items'].shape[0] == model['target_items'].shape[0] == counts['target_items'] + 1
        assert model['mapped_users'].shape == (counts['source_users'] + 1, model['target_items'].shape[1])
        for key in ('source_users', 'target_items'):
            norms = np.linalg.norm(text[key], axis=1)
            assert np.all((norms < 1e-6) | (np.abs(norms - 1) < 1e-4))
        mapping = read_json(BUNDLE / 'id_mapping.json')
        same_items = source_asin_item_sets(source, mapping, users)
        available = np.linalg.norm(text['target_items'], axis=1) > 0
        semantic_ids = target_ids[available[target_ids]]
        sem_scores = np.empty((len(users), counts['target_items'] + 1), dtype=np.float32)
        g_scores = np.empty_like(sem_scores)
        old_inputs = list(rows(PILOT / 'inputs_prompt_dev/agent_inputs.jsonl'))
        expected = defaultdict(set)
        for row in old_inputs:
            expected[row['source_user_id']].add(row['target_item_id'])
        legacy = {}; missing_profiles = []
        with (OUT / 'rankings.jsonl').open('w', encoding='utf-8') as stream:
            for index, user in enumerate(users):
                sem_scores[index] = text['target_items'].dot(text['source_users'][user])
                g_scores[index] = model['target_items'].dot(model['mapped_users'][user])
                user_available = bool(np.linalg.norm(text['source_users'][user]) > 0)
                sem_eligible = semantic_ids if user_available else np.asarray([], dtype=np.int64)
                if not user_available: missing_profiles.append(user)
                if user in expected:
                    old = recall(sem_scores[index], sem_eligible, g_scores[index], target_ids,
                                 {'recall_per_method': 50, 'rrf_constant': 60, 'candidates_per_user': 10})
                    got = {item for item, _ in old}
                    legacy[user] = {'same_candidate_set': got == expected[user],
                                    'recomputed': sorted(got), 'archived': sorted(expected[user])}
                rankings = {}
                for policy in POLICIES:
                    blocked = same_items[user] if policy == 'exclude_source_asin' else set()
                    sids = np.asarray([i for i in sem_eligible if int(i) not in blocked], dtype=np.int64)
                    gids = np.asarray([i for i in target_ids if int(i) not in blocked], dtype=np.int64)
                    semantic = ranked_ids(sem_scores[index], sids, RRF_DEPTH)
                    g = ranked_ids(g_scores[index], gids, RRF_DEPTH)
                    rankings[policy] = {'semantic': semantic, 'g': g, 'rrf': fuse(semantic, g)[:max(BUDGETS)]}
                stream.write(json.dumps({'user_id': user, 'semantic_profile_available': user_available,
                                         'source_seen_target_items': sorted(same_items[user]),
                                         'rankings': rankings}, separators=(',', ':')) + '\n')
                if (index + 1) % 26 == 0:
                    print(f'Ranked {index+1}/{len(users)} development users; no holdout read.', flush=True)
        assert np.isfinite(sem_scores).all() and np.isfinite(g_scores).all()
        assert len(legacy) == 20 and all(v['same_candidate_set'] for v in legacy.values()), 'Legacy pilot recall differs'
        score_errors = {'semantic': 0.0, 'g': 0.0}
        lookup = {user: index for index, user in enumerate(users)}
        for row in old_inputs:
            index = lookup[row['source_user_id']]; item = row['target_item_id']
            expected_sem = row['evidence']['semantic']['similarity']
            if expected_sem is not None:
                score_errors['semantic'] = max(score_errors['semantic'], abs(float(sem_scores[index,item]) - expected_sem))
            score_errors['g'] = max(score_errors['g'], abs(float(g_scores[index,item]) - row['evidence']['collaborative']['g_raw']))
        assert max(score_errors.values()) < 1e-4, score_errors
        save_arrays(OUT / 'scores.npz', users=np.asarray(users), semantic=sem_scores, g=g_scores)
        write_json(OUT / 'generation_audit.json', {
            'users': len(users), 'target_catalog_items': len(target_ids),
            'target_text_vectors_available': len(semantic_ids),
            'users_without_positive_semantic_profile': missing_profiles,
            'hidden_feedback_read': False, 'llm_calls': 0, 'gpu_used': False,
            'legacy_pilot_candidates': legacy, 'legacy_max_score_absolute_error': score_errors,
            'elapsed_seconds': round(time.monotonic() - started, 3),
            'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__},
        })
        complete_stage(OUT, ['rankings.jsonl', 'scores.npz', 'generation_audit.json'],
                       users=len(users), candidate_budgets=list(BUDGETS), hidden_feedback_read=False)
        print('Rankings and original 200-pair recall audit complete.', flush=True)


def evaluate():
    started = time.monotonic()
    manifest = read_json(OUT / 'manifest.json'); verify_files(OUT, manifest)
    request = read_json(OUT / 'request.json')
    stored = request['config']
    assert manifest['request'] == request
    assert all(stored[key] == value for key,value in settings().items()), 'Frozen settings changed'
    records = list(rows(OUT / 'rankings.jsonl')); users = [r['user_id'] for r in records]
    assert len(users) == len(set(users)) == 156
    # Only this declared holdout file is read; candidate generation is already complete.
    label_path = DATA / 'hidden_feedback/prompt_dev.pkl'
    hidden = pd.read_pickle(label_path)
    assert list(hidden.columns) == ['user','item'] and set(hidden['user']) == set(users)
    original_rows = len(hidden); hidden = hidden.drop_duplicates(['user','item'])
    truth = {user: set() for user in users}
    for user,item in hidden[['user','item']].itertuples(index=False,name=None):truth[int(user)].add(int(item))
    seen = {r['user_id']: set(r['source_seen_target_items']) for r in records}
    metrics = []; user_metrics = []; selections = {}
    for policy in POLICIES:
        for method in METHODS:
            previous = {u:set() for u in users}
            for k in BUDGETS:
                selected = {r['user_id']: candidate_ids(r['rankings'][policy], method, k) for r in records}
                assert all(previous[u] <= selected[u] for u in users), 'Candidate budgets are not nested'
                if policy == 'exclude_source_asin':assert all(not(selected[u] & seen[u]) for u in users)
                details = summarize(selected, truth, seen)
                metadata = {'policy': policy, 'method': method, 'k': k,
                            'equal_total_budget': method != 'union'}
                user_metrics.extend({**metadata, **r} for r in details.pop('per_user'))
                metrics.append({**metadata, **details});selections[(policy,method,k)] = selected
                previous = selected
    legacy = read_json(OUT / 'generation_audit.json')['legacy_pilot_candidates']
    legacy_selected = {u:set(legacy[str(u)]['recomputed']) for u in users if str(u) in legacy}
    legacy_truth = {u:truth[u] for u in legacy_selected}
    old = summarize(legacy_selected, legacy_truth, seen)
    assert old['candidates'] == 200 and old['observed_hits'] == 11 and old['different_asin_hits'] == 2
    old.pop('per_user')
    # Serialize observed positives only in this evaluation artifact, not ranking inputs.
    traces = []
    for r in records:
        user = r['user_id']; positions = {}
        for policy in POLICIES:
            for method in ('semantic','g','rrf'):
                positions[(policy,method)] = {item:rank for rank,item in enumerate(r['rankings'][policy][method],1)}
        for item in sorted(truth[user]):
            row = {'user_id':user,'item_id':item,'same_asin_source_history':int(item in seen[user])}
            for (policy,method), lookup in positions.items():row[policy+'_'+method+'_rank_within_saved_top200'] = lookup.get(item)
            traces.append(row)
    for name, data in [('aggregate_metrics.csv',metrics),('per_user_metrics.csv',user_metrics),
                       ('observed_history_evaluation_only.csv',traces)]:
        with (OUT/name).open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    result = {
        'state':'complete', 'completed_at':utc_now(), 'users':len(users),
        'hidden_interactions':len(hidden), 'hidden_rows_before_deduplication':original_rows,
        'same_asin_hidden_interactions':sum(len(truth[u]&seen[u]) for u in users),
        'different_asin_hidden_interactions':sum(len(truth[u]-seen[u]) for u in users),
        'metrics':metrics, 'legacy_pilot_reproduction':old,
        'label_source':{'path':str(label_path.relative_to(ROOT)),'sha256':sha256(label_path)},
        'candidate_generation_manifest_sha256':sha256(OUT/'manifest.json'),
        'ranking_is_frozen_before_label_read':True, 'internal_prompt_val_read':False,
        'formal_test_read':False, 'llm_calls':0, 'gpu_used':False,
        'unobserved_is_negative_preference':False, 'downstream_recommendation_evaluated':False,
        'evaluation_seconds':round(time.monotonic()-started,3),
    }
    write_json(OUT/'results.json',result)
    write_json(OUT/'evaluation_manifest.json',{
        'state':'complete','request_sha256':sha256(OUT/'request.json'),
        'files':{name:{'sha256':sha256(OUT/name),'bytes':(OUT/name).stat().st_size} for name in
                 ['results.json','aggregate_metrics.csv','per_user_metrics.csv','observed_history_evaluation_only.csv']},
        'label_source':result['label_source'], 'completed_at':result['completed_at'],
    })
    write_json(OUT/'evaluation_status.json',{'state':'complete','completed_at':result['completed_at']})
    print(json.dumps({k:v for k,v in result.items() if k not in ('metrics','legacy_pilot_reproduction')},ensure_ascii=False),flush=True)
    for r in metrics:
        print(r['policy'],r['method'],r['k'],r['candidates'],r['observed_hits'],
              round(r['recall_micro'],4),r['different_asin_hits'],round(r['different_asin_recall_micro'],4),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','evaluate'))
    args=parser.parse_args()
    (prepare if args.command == 'prepare' else evaluate)()
