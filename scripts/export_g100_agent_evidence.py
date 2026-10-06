"""Independent G-only Top100 export; reuse frozen vectors and train-only evidence.

No hidden target feedback is read. Internal validation users are never exported.
The original baseline and exporter remain unchanged. History dot products are
restricted to the current user's source history, preserving evidence values.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from agent_pipeline_common import ROOT, code_signature, complete_stage, load_bundle, read_json, rows, stable_top, stage
from encode_agent_text import catalog, positive_history
from export_agent_evidence import artifact_vectors, Behavior, rank_lookup, lexical_evidence


def g_candidates(g_scores, target_ids, config):
    return [(item, {"method": "g_only_top100", "sources": {"g": {"score": score, "recall_rank": rank}}})
            for rank, (item, score) in enumerate(stable_top(g_scores[target_ids], target_ids, config["candidates_per_user"]), 1)]


def export_g100(bundle, encoder, g, output, config):
    manifest, groups, source, target, bundle_hash = load_bundle(bundle)
    if config["group"] not in ("prompt_dev",):
        raise ValueError("This experiment exports development users only; validation stays untouched")
    for key in ("user_limit", "candidates_per_user", "recall_per_method", "source_neighbors", "target_neighbors", "bias_prior_strength"):
        if config[key] <= 0:
            raise ValueError("Export configuration must be positive: " + key)
    text, encoder_hash = artifact_vectors(encoder, "bge_text", bundle_hash)
    model, g_hash = artifact_vectors(g, "emcdr_g", bundle_hash)
    settings = {**config, "encoder_sha256": encoder_hash, "g_sha256": g_hash, "evidence_schema": "four_evidence_g100_v1", "retrieval_method": "g_only_top100",
                "implementation_sha256": code_signature("scripts/export_g100_agent_evidence.py", "scripts/export_agent_evidence.py", "scripts/encode_agent_text.py")}
    with stage(output, "agent_inputs", bundle_hash, settings) as run:
        if not run:
            return
        counts = manifest["counts"]
        for key, size in (("source_items", counts["source_items"]), ("target_items", counts["target_items"]), ("source_users", counts["source_users"])):
            if text[key].ndim != 2 or text[key].shape[0] != size + 1:
                raise ValueError("Encoder array shape disagrees with ID mapping")
            norms = np.linalg.norm(text[key], axis=1)
            if not np.all((norms < 1e-6) | (np.abs(norms - 1) < 1e-4)):
                raise ValueError("Semantic vectors must be L2 normalized or missing")
        if len({text[key].shape[1] for key in ("source_items", "target_items", "source_users")}) != 1:
            raise ValueError("Semantic vectors use different spaces")
        if model["mapped_users"].shape[0] != counts["source_users"] + 1 or model["target_items"].shape[0] != counts["target_items"] + 1 or model["mapped_users"].shape[1] != model["target_items"].shape[1]:
            raise ValueError("G vector dimensions disagree with ID mapping")
        src_catalog = catalog(Path(bundle) / "source_catalog.jsonl", counts["source_items"])
        tgt_catalog = catalog(Path(bundle) / "target_catalog.jsonl", counts["target_items"])
        selected = np.asarray(sorted(groups[config["group"]]), dtype=np.int64)
        selected = sorted(np.random.RandomState(config["seed"]).permutation(selected)[:config["user_limit"]].tolist())
        profiles = {p["source_user_id"]: p for p in rows(Path(bundle) / "source_profiles.jsonl") if p["source_user_id"] in selected}
        behavior = Behavior(source, target, counts, groups["support"], config)
        target_ids = np.arange(1, counts["target_items"] + 1)
        target_available = np.linalg.norm(text["target_items"], axis=1) > 0
        semantic_target_ids = target_ids[target_available[target_ids]]
        output = Path(output)
        nrecords = 0
        with (output / "agent_inputs.jsonl").open("w", encoding="utf-8") as stream, (output / "candidate_trace.jsonl").open("w", encoding="utf-8") as trace:
            for user in selected:
                profile = profiles[user]
                positive = positive_history(profile)
                user_available = bool(np.linalg.norm(text["source_users"][user]) > 0)
                semantic_scores = text["target_items"].dot(text["source_users"][user])
                semantic_ids = semantic_target_ids if user_available else np.asarray([], dtype=np.int64)
                g_scores = model["target_items"].dot(model["mapped_users"][user])
                sranks = rank_lookup(semantic_scores, semantic_ids)
                granks = rank_lookup(g_scores, target_ids)
                neighbors = behavior.source_neighbors(user)
                for item, retrieval in g_candidates(g_scores, target_ids, config):
                    candidate = tgt_catalog[item]
                    available = user_available and bool(target_available[item])
                    # Only this user's history is needed; avoid a full source-catalog dot per pair.
                    history_ids = np.asarray(sorted({h["item_id"] for h in profile["source_history"]}), dtype=np.int64)
                    history_scores = np.zeros(counts["source_items"] + 1, dtype=np.float32)
                    history_scores[history_ids] = text["source_items"][history_ids].dot(text["target_items"][item])
                    positive_ids = {h["item_id"] for h in positive if np.linalg.norm(text["source_items"][h["item_id"]]) > 0}
                    relevant = stable_top(history_scores[list(sorted(positive_ids))], sorted(positive_ids), config["history_evidence_limit"]) if target_available[item] else []
                    by_item = {h["item_id"]: h for h in positive}
                    negative = [h for h in profile["source_history"] if h.get("rating") is not None and h["rating"] <= 2]
                    negative_by_item = {h["item_id"]: h for h in negative}
                    negative_ids = sorted(negative_by_item)
                    negative_top = stable_top(history_scores[negative_ids], negative_ids, 3) if target_available[item] else []
                    semantic = {"similarity": float(semantic_scores[item]) if available else None,
                                "rank": sranks.get(item), "ranking_items": len(semantic_ids),
                                "score_definition": "L2 positive_source_profile dot L2 target_text;not_probability",
                                "positive_history_items": len(positive), "positive_rating_average": float(np.mean([h["rating"] for h in positive])) if positive else None, "encoded_positive_history_items": int(text["positive_history_counts"][user]),
                                "related_positive_history": [{"source_item_id": hid, "record_id": by_item[hid]["record_id"], "rating": by_item[hid]["rating"], "title": src_catalog[hid]["title"][:220], "similarity": score} for hid, score in relevant],
                                "related_negative_history": [{"source_item_id": hid, "record_id": negative_by_item[hid]["record_id"], "rating": negative_by_item[hid]["rating"], "title": src_catalog[hid]["title"][:220], "similarity": score} for hid, score in negative_top],
                                "missing_source_preference_vector": not user_available, "missing_target_text_vector": not bool(target_available[item]),
                                "missing_target_description": not bool(candidate.get("description")),
                                **lexical_evidence(positive, src_catalog, candidate)}
                    overlap, bias = behavior.evidence(user, item, neighbors)
                    collaborative = {"g_raw": float(g_scores[item]), "rank": granks[item], "ranking_items": len(target_ids),
                                     "rank_percentile": (len(target_ids) - granks[item]) / max(1, len(target_ids) - 1) * 100,
                                     "source_history_length": len(profile["source_history"]), "mapping_support_users": len(groups["support"]),
                                     "candidate_visible_train_users": int(behavior.user_counts[item]),
                                     "score_definition": "frozen_EMCDR_mapped_source_user_dot_target_item;not_probability",
                                     "missing_visible_target_support": bool(behavior.user_counts[item] == 0)}
                    pair_id = "cloth_sports:{}:{}:{}".format(config["group"], user, item)
                    record = {"pair_id": pair_id, "source_user_id": user, "target_item_id": item,
                              "source_preference": profile["source_preference"][:1400],
                              "candidate_description": candidate["text"][:1000] or "No static target metadata available.",
                              "evidence": {"semantic": semantic, "collaborative": collaborative, "overlap": overlap, "popularity_bias": bias},
                              "provenance": {"bundle_sha256": bundle_hash, "encoder_sha256": encoder_hash, "g_sha256": g_hash,
                                             "group": config["group"], "source_profile_template": profile.get("template_version"),
                                             "context_char_limits": {"source": 1400, "candidate": 1000}, "retrieval": retrieval}}
                    stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                    trace.write(json.dumps({"pair_id": pair_id, "source_user_id": user, "target_item_id": item, **retrieval}, allow_nan=False) + "\n")
                    nrecords += 1
                print(json.dumps({"user_id": user, "pairs_done": nrecords, "expected_pairs": len(selected)*config["candidates_per_user"]}), flush=True)
        complete_stage(output, ["agent_inputs.jsonl", "candidate_trace.jsonl"], users=selected, records=nrecords,
                       hidden_feedback_read=False, scope="prompt_visible_only", gold_candidate_insertion=False,
                       role_isolation="collector_adds_only_requested_role_evidence", tie_break="score_desc_item_id_asc")
        print(json.dumps({"users": len(selected), "pairs": nrecords, "output": str(output)}), flush=True)

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "encoder", "g", "output"):
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    config=read_json(ROOT/"scripts/configs/cloth_sports_agent.json")["export"]
    config={**config,"group":"prompt_dev","user_limit":156,"candidates_per_user":100,"recall_per_method":100}
    export_g100(args.bundle,args.encoder,args.g,args.output,config)
