"""Portable, train-only input contract shared by offline evidence stages."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
from contextlib import contextmanager
from datetime import datetime, timezone

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows(path):
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    os.replace(temp, path)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, allow_nan=False).encode()).hexdigest()


def code_signature(*names):
    names = ("scripts/agent_pipeline_common.py",) + names
    return fingerprint({name: sha256(ROOT / name) for name in names})


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def save_arrays(path, **arrays):
    path = Path(path)
    with path.with_name(path.name + ".tmp").open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    os.replace(path.with_name(path.name + ".tmp"), path)


def verify_files(root, manifest):
    root = Path(root).resolve()
    for name, info in manifest["files"].items():
        path = (root / name).resolve()
        if root not in path.parents:
            raise ValueError("Manifest path escapes artifact directory")
        if not path.is_file() or path.stat().st_size != info["bytes"] or sha256(path) != info["sha256"]:
            raise ValueError("Artifact integrity check failed: " + name)


def file_records(root, names):
    return {name: {"sha256": sha256(Path(root) / name), "bytes": (Path(root) / name).stat().st_size}
            for name in names}


@contextmanager
def stage(output, kind, bundle_hash, config):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    request = {"kind": kind, "bundle_sha256": bundle_hash, "config": config}
    request_path = output / "request.json"
    if request_path.exists() and read_json(request_path) != request:
        raise ValueError("Stage inputs/configuration changed; choose a new run directory: " + str(output))
    if (output / "manifest.json").exists():
        manifest = read_json(output / "manifest.json")
        if manifest.get("state") != "complete" or manifest.get("request") != request:
            raise ValueError("Incompatible completed stage")
        verify_files(output, manifest)
        yield False
        return
    write_json(request_path, request)
    write_json(output / "status.json", {"state": "running", "started_at": utc_now()})
    try:
        yield True
        if not (output / "manifest.json").exists():
            raise RuntimeError("Stage returned without a completion manifest")
    except Exception as exc:
        write_json(output / "status.json", {"state": "failed", "error": str(exc), "updated_at": utc_now()})
        raise


def complete_stage(output, names, **details):
    output = Path(output)
    manifest = {"state": "complete", "completed_at": utc_now(), "request": read_json(output / "request.json"),
                "files": file_records(output, names), **details}
    write_json(output / "manifest.json", manifest)
    write_json(output / "status.json", {"state": "complete", "completed_at": manifest["completed_at"]})


def package_data(data_dir, output):
    """Exclude hidden feedback, full target history, raw archives and credentials."""
    import pandas as pd
    data_dir, output = Path(data_dir), Path(output)
    origin = read_json(data_dir / "manifest.json")
    if origin["state"] != "complete":
        raise ValueError("CPU preparation has not completed")
    with stage(output, "portable_bundle", sha256(data_dir / "manifest.json"), {"policy": "prompt_visible_only_v1"}) as run:
        if not run:
            return
        joint = Path(origin["benchmark_directory"])
        mapping = read_json(joint / "id_mapping.json")
        groups = read_json(data_dir / "folds/prompt/users.json")
        train_src = pd.read_pickle(joint / "train_src.pkl")
        train_tgt = pd.read_pickle(data_dir / "folds/prompt/train_tgt.pkl")
        full_users = read_json(joint / "all_users.json")
        source = train_src[["user", "item"]].to_numpy(dtype="int64")
        target = train_tgt[["user", "item"]].to_numpy(dtype="int64")
        hidden = set(groups["prompt_dev"] + groups["prompt_val"])
        support = set(groups["support"])
        if not hidden.isdisjoint(target[:, 0]) or support & hidden:
            raise ValueError("Hidden users leak into visible target training")
        if support | hidden != set(full_users["overlap_users"]):
            raise ValueError("Internal groups disagree with benchmark training overlap")
        target_users = set(target[:, 0].tolist())
        if not support.issubset(target_users):
            raise ValueError("Support users lack visible target interactions")
        for uid in support | hidden:
            if mapping["src"]["id2user"][uid] != mapping["tgt"]["id2user"][uid]:
                raise ValueError("Shared user ID is not a shared raw identity")
        cold_raw = {mapping["src"]["id2user"][uid] for key in ("valid_cold_users", "test_cold_users")
                    for uid in full_users[key]}
        if cold_raw & {mapping["tgt"]["id2user"][uid] for uid in target_users}:
            raise ValueError("Formal cold users leak into target training")
        save_arrays(output / "interactions.npz", source=source, target=target)
        write_json(output / "groups.json", groups)
        write_json(output / "id_mapping.json", mapping)
        for name, source_path in {"source_profiles.jsonl": "full/source_profiles.jsonl",
                                  "source_catalog.jsonl": "catalogs/src/item_catalog.jsonl",
                                  "target_catalog.jsonl": "catalogs/tgt/item_catalog.jsonl"}.items():
            shutil.copyfile(data_dir / source_path, output / name)
        names = ["interactions.npz", "groups.json", "id_mapping.json", "source_profiles.jsonl",
                 "source_catalog.jsonl", "target_catalog.jsonl"]
        complete_stage(output, names, schema="agent_bundle_v1", origin_manifest_sha256=sha256(data_dir / "manifest.json"),
                       counts={"source_users": len(mapping["src"]["user2id"]),
                               "target_users": len(mapping["tgt"]["user2id"]),
                               "source_items": len(mapping["src"]["item2id"]),
                               "target_items": len(mapping["tgt"]["item2id"]),
                               "source_interactions": len(source), "target_interactions": len(target)},
                       omitted=["hidden_feedback", "benchmark_evaluation", "full_target_history", "raw_files", "credentials"])


def load_bundle(path):
    path = Path(path)
    manifest = read_json(path / "manifest.json")
    if manifest.get("state") != "complete" or manifest.get("schema") != "agent_bundle_v1":
        raise ValueError("Not a completed portable agent bundle")
    verify_files(path, manifest)
    groups = read_json(path / "groups.json")
    sets = [set(groups[name]) for name in ("support", "prompt_dev", "prompt_val")]
    if any(len(groups[name]) != len(pool) for name, pool in zip(("support", "prompt_dev", "prompt_val"), sets)):
        raise ValueError("Duplicate users inside an internal group")
    if sum(map(len, sets)) != len(set.union(*sets)):
        raise ValueError("Internal groups are not disjoint")
    with np.load(path / "interactions.npz", allow_pickle=False) as arrays:
        source, target = arrays["source"], arrays["target"]
    for data, domain in ((source, "source"), (target, "target")):
        if data.ndim != 2 or data.shape[1] != 2 or not np.issubdtype(data.dtype, np.integer):
            raise ValueError("Invalid interaction array")
        if len(data) and (np.any(data <= 0) or data[:, 0].max() > manifest["counts"][domain + "_users"]
                          or data[:, 1].max() > manifest["counts"][domain + "_items"]):
            raise ValueError("Out-of-range interaction ID")
        if len(data) != manifest["counts"][domain + "_interactions"]:
            raise ValueError("Interaction count differs from manifest")
    if (sets[1] | sets[2]) & set(target[:, 0].tolist()):
        raise ValueError("Hidden target histories are visible")
    if not sets[0].issubset(set(target[:, 0].tolist())):
        raise ValueError("Support pool lacks target observations")
    mapping = read_json(path / "id_mapping.json")
    for user in set.union(*sets):
        if not 1 <= user <= min(manifest["counts"]["source_users"], manifest["counts"]["target_users"]) or mapping["src"]["id2user"][user] != mapping["tgt"]["id2user"][user]:
            raise ValueError("Shared user identity mismatch")
    return manifest, groups, source, target, sha256(path / "manifest.json")


def stable_top(scores, ids, limit):
    scores, ids = np.asarray(scores), np.asarray(ids)
    valid = np.isfinite(scores)
    scores, ids = scores[valid], ids[valid]
    order = np.lexsort((ids, -scores))[:limit]
    return [(int(ids[i]), float(scores[i])) for i in order]


def normalize(array):
    array = np.asarray(array, dtype=np.float32)
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    return np.divide(array, norms, out=np.zeros_like(array), where=norms > 0)
