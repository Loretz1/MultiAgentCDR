"""Encode both catalogs in one BGE space; aggregate positive source reviews only."""
from __future__ import annotations

import argparse
import importlib.metadata
from pathlib import Path
import time

import numpy as np

from agent_pipeline_common import ROOT, code_signature, complete_stage, load_bundle, normalize, read_json, rows, save_arrays, stage


def catalog(path, size):
    records = {}
    for record in rows(path):
        if record["item_id"] in records:
            raise ValueError("Duplicate catalog item ID")
        records[record["item_id"]] = record
    if set(records) != set(range(1, size + 1)):
        raise ValueError("Catalog IDs are incomplete or out of range")
    return records


def positive_history(profile):
    # One contribution per item; deterministic latest-review tie breaking.
    latest = {}
    for record in profile["source_history"]:
        previous = latest.get(record["item_id"])
        if previous is None or (record.get("unix_review_time") or 0, record["record_id"]) > (
                previous.get("unix_review_time") or 0, previous["record_id"]):
            latest[record["item_id"]] = record
    return [latest[item] for item in sorted(latest)
            if latest[item].get("rating") is not None and latest[item]["rating"] >= 4]


def aggregate_profiles(profiles, item_vectors, nusers):
    vectors = np.zeros((nusers + 1, item_vectors.shape[1]), dtype=np.float32)
    counts = np.zeros(nusers + 1, dtype=np.int32)
    visited = set()
    for profile in profiles:
        user = profile["source_user_id"]
        if user in visited or not 1 <= user <= nusers:
            raise ValueError("Duplicate or invalid source profile user")
        visited.add(user)
        history = [h for h in positive_history(profile) if np.linalg.norm(item_vectors[h["item_id"]]) > 0]
        if history:
            weights = np.asarray([h["rating"] - 3 for h in history], dtype=np.float32)
            vectors[user] = np.average(item_vectors[[h["item_id"] for h in history]], axis=0, weights=weights)
            counts[user] = len(history)
    if len(visited) != nusers:
        raise ValueError("Source profiles do not cover every source user")
    return normalize(vectors), counts


def encode(bundle, output, config, device):
    from sentence_transformers import SentenceTransformer
    manifest, _, _, _, bundle_hash = load_bundle(bundle)
    if config["revision"] in ("main", "master"):
        raise ValueError("Freeze an immutable encoder revision first")
    settings = {**config, "device": device, "aggregation": "latest_positive_rating_minus_3_v1",
                "implementation_sha256": code_signature("scripts/encode_agent_text.py")}
    with stage(output, "bge_text", bundle_hash, settings) as run:
        if not run:
            return
        started = time.monotonic()
        model = SentenceTransformer(config["model"], revision=config["revision"], device=device)
        model.max_seq_length = config["max_seq_length"]
        dim = model.get_sentence_embedding_dimension()
        encoded = {}
        for domain in ("source", "target"):
            nitems = manifest["counts"][domain + "_items"]
            records = catalog(Path(bundle) / (domain + "_catalog.jsonl"), nitems)
            ids = [item for item in sorted(records) if records[item]["text"].strip()]
            vectors = np.zeros((nitems + 1, dim), dtype=np.float32)
            if ids:
                vectors[ids] = model.encode([records[item]["text"] for item in ids],
                                           batch_size=config["batch_size"], show_progress_bar=True,
                                           normalize_embeddings=True, convert_to_numpy=True)
            if not np.isfinite(vectors).all():
                raise ValueError("Nonfinite encoder output")
            encoded[domain + "_items"] = vectors
        encoded["source_users"], encoded["positive_history_counts"] = aggregate_profiles(
            rows(Path(bundle) / "source_profiles.jsonl"), encoded["source_items"], manifest["counts"]["source_users"])
        save_arrays(Path(output) / "vectors.npz", **encoded)
        complete_stage(output, ["vectors.npz"], dimension=dim, model=config["model"], revision=config["revision"],
                       normalization="L2;missing_or_no_positive_history=zero", prompt="none;symmetric_catalog_comparison",
                       text_policy="title+brand+categories+feature+description;token_truncation_at_max_seq_length",
                       versions={name: importlib.metadata.version(name) for name in ("torch", "sentence-transformers", "transformers")},
                       elapsed_seconds=round(time.monotonic() - started, 3))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "scripts/configs/cloth_sports_agent.json")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    encode(args.bundle, args.output, read_json(args.config)["encoder"], args.device)


if __name__ == "__main__":
    main()
