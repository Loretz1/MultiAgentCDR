"""Isolation, numeric evidence and actual CPU EMCDR integration checks."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from agent_pipeline_common import complete_stage, load_bundle, normalize, read_json, save_arrays, sha256, stage, write_json
from collect_agent_feedback import ROLES, user_prompt, validate_record
from encode_agent_text import aggregate_profiles, encode
from export_agent_evidence import Behavior, artifact_vectors, export, lexical_evidence, recall
from train_agent_g import negative_samples
from audit_real_agent_inputs import audit


def fixture(path):
    path.mkdir()
    groups = {"support": [1, 2], "prompt_dev": [3], "prompt_val": [4]}
    source = np.asarray([[1, 1], [1, 2], [2, 1], [2, 3], [3, 1], [3, 2], [4, 3], [5, 2]], dtype=np.int64)
    target = np.asarray([[1, 1], [1, 2], [2, 2], [5, 3]], dtype=np.int64)
    counts = {"source_users": 5, "target_users": 5, "source_items": 3, "target_items": 3,
              "source_interactions": len(source), "target_interactions": len(target)}
    mapping = {"src": {"id2user": [None, "shared1", "shared2", "shared3", "shared4", "source_only"]},
               "tgt": {"id2user": [None, "shared1", "shared2", "shared3", "shared4", "target_only"]}}
    profiles = []
    with stage(path, "portable_bundle", "fixture", {"fixture": True}):
        save_arrays(path / "interactions.npz", source=source, target=target)
        write_json(path / "groups.json", groups)
        write_json(path / "id_mapping.json", mapping)
        for domain in ("source", "target"):
            records = [{"item_id": item, "title": title, "brand": "", "categories": [["Sports", "Running"]],
                        "description": "", "text": title} for item, title in enumerate(("Running trail jacket", "Running trail socks", "Swimming goggles"), 1)]
            (path / (domain + "_catalog.jsonl")).write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
        for user in range(1, 6):
            history = [{"item_id": int(item), "record_id": "src:{}:{}".format(user, item),
                        "rating": 1 if user == 4 else 5, "unix_review_time": 10, "title": "Running"}
                       for owner, item in source if owner == user]
            profiles.append({"source_user_id": user, "source_preference": "Fixture source ratings only.",
                             "source_history": history, "template_version": "fixture"})
        (path / "source_profiles.jsonl").write_text("".join(json.dumps(r) + "\n" for r in profiles), encoding="utf-8")
        complete_stage(path, ["interactions.npz", "groups.json", "id_mapping.json", "source_profiles.jsonl", "source_catalog.jsonl", "target_catalog.jsonl"], schema="agent_bundle_v1", counts=counts, fixture=True)
    return profiles


def encoder_fixture(bundle, path, profiles):
    vectors = normalize([[0, 0], [1, 0], [1, 1], [0, 1]])
    users, counts = aggregate_profiles(profiles, vectors, 5)
    with stage(path, "bge_text", sha256(bundle / "manifest.json"), {"fixture": True}):
        save_arrays(path / "vectors.npz", source_items=vectors, target_items=vectors, source_users=users, positive_history_counts=counts)
        complete_stage(path, ["vectors.npz"], fixture=True)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bundle = self.root / "bundle"
        self.profiles = fixture(self.bundle)
        self.config = read_json(ROOT / "scripts/configs/cloth_sports_agent.json")["export"]

    def tearDown(self):
        self.temp.cleanup()

    def test_domain_numeric_collision_and_hidden_isolation(self):
        manifest, groups, source, target, _ = load_bundle(self.bundle)
        self.assertIn(5, source[:, 0])
        self.assertIn(5, target[:, 0])  # Distinct raw identities, intentionally allowed.
        self.assertNotIn(3, target[:, 0])
        self.assertNotIn(4, target[:, 0])
        self.assertEqual(len(groups["support"]), 2)

    def test_hidden_target_leak_fails_even_if_manifest_updated(self):
        with np.load(self.bundle / "interactions.npz") as data:
            source, target = data["source"], np.vstack((data["target"], [3, 1]))
        save_arrays(self.bundle / "interactions.npz", source=source, target=target)
        manifest = read_json(self.bundle / "manifest.json")
        manifest["counts"]["target_interactions"] += 1
        from agent_pipeline_common import file_records
        manifest["files"]["interactions.npz"] = file_records(self.bundle, ["interactions.npz"])["interactions.npz"]
        write_json(self.bundle / "manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "Hidden target"):
            load_bundle(self.bundle)

    def test_artifact_tampering_and_stale_split_rejected(self):
        path = self.root / "encoder"
        encoder_fixture(self.bundle, path, self.profiles)
        with self.assertRaisesRegex(ValueError, "different visible"):
            artifact_vectors(path, "bge_text", "another_split")
        with (path / "vectors.npz").open("ab") as stream:
            stream.write(b"tampered")
        with self.assertRaisesRegex(ValueError, "integrity"):
            artifact_vectors(path, "bge_text", sha256(self.bundle / "manifest.json"))

    def test_positive_aggregation_and_latest_negative(self):
        vectors = normalize([[0, 0], [1, 0], [0, 1], [1, 1]])
        profiles = json.loads(json.dumps(self.profiles))
        profiles[2]["source_history"].append({"item_id": 1, "record_id": "latest_negative", "rating": 1, "unix_review_time": 20})
        users, counts = aggregate_profiles(profiles, vectors, 5)
        np.testing.assert_allclose(users[3], [0, 1])
        self.assertEqual(counts[3], 1)
        np.testing.assert_array_equal(users[4], [0, 0])

    def test_encoder_contract_same_model_and_missing_text(self):
        class FixtureEncoder:
            calls = []
            def __init__(self, model, revision, device):
                self.calls.append((model, revision, device))
            def get_sentence_embedding_dimension(self):
                return 2
            def encode(self, texts, **options):
                self.calls.append((texts, options, self.max_seq_length))
                return normalize([[1, index + 1] for index in range(len(texts))])
        config = read_json(ROOT / "scripts/configs/cloth_sports_agent.json")["encoder"]
        with patch.dict(sys.modules, {"sentence_transformers": SimpleNamespace(SentenceTransformer=FixtureEncoder)}), patch("encode_agent_text.importlib.metadata.version", return_value="fixture"):
            encode(self.bundle, self.root / "encoder", config, "cpu")
        self.assertEqual(len(FixtureEncoder.calls), 3)  # One instance, two catalog calls.
        self.assertEqual(FixtureEncoder.calls[1][2], 512)
        self.assertTrue(FixtureEncoder.calls[1][1]["normalize_embeddings"])
        with np.load(self.root / "encoder/vectors.npz") as vectors:
            np.testing.assert_array_equal(vectors["source_users"][4], [0, 0])
        self.assertEqual(read_json(self.root / "encoder/manifest.json")["revision"], config["revision"])

    def test_cache_refuses_changed_config(self):
        output = self.root / "cache"
        with stage(output, "example", "split", {"seed": 999}):
            write_json(output / "example.json", {"ok": True})
            complete_stage(output, ["example.json"])
        with stage(output, "example", "split", {"seed": 999}) as should_run:
            self.assertFalse(should_run)
        with self.assertRaisesRegex(ValueError, "changed"):
            with stage(output, "example", "split", {"seed": 1000}):
                pass

    def test_support_union_denominators_and_no_neighbors(self):
        manifest, groups, source, target, _ = load_bundle(self.bundle)
        behavior = Behavior(source, target, manifest["counts"], groups["support"], self.config)
        neighbors = behavior.source_neighbors(3)
        overlap, bias = behavior.evidence(3, 2, neighbors)
        self.assertEqual(overlap["actual_neighbors"], 2)
        self.assertEqual(overlap["direct_support_users"], 2)
        self.assertEqual(overlap["union_support_users"], 2)
        self.assertEqual(overlap["union_support_rate"], 1)
        self.assertEqual(bias["visible_target_users"], 3)
        self.assertAlmostEqual(bias["global_support_rate"], 2 / 3)
        self.assertAlmostEqual(bias["smoothed_local_rate"], (2 + 10 * 2 / 3) / 12)
        self.assertFalse(bias["exposure_available"])
        overlap, bias = behavior.evidence(3, 3, [])
        self.assertIsNone(overlap["union_support_rate"])
        self.assertIsNone(bias["local_support_rate"])
        self.assertIsNone(bias["relative_support"])

    def test_negative_sampler_no_padding_no_observed_items(self):
        seen = {1: {1, 2, 3}, 2: {3}}
        users = np.asarray([1, 2] * 100)
        negatives = negative_samples(users, seen, 4, np.random.RandomState(999))
        self.assertTrue(all(item not in seen[user] and item > 0 for user, item in zip(users, negatives)))
        with self.assertRaisesRegex(ValueError, "No unobserved"):
            negative_samples([1], {1: {1, 2}}, 2, np.random.RandomState(999))

    def test_recall_ties_dedup_and_missing_semantics(self):
        config = {**self.config, "recall_per_method": 3, "candidates_per_user": 3}
        result = recall(np.asarray([0, 1, 1, 0]), np.asarray([1, 2, 3]), np.asarray([0, 1, 1, 0]), np.asarray([1, 2, 3]), config)
        self.assertEqual([item for item, _ in result], [1, 2, 3])
        result = recall(np.zeros(4), np.asarray([], dtype=int), np.asarray([0, 1, 1, 0]), np.arange(1, 4), config)
        self.assertTrue(all(set(details["sources"]) == {"g"} for _, details in result))

    def test_literal_concept_provenance(self):
        source = {1: {"title": "Trail running jacket", "categories": []}}
        result = lexical_evidence([{"item_id": 1, "record_id": "review1"}], source, {"title": "Trail running socks", "categories": []})
        terms = {record["concept"]: record for record in result["matched_concepts"]}
        self.assertEqual(terms["trail"]["source"]["record_id"], "review1")
        self.assertEqual(terms["trail"]["source"]["span"], "Trail")
        self.assertEqual(result["unmatched_concepts"][0]["concept"], "socks")

    @unittest.skipUnless(os.environ.get("AGENT_TEST_TORCH_PYTHON"), "Set AGENT_TEST_TORCH_PYTHON for actual CPU training")
    def test_actual_emcdr_cpu_to_four_role_payload(self):
        config = read_json(ROOT / "scripts/configs/cloth_sports_agent.json")
        config["g"].update(feature_dim=4, source_epochs=2, target_epochs=2, mapping_epochs=3, batch_size=2)
        write_json(self.root / "config.json", config)
        result = subprocess.run([os.environ["AGENT_TEST_TORCH_PYTHON"], str(ROOT / "scripts/train_agent_g.py"),
                                 "--bundle", str(self.bundle), "--output", str(self.root / "g"), "--config", str(self.root / "config.json"), "--device", "cpu"],
                                capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        g_manifest = read_json(self.root / "g/manifest.json")
        self.assertEqual(g_manifest["support_users"], 2)
        self.assertEqual(g_manifest["selection"], "fixed_epochs_no_hidden_feedback")
        encoder_fixture(self.bundle, self.root / "encoder", self.profiles)
        settings = {**config["export"], "candidates_per_user": 2}
        export(self.bundle, self.root / "encoder", self.root / "g", self.root / "output", settings)
        records = [json.loads(line) for line in (self.root / "output/agent_inputs.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(records), 2)
        audit(self.bundle, self.root / "encoder", self.root / "g", self.root / "output/agent_inputs.jsonl", self.root / "audit.json")
        self.assertEqual(read_json(self.root / "audit.json")["state"], "passed")
        for record in records:
            validate_record(record, 1)
            for role in ROLES:
                prompt = user_prompt(record, role)
                self.assertIn("Your " + role + " evidence only:", prompt)
                for other in set(ROLES) - {role}:
                    self.assertNotIn("Your " + other + " evidence only:", prompt)
        # Adding or changing feedback outside the allowlisted bundle cannot alter inputs.
        (self.bundle / "hidden_feedback.jsonl").write_text('{"user":3,"item":3,"secret_truth":true}\n', encoding="utf-8")
        export(self.bundle, self.root / "encoder", self.root / "g", self.root / "output2", settings)
        self.assertEqual((self.root / "output/agent_inputs.jsonl").read_bytes(), (self.root / "output2/agent_inputs.jsonl").read_bytes())
        export(self.bundle, self.root / "encoder", self.root / "g", self.root / "val", {**settings, "group": "prompt_val"})
        val_record = json.loads((self.root / "val/agent_inputs.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertIsNone(val_record["evidence"]["semantic"]["similarity"])
        self.assertEqual(set(val_record["provenance"]["retrieval"]["sources"]), {"g"})
        report_dir = os.environ.get("AGENT_TEST_REPORT_DIR")
        if report_dir:
            report = Path(report_dir)
            report.mkdir(parents=True, exist_ok=True)
            (report / "cpu_smoke.log").write_text(result.stdout + result.stderr, encoding="utf-8")
            write_json(report / "fixture_example.json", {"fixture_only": True, "not_real_BGE_or_research_results": True, "example": records[0]})
            write_json(report / "cpu_smoke_manifest.json", g_manifest)


if __name__ == "__main__":
    unittest.main()
