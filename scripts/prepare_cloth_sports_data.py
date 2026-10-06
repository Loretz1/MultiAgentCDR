#!/usr/bin/env python3
"""Prepare reproducible CPU-only Cloth -> Sports data and evidence inputs.

This script uses the repository's actual benchmark splitting functions, loaded
through AST without importing its GPU/model dependencies. It never downloads
data, fits a model, fabricates semantic scores, or calls an LLM.
"""
from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import html
import json
import logging
import math
import os
from pathlib import Path
import random
import re
import shutil
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from types import SimpleNamespace

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = {"src": "Clothing_Shoes_and_Jewelry", "tgt": "Sports_and_Outdoors"}
CONFIG = {"t_cold_valid": 0.1, "t_cold_test": 0.1,
          "warm_valid_ratio": 0, "warm_test_ratio": 0,
          "shuffle_user_sequence": True, "only_overlap_users": False}
SPLIT_NAMES = ("train_src", "train_tgt", "valid_cold_tgt", "test_cold_tgt",
               "valid_warm_tgt", "test_warm_tgt")
SCHEMA_VERSION = "cloth_sports_cpu_v1"
LOG = logging.getLogger("cloth_sports_preparation")


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    tmp.replace(path)


def write_jsonl(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    count = 0
    with tmp.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            count += 1
    tmp.replace(path)
    return count


def sha256_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_gzip_records(path: Path):
    """Accept Amazon JSON and legacy Python literals; never use eval()."""
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    record = ast.literal_eval(line)
            except (ValueError, SyntaxError) as error:
                raise ValueError(f"Invalid record: {path.name}:{line_number}") from error
            if not isinstance(record, dict):
                raise ValueError(f"Expected an object: {path.name}:{line_number}")
            yield line_number, record
            if line_number % 100000 == 0:
                LOG.info("Read %s: %s records", path.name, f"{line_number:,}")


def numeric_rating(value):
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return None
    return rating if math.isfinite(rating) and 1 <= rating <= 5 else None


def rating_group(rating):
    if rating is None:
        return "unknown"
    if rating >= 4:
        return "positive"
    if rating <= 2:
        return "negative"
    return "neutral"


def load_reviews(path: Path):
    """Retain compact source references; full text is streamed on a later pass."""
    by_user = defaultdict(list)
    ratings, groups = Counter(), Counter()
    text_missing = summary_missing = 0
    minimum_time = maximum_time = None
    for line_number, record in read_gzip_records(path):
        user, item = record["reviewerID"], record["asin"]
        if not isinstance(user, str) or not user.strip() or not isinstance(item, str) or not item.strip():
            raise ValueError(f"Empty or invalid reviewerID/asin: {path.name}:{line_number}")
        timestamp = int(record["unixReviewTime"])
        rating = numeric_rating(record.get("overall"))
        by_user[user].append((item, timestamp, rating, line_number))
        ratings[str(rating) if rating is not None else "unknown"] += 1
        groups[rating_group(rating)] += 1
        text_missing += not isinstance(record.get("reviewText"), str) or not record.get("reviewText", "").strip()
        summary_missing += not isinstance(record.get("summary"), str) or not record.get("summary", "").strip()
        minimum_time = timestamp if minimum_time is None else min(minimum_time, timestamp)
        maximum_time = timestamp if maximum_time is None else max(maximum_time, timestamp)
    interactions = sum(map(len, by_user.values()))
    if not interactions:
        raise ValueError(f"No review records found in {path}")
    items = {record[0] for records in by_user.values() for record in records}
    duplicate_pairs = sum(len(rows) - len({row[0] for row in rows}) for rows in by_user.values())
    return dict(by_user), {"users": len(by_user), "items": len(items),
                          "interactions": interactions, "rating_counts": dict(ratings),
                          "rating_groups": dict(groups),
                          "duplicate_user_item_rows": duplicate_pairs,
                          "review_text_missing": text_missing,
                          "review_summary_missing": summary_missing,
                          "minimum_unix_review_time": minimum_time,
                          "maximum_unix_review_time": maximum_time}


def load_benchmark_functions():
    """Execute only explicitly selected local benchmark function definitions."""
    split_path = ROOT / "CDRec/src/utils/check_and_prepare_dataset.py"
    amazon_path = ROOT / "CDRec/src/utils/data_preprocessing/amazon_data_processor.py"
    selected = {"split_users_and_reindex", "to_df", "split_interation"}
    tree = ast.parse(split_path.read_text(encoding="utf-8-sig"))
    definitions = [node for node in tree.body
                   if isinstance(node, ast.FunctionDef) and node.name in selected]
    if {node.name for node in definitions} != selected:
        raise RuntimeError("The benchmark's expected splitting functions changed")
    amazon_tree = ast.parse(amazon_path.read_text(encoding="utf-8-sig"))
    amazon_class = next(node for node in amazon_tree.body
                        if isinstance(node, ast.ClassDef) and node.name == "AmazonDataProcessor")
    sequence_method = next(node for node in amazon_class.body
                           if isinstance(node, ast.FunctionDef) and node.name == "_get_item_seqs")
    sequence_method.name = "benchmark_get_item_seqs"
    namespace = {"os": os, "json": json, "np": np, "pd": pd,
                 "random": random, "defaultdict": defaultdict, "logger": LOG,
                 "List": list, "Tuple": tuple, "Dict": dict}
    module = ast.Module(body=definitions + [sequence_method], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "<local_benchmark_functions>", "exec"), namespace)
    return namespace, {str(path.relative_to(ROOT)): sha256_file(path)
                       for path in (split_path, amazon_path)}


