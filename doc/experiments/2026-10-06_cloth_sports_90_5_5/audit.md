# Cloth -> Sports local preparation audit

Created (UTC): 2026-10-06T00:59:01.062500+00:00

| Domain | Users | Items | Review rows | Duplicate user/item rows |
|---|---:|---:|---:|---:|
| Clothing_Shoes_and_Jewelry | 39387 | 23033 | 278677 | 0 |
| Sports_and_Outdoors | 35598 | 18357 | 296337 | 0 |

## Benchmark and internal prompt split

Benchmark user groups: `{"overlap_users": 3128, "valid_cold_users": 390, "test_cold_users": 390, "src_only_users": 35479, "tgt_only_users": 31690}`

Benchmark interactions: `{"train_src": 278677, "train_tgt": 287894, "valid_cold_tgt": 4373, "test_cold_tgt": 4070, "valid_warm_tgt": 0, "test_warm_tgt": 0}`

Internal groups: `{"support": 2816, "prompt_dev": 156, "prompt_val": 156}`

Prompt development/validation target histories are wholly hidden from the prompt-fold training data and its popularity statistics. Source profiles use source training reviews only. Restore full benchmark training data only after prompt development is finished.

## Metadata

```json
{
  "src": {
    "metadata_records_scanned": 1503384,
    "retained_5core_items": 23033,
    "metadata_found": 23033,
    "metadata_missing": 0,
    "duplicate_relevant_metadata_rows": 0,
    "title_missing": 23,
    "description_missing": 21614,
    "text_empty": 0
  },
  "tgt": {
    "metadata_records_scanned": 532197,
    "retained_5core_items": 18357,
    "metadata_found": 18357,
    "metadata_missing": 0,
    "duplicate_relevant_metadata_rows": 0,
    "title_missing": 90,
    "description_missing": 2661,
    "text_empty": 0
  }
}
```

## Validation

- PASS: original_benchmark_functions_used
- PASS: benchmark_cold_raw_users_absent_from_target_train
- PASS: all_original_review_rows_preserved
- PASS: prompt_hidden_users_absent_from_visible_target_train
- PASS: profiles_source_train_only_and_candidate_blind
- PASS: metadata_behavior_fields_excluded
- PASS: full_and_fold_popularity_computed_separately

## Remaining work and limits

- No semantic embeddings, G model, nearest neighbors, candidate lists, agent labels or confidence have been generated.
- Internal prompt groups are a single deterministic user split; no cross-fitting has run.
- Positive/negative ratings label source review sentiment only; benchmark interactions are unchanged.
- Static metadata is not timestamped; the benchmark is an offline non-temporal protocol.
- Hidden feedback contains observed interactions, not role-specific A/B/C gold labels.
- Raw single-domain IDs remain domain-specific; benchmark cold labels use source-space user IDs.

## Artifact locations

- Benchmark: `F:\Projects\MultiAgentCDR\CDRec\data\Amazon2014\Clothing_Shoes_and_Jewelry+Sports_and_Outdoors\all_users\WarmValid0_WarmTest0_ColdValid0.1_ColdTest0.1_shuffle`
- Evidence: `F:\Projects\MultiAgentCDR\CDRec\data\agent_evidence\cloth_to_sports\v2`
- Full details: `F:\Projects\MultiAgentCDR\doc\experiments\2026-10-06_cloth_sports_90_5_5\audit.json`

Elapsed preprocessing time: 242.3 seconds.
