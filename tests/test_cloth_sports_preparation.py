"""Small integration checks for data preparation; no network or GPU needed."""

from __future__ import annotations

import ast
import gzip
import json
import random
import subprocess
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from logging import getLogger
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DOMAINS = ("Clothing_Shoes_and_Jewelry", "Sports_and_Outdoors")


def write_gzip_records(path: Path, records: list[dict], python_literal=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for record in records:
            handle.write((repr(record) if python_literal else json.dumps(record)) + "\n")


def make_fixture(data_root: Path) -> dict[str, list[dict]]:
    """Include low ratings, duplicate reviews, absent metadata and shared ASINs."""
    result = {}
    overlap = [f"USER{i:03d}" for i in range(30)]
    for role, domain in zip(("src", "tgt"), DOMAINS):
        raw = data_root / "Amazon2014" / domain / "raw"
        items = ["SHARED_ASIN"] + [f"{role.upper()}_ITEM{i}" for i in range(1, 5)]
        # Reverse raw user order to exercise sequence-shuffle insertion order.
        users = list(reversed(overlap)) + [f"{role.upper()}_ONLY{i}" for i in range(2)]
        reviews = [
            {
                "reviewerID": user,
                "asin": item,
                "unixReviewTime": 1000 + index,
                "overall": [1.0, 2.0, 3.0, 5.0, 4.0][index],
                "reviewText": f"{role} review {user} {item}",
                "summary": f"rating {[1, 2, 3, 5, 4][index]}",
            }
            for user in users
            for index, item in enumerate(items)
        ]
        reviews.append(dict(reviews[0]))
        result[role] = reviews
        write_gzip_records(raw / f"reviews_{domain}_5.json.gz", reviews)
        metadata = [
            {
                "asin": item,
                "title": f"Product {item}",
                "brand": "Fixture Brand",
                "description": f"Static description {item}",
                "categories": [["Clothing" if role == "src" else "Sports", "Outdoor"]],
                "related": {"also_bought": ["HELDOUT_BEHAVIOR_SENTINEL"]},
                "salesRank": {"Sports": 987654321},
            }
            for item in items[:-1]
        ]
        metadata[1].pop("title")
        write_gzip_records(raw / f"meta_{domain}.json.gz", metadata, python_literal=True)
    return result


def baseline_functions() -> dict:
    """Run the checked-in split functions as a golden reference, without torch."""
    source = ROOT / "CDRec/src/utils/check_and_prepare_dataset.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    names = {"split_users_and_reindex", "to_df", "split_interation"}
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    namespace = {"np": np, "pd": pd, "json": json, "logger": getLogger(__name__)}
    import os
    namespace["os"] = os
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), "exec"), namespace)
    processor_source = ROOT / "CDRec/src/utils/data_preprocessing/amazon_data_processor.py"
    processor_tree = ast.parse(processor_source.read_text(encoding="utf-8"))
    processor_class = next(node for node in processor_tree.body if isinstance(node, ast.ClassDef))
    method = next(node for node in processor_class.body if isinstance(node, ast.FunctionDef) and node.name == "_get_item_seqs")
    namespace.update(random=random, defaultdict=defaultdict, Dict=dict, List=list, Tuple=tuple)
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(processor_source), "exec"), namespace)
    return namespace


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class ClothSportsPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts import prepare_cloth_sports_data as preparation
        cls.preparation = preparation
        cls.temporary = tempfile.TemporaryDirectory(prefix="cloth_sports_checks_")
        cls.base = Path(cls.temporary.name)
        cls.data = cls.base / "data"
        cls.output = cls.base / "evidence"
        cls.report = cls.base / "report"
        cls.raw = make_fixture(cls.data)
        cls.audit = preparation.run_pipeline(cls.data, cls.output, cls.report)
        cls.manifest = json.loads((cls.output / "manifest.json").read_text(encoding="utf-8"))
        cls.joint = Path(cls.manifest["benchmark_directory"])

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_original_benchmark_splits_and_ids_are_identical(self):
        reference = baseline_functions()
        # Independent frozen config: the checked-in Amazon2014 partial-overlap protocol.
        config = {
            "t_cold_valid": 0.1, "t_cold_test": 0.1,
            "warm_valid_ratio": 0, "warm_test_ratio": 0,
            "shuffle_user_sequence": True, "only_overlap_users": False,
        }
        sequences = {
            role: reference["_get_item_seqs"](
                SimpleNamespace(config=config),
                [(row["reviewerID"], row["asin"], row["unixReviewTime"]) for row in rows],
            )
            for role, rows in self.raw.items()
        }
        with tempfile.TemporaryDirectory(dir=self.base) as temporary:
            users, mapping = reference["split_users_and_reindex"](config, temporary, sequences)
            frames = reference["split_interation"](config, temporary, sequences, users, mapping)
        for name, expected in (("all_users.json", users), ("id_mapping.json", mapping)):
            self.assertEqual(json.loads((self.joint / name).read_text()), expected)
        split_names = (
            "train_src", "train_tgt", "valid_cold_tgt", "test_cold_tgt",
            "valid_warm_tgt", "test_warm_tgt",
        )
        for name, expected in zip(split_names, frames):
            pd.testing.assert_frame_equal(pd.read_pickle(self.joint / f"{name}.pkl"), expected)
        self.assertEqual(self.joint.name, "WarmValid0_WarmTest0_ColdValid0.1_ColdTest0.1_shuffle")
        # Numeric equality of cold-source IDs and target-only IDs is legitimate.
        cold_uid = users["valid_cold_users"][0]
        self.assertNotEqual(mapping["src"]["id2user"][cold_uid], mapping["tgt"]["id2user"][cold_uid])
        for role, domain in zip(("src", "tgt"), DOMAINS):
            stored = self.data / "Amazon2014" / domain / "processed/all_item_seqs_shuffle.json"
            self.assertEqual(json.loads(stored.read_text()), sequences[role])

    def test_internal_target_histories_are_hidden_and_full_train_is_preserved(self):
        groups = json.loads((self.output / "folds/prompt/users.json").read_text())
        held = set(groups["prompt_dev"] + groups["prompt_val"])
        self.assertTrue(held)
        self.assertTrue(set(groups["support"]).isdisjoint(held))
        self.assertTrue(set(groups["prompt_dev"]).isdisjoint(groups["prompt_val"]))
        visible = pd.read_pickle(self.output / "folds/prompt/train_tgt.pkl")
        full = pd.read_pickle(self.joint / "train_tgt.pkl")
        self.assertTrue(held.isdisjoint(visible.user))
        self.assertTrue(held.issubset(set(full.user)))
        restored = [visible]
        for group in ("prompt_dev", "prompt_val"):
            hidden = pd.read_pickle(self.output / f"hidden_feedback/{group}.pkl")
            restored.append(hidden)
            self.assertEqual(set(hidden.user), set(groups[group]))
            records = read_jsonl(self.output / f"hidden_feedback/{group}_reviews.jsonl")
            self.assertEqual(set(row["user_id"] for row in records), set(groups[group]))
        pd.testing.assert_frame_equal(
            pd.concat(restored).sort_values(["user", "item"]).reset_index(drop=True), full
        )
        visible_reviews = read_jsonl(self.output / "folds/prompt/train_tgt_reviews.jsonl")
        self.assertTrue(held.isdisjoint(row["user_id"] for row in visible_reviews))
        for item in read_jsonl(self.output / "folds/prompt/target_popularity.jsonl"):
            subset = visible[visible.item == item["item_id"]]
            self.assertEqual(item["interaction_count"], len(subset))
            self.assertEqual(item["distinct_user_count"], subset.user.nunique())
            self.assertEqual(item["target_training_user_count"], visible.user.nunique())
        self.assertIn("hidden_feedback/", self.manifest["feedback_only_do_not_use_as_evidence"])

    def test_internal_ratios_preserve_support_and_can_reproduce_legacy_split(self):
        users = list(range(1, 3129))
        current = self.preparation.make_internal_split(users)
        self.assertEqual({key: len(value) for key, value in current.items()},
                         {"support": 2816, "prompt_dev": 156, "prompt_val": 156})
        self.assertEqual(set().union(*(set(group) for group in current.values())), set(users))
        self.assertEqual(current, self.preparation.make_internal_split(list(reversed(users))))
        self.assertNotEqual(current, self.preparation.make_internal_split(users, seed=42))
        legacy = self.preparation.make_internal_split(users, dev_ratio=0.2, val_ratio=0.2)
        self.assertEqual({key: len(value) for key, value in legacy.items()},
                         {"support": 1878, "prompt_dev": 625, "prompt_val": 625})

    def test_internal_ratios_reject_invalid_values_and_handle_tiny_datasets(self):
        for dev, val in ((0, 0.05), (-0.1, 0.05), (0.5, 0.5), (float("nan"), 0.05),
                         (0.05, float("inf"))):
            with self.subTest(dev=dev, val=val), self.assertRaises(ValueError):
                self.preparation.make_internal_split([1, 2, 3], dev, val)
        for count in (0, 1, 2):
            result = self.preparation.make_internal_split(list(range(count)))
            self.assertEqual(result, {"support": list(range(count)), "prompt_dev": [], "prompt_val": []})
        result = self.preparation.make_internal_split([1, 2, 3])
        self.assertTrue(all(len(group) == 1 for group in result.values()))

    def test_raw_ratings_text_and_duplicate_rows_survive(self):
        source = read_jsonl(self.output / "full/train_src_reviews.jsonl")
        self.assertEqual(len(source), len(self.raw["src"]))
        for row, expected in zip(source, self.raw["src"]):
            for field in ("reviewerID", "asin", "overall", "reviewText", "summary", "unixReviewTime"):
                self.assertEqual(row[field], expected[field])
            if row["overall"] <= 2:
                self.assertEqual(row["rating_group"], "negative")
        self.assertEqual(len({row["record_id"] for row in source}), len(source))
        profiles = read_jsonl(self.output / "full/source_profiles.jsonl")
        for profile in profiles:
            self.assertTrue(profile["candidate_blind"])
            self.assertEqual(profile["evidence_scope"], "source_train_only")
            self.assertGreater(profile["rating_groups"]["negative"], 0)
            self.assertTrue(all(row["record_id"].startswith("src:") for row in profile["source_history"]))
        self.assertEqual(self.audit["raw_reviews"]["src"]["duplicate_user_item_rows"], 1)
        self.assertEqual(self.audit["raw_reviews"]["tgt"]["duplicate_user_item_rows"], 1)
        self.assertEqual(self.audit["shared_asins_between_domains"], 1)

    def test_static_catalog_excludes_behavior_and_marks_missing_data(self):
        for role in ("src", "tgt"):
            catalog = read_jsonl(self.output / f"catalogs/{role}/item_catalog.jsonl")
            self.assertEqual(len(catalog), 5)
            self.assertEqual(sum(not row["metadata_found"] for row in catalog), 1)
            missing = next(row for row in catalog if not row["metadata_found"])
            self.assertEqual(missing["text"], "")
            self.assertIsNone(missing["metadata_source_line"])
            content = json.dumps(catalog)
            self.assertNotIn("related", content)
            self.assertNotIn("salesRank", content)
            self.assertNotIn("HELDOUT_BEHAVIOR_SENTINEL", content)
            self.assertEqual(self.audit["metadata"][role]["metadata_missing"], 1)
            self.assertEqual(self.audit["metadata"][role]["title_missing"], 2)

    def test_invalid_essential_review_fields_fail_explicitly(self):
        for field, bad_value in (("reviewerID", None), ("asin", ""), ("unixReviewTime", None)):
            with self.subTest(field=field):
                row = dict(self.raw["src"][0])
                row[field] = bad_value
                path = self.base / f"invalid_{field}.json.gz"
                write_gzip_records(path, [row])
                with self.assertRaises((ValueError, TypeError, KeyError)):
                    self.preparation.load_reviews(path)

    def test_runner_automatically_prepares_after_completed_download(self):
        report = self.base / "runner_report"
        output = self.base / "runner_output"
        report.mkdir()
        (report / "download_status.json").write_text(
            json.dumps({"state": "complete", "files": {}, "elapsed_seconds": 1}), encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/run_cloth_sports_local.py"),
             "--data-root", str(self.data), "--output-dir", str(output),
             "--report-dir", str(report), "--download-pid", "99999999",
             "--prompt-dev-ratio", "0.2", "--prompt-val-ratio", "0.2", "--internal-seed", "123"],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        pipeline = json.loads((report / "pipeline_status.json").read_text(encoding="utf-8"))
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(pipeline["state"], "complete")
        self.assertEqual(pipeline["preparation"]["state"], "complete")
        self.assertEqual(manifest["state"], "complete")
        self.assertTrue((report / "audit.json").exists())
        groups = json.loads((output / "folds/prompt/users.json").read_text(encoding="utf-8"))
        self.assertEqual(groups["requested_ratios"], [0.6, 0.2, 0.2])
        self.assertEqual(groups["seed"], 123)
        self.assertEqual(manifest["internal_seed"], 123)

    def test_runner_does_not_prepare_when_download_failed(self):
        report = self.base / "runner_failed_report"
        output = self.base / "runner_failed_output"
        report.mkdir()
        (report / "download_status.json").write_text(
            json.dumps({"state": "failed", "errors": ["fixture download failure"]}), encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/run_cloth_sports_local.py"),
             "--data-root", str(self.data), "--output-dir", str(output),
             "--report-dir", str(report), "--download-pid", "99999999"],
            cwd=ROOT, text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 1)
        status = json.loads((report / "pipeline_status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["state"], "failed")
        self.assertIn("fixture download failure", status["error"])
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