def joint_directory(data_root: Path):
    split = (f"WarmValid{CONFIG['warm_valid_ratio']}_WarmTest{CONFIG['warm_test_ratio']}_"
             f"ColdValid{CONFIG['t_cold_valid']}_ColdTest{CONFIG['t_cold_test']}_shuffle")
    return data_root / "Amazon2014" / "+".join(DOMAINS.values()) / "all_users" / split


def publish_benchmark_file(source: Path, destination: Path):
    """Never silently replace a different pre-existing benchmark artifact."""
    if destination.exists():
        if source.suffix == ".pkl":
            pd.testing.assert_frame_equal(pd.read_pickle(source), pd.read_pickle(destination))
        else:
            if json.loads(source.read_text(encoding="utf-8")) != json.loads(destination.read_text(encoding="utf-8")):
                raise ValueError(f"Existing benchmark artifact disagrees: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    shutil.copyfile(source, temporary)
    temporary.replace(destination)


def build_benchmark(data_root: Path, output_dir: Path, reviews):
    functions, source_hashes = load_benchmark_functions()
    sequences = {}
    for role, records in reviews.items():
        compact = [(user, item, timestamp) for user, rows in records.items()
                   for item, timestamp, rating, line in rows]
        sequences[role] = functions["benchmark_get_item_seqs"](
            SimpleNamespace(config=CONFIG), compact)
    joint = joint_directory(data_root)
    joint.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="benchmark_", dir=output_dir) as temporary:
        stage = Path(temporary)
        users, mapping = functions["split_users_and_reindex"](CONFIG, str(stage), sequences)
        frames = dict(zip(SPLIT_NAMES, functions["split_interation"](
            CONFIG, str(stage), sequences, users, mapping)))
        for name in ["all_users.json", "id_mapping.json"] + [f"{name}.pkl" for name in SPLIT_NAMES]:
            publish_benchmark_file(stage / name, joint / name)
        for role, domain in DOMAINS.items():
            seq_path = stage / f"{role}_all_item_seqs_shuffle.json"
            write_json(seq_path, sequences[role])
            publish_benchmark_file(seq_path, data_root / "Amazon2014" / domain /
                                   "processed/all_item_seqs_shuffle.json")
    # IDs of domain-only users may numerically coincide; audit raw identities.
    cold_raw = {mapping["src"]["id2user"][uid]
                for key in ("valid_cold_users", "test_cold_users") for uid in users[key]}
    train_target_raw = {mapping["tgt"]["id2user"][uid]
                        for uid in frames["train_tgt"]["user"].unique()}
    assert cold_raw.isdisjoint(train_target_raw)
    assert len(frames["train_src"]) == sum(map(len, reviews["src"].values()))
    assert sum(len(frames[name]) for name in SPLIT_NAMES if name != "train_src") == sum(map(len, reviews["tgt"].values()))
    assert not len(frames["valid_warm_tgt"]) and not len(frames["test_warm_tgt"])
    for uid in users["overlap_users"]:
        assert mapping["src"]["id2user"][uid] == mapping["tgt"]["id2user"][uid]
    return users, mapping, frames, joint, source_hashes


