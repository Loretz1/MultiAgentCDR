"""Independently recompute pilot evidence from visible observations and frozen vectors."""
from __future__ import annotations

import argparse
from collections import defaultdict, Counter
from pathlib import Path

import numpy as np

from agent_pipeline_common import load_bundle, read_json, rows, sha256, write_json
from collect_agent_feedback import validate_record


def binary_cosine(common, left_size, right_size):
    # Preserve the producer's float32 arithmetic for deterministic boundary ties.
    left = np.float32(1) / np.sqrt(np.float32(left_size))
    right = np.float32(1) / np.sqrt(np.float32(right_size))
    score = np.float32(0)
    for _ in range(common):
        score = np.float32(score + left * right)
    return float(score)


def audit(bundle, encoder, g, inputs, output):
    manifest, groups, source, target, bundle_hash = load_bundle(bundle)
    records = list(rows(inputs))
    if not records:
        raise ValueError("Empty real input file")
    src_history, tgt_history, item_users = defaultdict(set), defaultdict(set), defaultdict(set)
    for user, item in source:
        src_history[int(user)].add(int(item))
    for user, item in target:
        tgt_history[int(user)].add(int(item))
        item_users[int(item)].add(int(user))
    counts = Counter(target[:, 1].tolist())
    config = read_json(Path(inputs).parent / "manifest.json")["request"]["config"]
    profiles = {p["source_user_id"]: p for p in rows(Path(bundle) / "source_profiles.jsonl") if p["source_user_id"] in {r["source_user_id"] for r in records}}
    source_catalog = {r["item_id"]: r for r in rows(Path(bundle) / "source_catalog.jsonl")}
    target_catalog = {r["item_id"]: r for r in rows(Path(bundle) / "target_catalog.jsonl")}
    with np.load(Path(encoder) / "vectors.npz") as data:
        text = {key: data[key] for key in data.files}
    with np.load(Path(g) / "vectors.npz") as data:
        model = {key: data[key] for key in data.files}
    ids = np.arange(1, manifest["counts"]["target_items"] + 1)
    candidate_neighbor_cache = {}
    pair_ids = set()
    checks = Counter()
    for record in records:
        validate_record(record, len(pair_ids) + 1)
        user, item = record["source_user_id"], record["target_item_id"]
        assert record["pair_id"] not in pair_ids
        pair_ids.add(record["pair_id"])
        assert user in groups[config["group"]] and user not in tgt_history
        assert record["provenance"]["bundle_sha256"] == bundle_hash
        expected_g = model["target_items"].dot(model["mapped_users"][user])
        collaborative = record["evidence"]["collaborative"]
        np.testing.assert_allclose(collaborative["g_raw"], expected_g[item], atol=1e-5)
        rank = 1 + int(np.sum(expected_g[ids] > expected_g[item])) + int(np.sum((expected_g[ids] == expected_g[item]) & (ids < item)))
        assert collaborative["rank"] == rank
        checks["g_score_and_rank"] += 1
        semantic = record["evidence"]["semantic"]
        if semantic["similarity"] is not None:
            np.testing.assert_allclose(semantic["similarity"], text["target_items"][item].dot(text["source_users"][user]), atol=1e-5)
        checks["semantic_score"] += 1
        for match in semantic["matched_concepts"]:
            origin = match["source"]
            history = [h for h in profiles[user]["source_history"] if h["record_id"] == origin["record_id"]]
            assert len(history) == 1 and history[0]["rating"] >= 4 and history[0]["item_id"] == origin["source_item_id"]
            def field_text(catalog, location):
                return "; ".join(path[-1] for path in catalog["categories"] if path) if location["field"] == "category_leaf" else catalog[location["field"]]
            assert origin["span"] in field_text(source_catalog[origin["source_item_id"]], origin)
            assert match["target"]["span"] in field_text(target_catalog[item], match["target"])
            assert origin["span"].lower() == match["target"]["span"].lower() == match["concept"]
        checks["literal_concept_provenance"] += 1
        neighbors = []
        for supporter in groups["support"]:
            common = len(src_history[user] & src_history[supporter])
            if common and supporter != user:
                neighbors.append((supporter, binary_cosine(common, len(src_history[user]), len(src_history[supporter]))))
        neighbors.sort(key=lambda pair: (-pair[1], pair[0]))
        neighbors = neighbors[:config["source_neighbors"]]
        if item not in candidate_neighbor_cache:
            cooccurrences = Counter()
            for owner in item_users[item]:
                cooccurrences.update(tgt_history[owner] - {item})
            related = [(other, binary_cosine(common, len(item_users[item]), len(item_users[other]))) for other, common in cooccurrences.items()]
            related.sort(key=lambda pair: (-pair[1], pair[0]))
            candidate_neighbor_cache[item] = {other for other, _ in related[:config["target_neighbors"]]}
        related = candidate_neighbor_cache[item]
        direct = {owner for owner, _ in neighbors if item in tgt_history[owner]}
        indirect = {owner for owner, _ in neighbors if tgt_history[owner] & related}
        overlap = record["evidence"]["overlap"]
        assert overlap["actual_neighbors"] == len(neighbors)
        assert overlap["direct_support_users"] == len(direct)
        assert overlap["indirect_support_users"] == len(indirect), (record["pair_id"], overlap, len(indirect))
        assert overlap["union_support_users"] == len(direct | indirect)
        if neighbors:
            np.testing.assert_allclose(overlap["union_support_rate"], len(direct | indirect)/len(neighbors))
        else:
            assert overlap["union_support_rate"] is None
        checks["overlap_support_and_denominators"] += 1
        bias = record["evidence"]["popularity_bias"]
        assert bias["train_interactions"] == counts[item]
        assert bias["distinct_train_users"] == len(item_users[item])
        assert bias["visible_target_users"] == len(tgt_history)
        assert bias["local_support_users"] == len(direct) and bias["local_group_size"] == len(neighbors)
        np.testing.assert_allclose(bias["global_support_rate"], len(item_users[item])/len(tgt_history))
        assert bias["exposure_available"] is False and bias["exposure"] is None
        checks["popularity_counts_and_scope"] += 1
    result = {"state": "passed", "pairs": len(records), "users": len(profiles), "checks": dict(checks),
              "input_sha256": sha256(inputs), "bundle_sha256": bundle_hash, "hidden_target_feedback_read": False,
              "method": "independent_sets_and_counts;vector_dot_and_rank_recomputed"}
    write_json(output, result)
    print(result, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "encoder", "g", "inputs", "output"):
        parser.add_argument("--"+name, required=True, type=Path)
    args = parser.parse_args()
    audit(args.bundle, args.encoder, args.g, args.inputs, args.output)
