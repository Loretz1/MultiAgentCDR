"""Deterministic train-only recall and four role evidence, without held-out labels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import numpy as np
from scipy import sparse

from agent_pipeline_common import ROOT, code_signature, complete_stage, load_bundle, read_json, rows, sha256, stable_top, stage, verify_files
from encode_agent_text import catalog, positive_history


def artifact_vectors(path, kind, bundle_hash):
    path = Path(path)
    manifest = read_json(path / "manifest.json")
    if manifest.get("state") != "complete" or manifest["request"]["kind"] != kind:
        raise ValueError("Wrong or unfinished vector artifact")
    if manifest["request"]["bundle_sha256"] != bundle_hash:
        raise ValueError("Vectors belong to a different visible training split")
    verify_files(path, manifest)
    with np.load(path / "vectors.npz", allow_pickle=False) as arrays:
        result = {key: arrays[key] for key in arrays.files}
    if not all(np.isfinite(array).all() for array in result.values()):
        raise ValueError("Nonfinite evidence vector artifact")
    return result, sha256(path / "manifest.json")


def binary_matrix(interactions, users, items):
    matrix = sparse.csr_matrix((np.ones(len(interactions), dtype=np.float32),
                               (interactions[:, 0], interactions[:, 1])), shape=(users + 1, items + 1))
    matrix.data[:] = 1
    return matrix


def normalize_sparse(matrix):
    lengths = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel())
    inverse = np.divide(1, lengths, out=np.zeros_like(lengths), where=lengths > 0)
    return sparse.diags(inverse).dot(matrix).tocsr()


STOPWORDS = set("the a an and or for with to of in on by from new inch inches size black blue red white men mens women womens clothing shoes jewelry sports outdoors accessories international shipping available".split())


def concepts(record):
    # Literal lexical matches only: no invented synonyms or semantic equivalence.
    fields = {"title": record.get("title", ""), "brand": record.get("brand", ""),
              "category_leaf": "; ".join(path[-1] for path in record.get("categories", []) if path)}
    result = {}
    for field, text in fields.items():
        for match in re.finditer(r"[A-Za-z][A-Za-z-]{2,}", text):
            token = match.group().lower()
            if token not in STOPWORDS and token not in result:
                result[token] = {"field": field, "span": match.group()}
    return result


def lexical_evidence(history, source_catalog, candidate, limit=12):
    candidate_concepts = concepts(candidate)
    source_concepts = {}
    for record in history:
        for term, location in concepts(source_catalog[record["item_id"]]).items():
            source_concepts.setdefault(term, {**location, "source_item_id": record["item_id"],
                                            "record_id": record["record_id"]})
    matched = [{"concept": term, "match_type": "literal_token", "source": source_concepts[term],
                "target": candidate_concepts[term]} for term in sorted(candidate_concepts.keys() & source_concepts.keys())]
    unmatched = [{"concept": term, "target": candidate_concepts[term]}
                 for term in sorted(candidate_concepts.keys() - source_concepts.keys())]
    return {"matched_concepts": matched[:limit], "unmatched_concepts": unmatched[:limit],
            "matched_total": len(matched), "unmatched_total": len(unmatched), "concept_list_limit": limit,
            "unmatched_meaning": "no literal positive-history support found;not_negative_evidence"}


class Behavior:
    def __init__(self, source, target, counts, support, config):
        self.config = config
        self.support = np.asarray(sorted(support), dtype=np.int64)
        self.source = normalize_sparse(binary_matrix(source, counts["source_users"], counts["source_items"]))
        self.target = binary_matrix(target, counts["target_users"], counts["target_items"])
        self.items = normalize_sparse(self.target.T.tocsr())
        self.user_sets = {int(user): set(self.target[user].indices.tolist()) for user in self.support}
        self.nusers = len(np.unique(target[:, 0]))
        self.event_counts = np.bincount(target[:, 1], minlength=counts["target_items"] + 1)
        self.user_counts = np.asarray(self.target.sum(axis=0)).ravel().astype(int)
        self.pop_rank = {item: rank for rank, (item, _) in enumerate(
            stable_top(self.event_counts[1:], np.arange(1, counts["target_items"] + 1), counts["target_items"]), 1)}
        self.neighbor_cache = {}

    def source_neighbors(self, user):
        scores = self.source[self.support].dot(self.source[user].T).toarray().ravel()
        scores[self.support == user] = 0
        return stable_top(scores[scores > 0], self.support[scores > 0], self.config["source_neighbors"])

    def target_neighbors(self, item):
        if item not in self.neighbor_cache:
            scores = self.items.dot(self.items[item].T).toarray().ravel()
            scores[0] = scores[item] = 0
            ids = np.flatnonzero(scores > 0)
            self.neighbor_cache[item] = stable_top(scores[ids], ids, self.config["target_neighbors"])
        return self.neighbor_cache[item]

    def evidence(self, user, item, neighbors):
        target_neighbors = self.target_neighbors(item)
        related = {identifier for identifier, _ in target_neighbors}
        direct, indirect, examples = set(), set(), []
        for neighbor, weight in neighbors:
            history = self.user_sets[neighbor]
            nearby = sorted(history & related)
            if item in history:
                direct.add(neighbor)
            if nearby:
                indirect.add(neighbor)
            if item in history or nearby:
                examples.append({"support_user_id": neighbor, "source_behavior_cosine": weight,
                                 "direct_target_item_id": item if item in history else None,
                                 "observed_target_neighbor_ids": nearby[:5]})
        union = direct | indirect
        k = len(neighbors)
        total_weight = sum(weight for _, weight in neighbors)
        overlap = {"actual_neighbors": k, "requested_neighbors": self.config["source_neighbors"],
                   "direct_support_users": len(direct), "indirect_support_users": len(indirect),
                   "union_support_users": len(union), "union_support_rate": len(union) / k if k else None,
                   "weighted_union_support_rate": sum(weight for identifier, weight in neighbors if identifier in union) / total_weight if total_weight else None,
                   "target_neighbor_count": len(target_neighbors),
                   "target_neighbors": [{"item_id": identifier, "cooccurrence_cosine": score} for identifier, score in target_neighbors[:5]],
                   "support_examples": examples[:self.config["support_examples_limit"]],
                   "missing_neighbors": k == 0, "scope": "source_binary_behavior;support_only;visible_target_cooccurrence",
                   "interaction_meaning": "observed_training_interaction;not_explicit_like",
                   "denominator": "actual_positive_similarity_support_neighbors;union_deduplicated_by_user"}
        global_rate = int(self.user_counts[item]) / self.nusers if self.nusers else 0
        prior = self.config["bias_prior_strength"]
        smooth = (len(direct) + prior * global_rate) / (k + prior) if k else None
        bias = {"train_interactions": int(self.event_counts[item]), "distinct_train_users": int(self.user_counts[item]),
                "visible_target_users": self.nusers, "popularity_rank": self.pop_rank[item],
                "popularity_percentile": float(np.mean(self.event_counts[1:] <= self.event_counts[item]) * 100),
                "global_support_rate": global_rate, "local_support_users": len(direct), "local_group_size": k,
                "local_support_rate": len(direct) / k if k else None, "smoothed_local_rate": smooth,
                "relative_support": smooth / max(global_rate, 1 / max(1, self.nusers)) if smooth is not None else None,
                "prior_strength": prior, "smoothing_formula": "(local_users+prior_strength*global_rate)/(local_group_size+prior_strength)",
                "exposure_available": False, "exposure": None, "missing_neighbors": k == 0,
                "scope": "visible_target_train;local_direct_support_only;no_causal_bias_claim"}
        return overlap, bias


def rank_lookup(scores, valid_ids):
    ordered = stable_top(scores[valid_ids], valid_ids, len(valid_ids))
    return {item: rank for rank, (item, _) in enumerate(ordered, 1)}


def recall(semantic_scores, semantic_ids, g_scores, target_ids, config):
    semantic = stable_top(semantic_scores[semantic_ids], semantic_ids, config["recall_per_method"])
    collaborative = stable_top(g_scores[target_ids], target_ids, config["recall_per_method"])
    merged = {}
    for method, records in (("semantic", semantic), ("g", collaborative)):
        for rank, (item, score) in enumerate(records, 1):
            entry = merged.setdefault(item, {"rrf": 0.0, "sources": {}})
            entry["rrf"] += 1 / (config["rrf_constant"] + rank)
            entry["sources"][method] = {"score": score, "recall_rank": rank}
    return sorted(merged.items(), key=lambda pair: (-pair[1]["rrf"], pair[0]))[:config["candidates_per_user"]]


def export(bundle, encoder, g, output, config):
    manifest, groups, source, target, bundle_hash = load_bundle(bundle)
    if config["group"] not in ("prompt_dev", "prompt_val"):
        raise ValueError("Pilot export requires a hidden-history dev or validation group")
    for key in ("user_limit", "candidates_per_user", "recall_per_method", "source_neighbors", "target_neighbors", "bias_prior_strength"):
        if config[key] <= 0:
            raise ValueError("Export configuration must be positive: " + key)
    text, encoder_hash = artifact_vectors(encoder, "bge_text", bundle_hash)
    model, g_hash = artifact_vectors(g, "emcdr_g", bundle_hash)
    settings = {**config, "encoder_sha256": encoder_hash, "g_sha256": g_hash, "evidence_schema": "four_evidence_train_v1",
                "implementation_sha256": code_signature("scripts/export_agent_evidence.py", "scripts/encode_agent_text.py")}
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
                for item, retrieval in recall(semantic_scores, semantic_ids, g_scores, target_ids, config):
                    candidate = tgt_catalog[item]
                    available = user_available and bool(target_available[item])
                    history_scores = text["source_items"].dot(text["target_items"][item])
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
                                "positive_history_items": len(positive), "encoded_positive_history_items": int(text["positive_history_counts"][user]),
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
        complete_stage(output, ["agent_inputs.jsonl", "candidate_trace.jsonl"], users=selected, records=nrecords,
                       hidden_feedback_read=False, scope="prompt_visible_only", gold_candidate_insertion=False,
                       role_isolation="collector_adds_only_requested_role_evidence", tie_break="score_desc_item_id_asc")
        print(json.dumps({"users": len(selected), "pairs": nrecords, "output": str(output)}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "encoder", "g", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "scripts/configs/cloth_sports_agent.json")
    parser.add_argument("--group", choices=("prompt_dev", "prompt_val"))
    args = parser.parse_args()
    config = read_json(args.config)["export"]
    if args.group:
        config = {**config, "group": args.group}
    export(args.bundle, args.encoder, args.g, args.output, config)


if __name__ == "__main__":
    main()