def internal_split_ratios(dev_ratio, val_ratio):
    if not all(math.isfinite(ratio) and 0 < ratio < 1 for ratio in (dev_ratio, val_ratio)):
        raise ValueError("Prompt development and validation ratios must be finite and between 0 and 1")
    if dev_ratio + val_ratio >= 1:
        raise ValueError("Prompt development and validation ratios must leave a nonempty support pool")
    return [round(1 - dev_ratio - val_ratio, 12), dev_ratio, val_ratio]


def make_internal_split(overlap_users, dev_ratio=0.05, val_ratio=0.05, seed=999):
    internal_split_ratios(dev_ratio, val_ratio)
    shuffled = np.random.RandomState(seed).permutation(sorted(overlap_users)).tolist()
    count = len(shuffled)
    dev_size = max(1, int(count * dev_ratio)) if count >= 3 else 0
    val_size = max(1, int(count * val_ratio)) if count >= 3 else 0
    if count >= 3 and dev_size + val_size >= count:
        raise ValueError("Requested ratios cannot retain support users after rounding this tiny dataset")
    result = {"support": sorted(shuffled[dev_size + val_size:]),
              "prompt_dev": sorted(shuffled[:dev_size]),
              "prompt_val": sorted(shuffled[dev_size:dev_size + val_size])}
    assert set().union(*(set(group) for group in result.values())) == set(overlap_users)
    assert sum(map(len, result.values())) == len(overlap_users)
    return result


def clean_text(value):
    if isinstance(value, (list, tuple)):
        return " ".join(filter(None, (clean_text(item) for item in value)))
    if not isinstance(value, (str, int, float)):
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", str(value)))).strip()


def category_paths(value):
    if not isinstance(value, list):
        return []
    if value and all(isinstance(item, str) for item in value):
        value = [value]
    result = []
    for path in value:
        if isinstance(path, (list, tuple)):
            cleaned = [clean_text(item) for item in path if clean_text(item)]
            if cleaned and cleaned not in result:
                result.append(cleaned)
    return result


def load_catalog(path: Path, role: str, item_mapping, output_path: Path):
    found, duplicate_meta, raw_count = {}, 0, 0
    for line, record in read_gzip_records(path):
        raw_count += 1
        asin = str(record.get("asin", ""))
        if asin not in item_mapping:
            continue
        if asin in found:
            duplicate_meta += 1
            continue  # Deterministic first occurrence; reported, never silent.
        features = record.get("feature", record.get("features", []))
        features = features if isinstance(features, list) else [features]
        found[asin] = {"title": clean_text(record.get("title", "")),
                       "brand": clean_text(record.get("brand", "")),
                       "description": clean_text(record.get("description", "")),
                       "categories": category_paths(record.get("categories", [])),
                       "feature": [clean_text(value) for value in features if clean_text(value)],
                       "metadata_source_line": line}
    catalog = {}
    for asin, item_id in sorted(item_mapping.items(), key=lambda pair: pair[1]):
        metadata = found.get(asin, {"title": "", "brand": "", "description": "",
                                    "categories": [], "feature": [], "metadata_source_line": None})
        record = {"schema_version": SCHEMA_VERSION, "role": role, "domain": DOMAINS[role],
                  "raw_item_id": asin, "item_id": item_id, **metadata,
                  "metadata_found": asin in found}
        record["text"] = "\n".join(part for part in (
            record["title"], record["brand"],
            "; ".join(" > ".join(path) for path in record["categories"]),
            record["description"], "; ".join(record["feature"])) if part)
        catalog[asin] = record
    write_jsonl(output_path, catalog.values())
    return catalog, {"metadata_records_scanned": raw_count,
                     "retained_5core_items": len(catalog), "metadata_found": len(found),
                     "metadata_missing": len(catalog) - len(found),
                     "duplicate_relevant_metadata_rows": duplicate_meta,
                     "title_missing": sum(not item["title"] for item in catalog.values()),
                     "description_missing": sum(not item["description"] for item in catalog.values()),
                     "text_empty": sum(not item["text"] for item in catalog.values())}


def write_review_sidecars(paths, output_dir, users, mapping, internal):
    valid_raw = {mapping["src"]["id2user"][uid] for uid in users["valid_cold_users"]}
    test_raw = {mapping["src"]["id2user"][uid] for uid in users["test_cold_users"]}
    hidden_groups = {uid: name for name in ("prompt_dev", "prompt_val") for uid in internal[name]}
    destinations = {
        "train_src": output_dir / "full/train_src_reviews.jsonl",
        "train_tgt": output_dir / "full/train_tgt_reviews.jsonl",
        "valid_cold": output_dir / "benchmark_evaluation/valid_cold_reviews.jsonl",
        "test_cold": output_dir / "benchmark_evaluation/test_cold_reviews.jsonl",
        "visible_tgt": output_dir / "folds/prompt/train_tgt_reviews.jsonl",
        "prompt_dev": output_dir / "hidden_feedback/prompt_dev_reviews.jsonl",
        "prompt_val": output_dir / "hidden_feedback/prompt_val_reviews.jsonl"}
    handles, counts = {}, Counter()
    try:
        for name, path in destinations.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            handles[name] = path.with_suffix(path.suffix + ".part").open("w", encoding="utf-8")
        for role, path in paths.items():
            for line, original in read_gzip_records(path):
                raw_user, raw_item = str(original["reviewerID"]), str(original["asin"])
                id_space = role
                if role == "src":
                    splits = ["train_src"]
                elif raw_user in valid_raw:
                    splits, id_space = ["valid_cold"], "src"
                elif raw_user in test_raw:
                    splits, id_space = ["test_cold"], "src"
                else:
                    uid = mapping["tgt"]["user2id"][raw_user]
                    splits = ["train_tgt", hidden_groups.get(uid, "visible_tgt")]
                record = {**original, "record_id": f"{role}:reviews:{line}",
                          "raw_user_id": raw_user, "raw_item_id": raw_item,
                          "domain": DOMAINS[role], "role": role,
                          "user_id": mapping[id_space]["user2id"][raw_user],
                          "user_id_space": id_space,
                          "item_id": mapping[role]["item2id"][raw_item],
                          "rating_group": rating_group(numeric_rating(original.get("overall"))),
                          "raw_file": path.name, "raw_line": line}
                for split in splits:
                    handles[split].write(json.dumps({**record, "split": split}, ensure_ascii=False, allow_nan=False) + "\n")
                    counts[split] += 1
    finally:
        for handle in handles.values():
            handle.close()
    for path in destinations.values():
        path.with_suffix(path.suffix + ".part").replace(path)
    return dict(counts)


def source_profiles(reviews, mapping, catalog):
    """Candidate-blind templates use exclusively source training observations."""
    for raw_user in sorted(reviews):
        groups = Counter()
        categories = {group: Counter() for group in ("positive", "neutral", "negative", "unknown")}
        history = []
        for asin, timestamp, rating, line in reviews[raw_user]:
            group = rating_group(rating)
            groups[group] += 1
            item = catalog[asin]
            for category in sorted({path[-1] for path in item["categories"] if path}):
                categories[group][category] += 1
            history.append({"record_id": f"src:reviews:{line}", "raw_item_id": asin,
                            "item_id": mapping["item2id"][asin], "rating": rating,
                            "rating_group": group, "unix_review_time": timestamp,
                            "title": item["title"], "categories": item["categories"]})
        top = {group: [{"category": name, "review_count": count}
                       for name, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:10]]
               for group, counter in categories.items()}
        positive = "; ".join(f"{item['category']} ({item['review_count']} reviews)" for item in top["positive"])
        negative = "; ".join(f"{item['category']} ({item['review_count']} reviews)" for item in top["negative"])
        summary = (f"Observed source-domain training reviews: {len(history)}. "
                   f"Positive ratings (4-5): {groups['positive']}; neutral (above 2 and below 4): {groups['neutral']}; "
                   f"negative ratings (1-2): {groups['negative']}; unknown: {groups['unknown']}. "
                   f"Positive-rated categories: {positive or 'no available category evidence'}. "
                   f"Low-rated categories: {negative or 'no available category evidence'}. "
                   "Observed interactions alone are not interpreted as positive preference.")
        yield {"schema_version": SCHEMA_VERSION, "template_version": "rating_categories_v1",
               "source_user_id": mapping["user2id"][raw_user], "raw_user_id": raw_user,
               "domain": DOMAINS["src"], "source_preference": summary,
               "rating_groups": dict(groups), "top_categories_by_rating": top,
               "source_history": history, "evidence_scope": "source_train_only",
               "candidate_blind": True}


def write_popularity(frame, item_mapping, path: Path, scope: str):
    counts = frame.groupby("item").size().to_dict()
    distinct = frame.groupby("item")["user"].nunique().to_dict()
    num_users = int(frame["user"].nunique())
    all_ids = sorted(item_mapping.values())
    values = pd.Series([counts.get(item, 0) for item in all_ids], index=all_ids, dtype="int64")
    ranks = values.rank(method="min", ascending=False)
    percentiles = values.rank(method="max", pct=True) * 100.0
    raw_by_id = {item_id: raw for raw, item_id in item_mapping.items()}
    records = ({"item_id": item, "raw_item_id": raw_by_id[item], "scope": scope,
                "interaction_count": int(counts.get(item, 0)),
                "distinct_user_count": int(distinct.get(item, 0)),
                "target_training_user_count": num_users,
                "global_support_rate": distinct.get(item, 0) / num_users if num_users else None,
                "popularity_rank": int(ranks[item]),
                "popularity_percentile": float(percentiles[item]),
                "percentile_definition": "100 * fraction of full target catalog with interaction_count <= this item's count",
                "exposure_available": False} for item in all_ids)
    write_jsonl(path, records)
    return {"interactions": len(frame), "users": num_users,
            "observed_items": len(counts), "catalog_items": len(all_ids)}


def run_pipeline(data_root: Path, output_dir: Path, report_dir: Path,
                 prompt_dev_ratio=0.05, prompt_val_ratio=0.05, internal_seed=999):
    requested_ratios = internal_split_ratios(prompt_dev_ratio, prompt_val_ratio)
    data_root, output_dir, report_dir = (Path(path).resolve() for path in (data_root, output_dir, report_dir))
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    started, stage_start = time.monotonic(), time.monotonic()
    timings = {}
    run_time = datetime.now(timezone.utc).isoformat()
    write_json(output_dir / "status.json", {"state": "running", "started_at_utc": run_time})
    raw_paths = {role: {kind: data_root / "Amazon2014" / domain / "raw" /
                       (f"reviews_{domain}_5.json.gz" if kind == "reviews" else f"meta_{domain}.json.gz")
                       for kind in ("reviews", "metadata")} for role, domain in DOMAINS.items()}
    for role_paths in raw_paths.values():
        for path in role_paths.values():
            if not path.is_file():
                raise FileNotFoundError(f"Required raw file is missing: {path}")

    def stage_finished(name):
        nonlocal stage_start
        now = time.monotonic()
        timings[name] = round(now - stage_start, 3)
        LOG.info("Stage complete: %s (%.1f seconds)", name, now - stage_start)
        stage_start = now
        write_json(output_dir / "status.json", {"state": "running", "started_at_utc": run_time,
                   "last_completed_stage": name, "stage_seconds": timings,
                   "elapsed_seconds": round(now - started, 1)})

    LOG.info("Loading compact review records")
    reviews, audit = {}, {"schema_version": SCHEMA_VERSION, "created_at_utc": run_time,
                          "domains": DOMAINS, "config": CONFIG, "raw_reviews": {}}
    for role in DOMAINS:
        reviews[role], audit["raw_reviews"][role] = load_reviews(raw_paths[role]["reviews"])
    stage_finished("load_reviews")
    LOG.info("Building exact benchmark mappings and splits")
    users, mapping, frames, joint, source_hashes = build_benchmark(data_root, output_dir, reviews)
    internal = make_internal_split(users["overlap_users"], prompt_dev_ratio, prompt_val_ratio, internal_seed)
    hidden = set(internal["prompt_dev"] + internal["prompt_val"])
    visible = frames["train_tgt"][~frames["train_tgt"]["user"].isin(hidden)].reset_index(drop=True)
    fold_dir = output_dir / "folds/prompt"
    fold_dir.mkdir(parents=True, exist_ok=True)
    visible.to_pickle(fold_dir / "train_tgt.pkl")
    internal_config = {"seed": internal_seed, "requested_ratios": requested_ratios,
                       "actual_ratios": {name: len(group) / len(users["overlap_users"])
                                         if users["overlap_users"] else 0 for name, group in internal.items()}}
    write_json(fold_dir / "users.json", {**internal_config,
               "tiny_dataset_policy": "If fewer than three training overlap users, retain all as support; otherwise at least one user per development/validation group.",
               "user_id_space": "shared_training_overlap", **internal})
    (output_dir / "hidden_feedback").mkdir(exist_ok=True)
    for group in ("prompt_dev", "prompt_val"):
        frames["train_tgt"][frames["train_tgt"]["user"].isin(internal[group])].reset_index(drop=True).to_pickle(
            output_dir / "hidden_feedback" / f"{group}.pkl")
    assert hidden.isdisjoint(set(visible["user"]))
    assert hidden.issubset(set(users["overlap_users"]))
    assert len(visible) + sum(int(frames["train_tgt"]["user"].isin(internal[group]).sum())
                              for group in ("prompt_dev", "prompt_val")) == len(frames["train_tgt"])
    audit["benchmark_user_groups"] = {key: len(value) for key, value in users.items()}
    audit["benchmark_interactions"] = {key: len(value) for key, value in frames.items()}
    audit["internal_user_groups"] = {key: len(value) for key, value in internal.items()}
    audit["internal_split_config"] = internal_config
    audit["shared_asins_between_domains"] = len(set(mapping["src"]["item2id"]) & set(mapping["tgt"]["item2id"]))
    stage_finished("benchmark_and_internal_splits")
    LOG.info("Streaming metadata; retaining only 5-core catalog items")
    catalogs, audit["metadata"] = {}, {}
    for role in DOMAINS:
        catalogs[role], audit["metadata"][role] = load_catalog(
            raw_paths[role]["metadata"], role, mapping[role]["item2id"],
            output_dir / "catalogs" / role / "item_catalog.jsonl")
    stage_finished("static_catalogs")
    audit["review_sidecar_rows"] = write_review_sidecars(
        {role: paths["reviews"] for role, paths in raw_paths.items()}, output_dir, users, mapping, internal)
    for sidecar, frame_name in (("train_src", "train_src"), ("train_tgt", "train_tgt"),
                                ("valid_cold", "valid_cold_tgt"), ("test_cold", "test_cold_tgt")):
        assert audit["review_sidecar_rows"].get(sidecar, 0) == len(frames[frame_name])
    assert audit["review_sidecar_rows"].get("visible_tgt", 0) == len(visible)
    audit["source_profiles"] = write_jsonl(output_dir / "full/source_profiles.jsonl",
        source_profiles(reviews["src"], mapping["src"], catalogs["src"]))
    audit["popularity"] = {
        "full": write_popularity(frames["train_tgt"], mapping["tgt"]["item2id"],
                                  output_dir / "full/target_popularity.jsonl", "benchmark_train_full"),
        "prompt": write_popularity(visible, mapping["tgt"]["item2id"],
                                    fold_dir / "target_popularity.jsonl", "prompt_fold_visible_train")}
    stage_finished("sidecars_profiles_and_statistics")
    LOG.info("Hashing raw inputs and writing final audit")
    raw_manifest = {role: {kind: {"path": str(path), "size_bytes": path.stat().st_size,
                                  "sha256": sha256_file(path)} for kind, path in paths.items()}
                    for role, paths in raw_paths.items()}
    stage_finished("raw_checksums")
    audit["checks"] = {"original_benchmark_functions_used": True,
                       "benchmark_cold_raw_users_absent_from_target_train": True,
                       "all_original_review_rows_preserved": True,
                       "prompt_hidden_users_absent_from_visible_target_train": True,
                       "profiles_source_train_only_and_candidate_blind": True,
                       "metadata_behavior_fields_excluded": True,
                       "full_and_fold_popularity_computed_separately": True}
    audit["limitations"] = [
        "No semantic embeddings, G model, nearest neighbors, candidate lists, agent labels or confidence have been generated.",
        "Internal prompt groups are a single deterministic user split; no cross-fitting has run.",
        "Positive/negative ratings label source review sentiment only; benchmark interactions are unchanged.",
        "Static metadata is not timestamped; the benchmark is an offline non-temporal protocol.",
        "Hidden feedback contains observed interactions, not role-specific A/B/C gold labels.",
        "Raw single-domain IDs remain domain-specific; benchmark cold labels use source-space user IDs."]
    audit["stage_seconds"] = timings
    audit["elapsed_seconds"] = round(time.monotonic() - started, 3)
    write_json(report_dir / "audit.json", audit)
    table = ["# Cloth -> Sports local preparation audit", "", f"Created (UTC): {run_time}", "",
             "| Domain | Users | Items | Review rows | Duplicate user/item rows |",
             "|---|---:|---:|---:|---:|"]
    for role, values in audit["raw_reviews"].items():
        table.append(f"| {DOMAINS[role]} | {values['users']} | {values['items']} | {values['interactions']} | {values['duplicate_user_item_rows']} |")
    table.extend(["", "## Benchmark and internal prompt split", "",
                  f"Benchmark user groups: `{json.dumps(audit['benchmark_user_groups'])}`", "",
                  f"Benchmark interactions: `{json.dumps(audit['benchmark_interactions'])}`", "",
                  f"Internal groups: `{json.dumps(audit['internal_user_groups'])}`", "",
                  "Prompt development/validation target histories are wholly hidden from the prompt-fold training data and its popularity statistics. Source profiles use source training reviews only. Restore full benchmark training data only after prompt development is finished.", "",
                  "## Metadata", "", "```json", json.dumps(audit["metadata"], indent=2), "```", "",
                  "## Validation", ""])
    table.extend(f"- PASS: {name}" for name in audit["checks"])
    table.extend(["", "## Remaining work and limits", ""] + [f"- {note}" for note in audit["limitations"]])
    table.extend(["", "## Artifact locations", "", f"- Benchmark: `{joint}`",
                  f"- Evidence: `{output_dir}`", f"- Full details: `{report_dir / 'audit.json'}`", "",
                  f"Elapsed preprocessing time: {audit['elapsed_seconds']:.1f} seconds.", ""])
    (report_dir / "audit.md").write_text("\n".join(table), encoding="utf-8")
    manifest = {"schema_version": SCHEMA_VERSION, "state": "complete", "created_at_utc": run_time,
                "domains": DOMAINS, "benchmark_config": CONFIG, "internal_seed": internal_seed,
                "artifact_version": output_dir.name, "internal_split_config": internal_config,
                "benchmark_source_sha256": source_hashes,
                "script_sha256": sha256_file(Path(__file__)), "python_version": sys.version,
                "numpy_version": np.__version__, "pandas_version": pd.__version__,
                "raw_inputs": raw_manifest, "benchmark_directory": str(joint),
                "evidence_directory": str(output_dir), "audit_json": str(report_dir / "audit.json"),
                "prompt_fold_inputs": {"source_profiles": "full/source_profiles.jsonl",
                    "source_reviews": "full/train_src_reviews.jsonl", "target_reviews": "folds/prompt/train_tgt_reviews.jsonl",
                    "target_interactions": "folds/prompt/train_tgt.pkl", "user_groups": "folds/prompt/users.json",
                    "catalogs": ["catalogs/src/item_catalog.jsonl", "catalogs/tgt/item_catalog.jsonl"],
                    "popularity": "folds/prompt/target_popularity.jsonl"},
                "feedback_only_do_not_use_as_evidence": ["hidden_feedback/", "benchmark_evaluation/"],
                "full_training_inputs_not_for_prompt_fold": ["full/train_tgt_reviews.jsonl", "full/target_popularity.jsonl"],
                "stage_seconds": timings, "elapsed_seconds": audit["elapsed_seconds"]}
    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "status.json", {"state": "complete", "elapsed_seconds": audit["elapsed_seconds"],
                                            "manifest": str(output_dir / "manifest.json")})
    LOG.info("Preparation complete in %.1f seconds; audit: %s", audit["elapsed_seconds"], report_dir / "audit.md")
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=ROOT / "CDRec/data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "CDRec/data/agent_evidence/cloth_to_sports/v2")
    parser.add_argument("--report-dir", type=Path, default=ROOT / "doc/experiments/2026-10-06_cloth_sports_90_5_5")
    parser.add_argument("--prompt-dev-ratio", type=float, default=0.05)
    parser.add_argument("--prompt-val-ratio", type=float, default=0.05)
    parser.add_argument("--internal-seed", type=int, default=999)
    args = parser.parse_args()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(), logging.FileHandler(args.report_dir / "preparation.log", encoding="utf-8")])
    try:
        run_pipeline(args.data_root, args.output_dir, args.report_dir,
                     args.prompt_dev_ratio, args.prompt_val_ratio, args.internal_seed)
    except Exception:
        LOG.exception("Preparation failed")
        write_json(args.output_dir / "status.json", {"state": "failed", "log": str(args.report_dir / "preparation.log")})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
