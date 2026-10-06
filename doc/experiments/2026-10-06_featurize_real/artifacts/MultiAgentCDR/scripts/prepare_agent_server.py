"""Build an allowlisted server archive locally, or verify its bundle on Linux."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tarfile

from agent_pipeline_common import ROOT, file_records, load_bundle, package_data, read_json, rows, sha256, verify_files, write_json
from encode_agent_text import catalog


SERVER_FILES = [
    "scripts/agent_pipeline_common.py", "scripts/encode_agent_text.py", "scripts/train_agent_g.py",
    "scripts/export_agent_evidence.py", "scripts/prepare_agent_server.py",
    "scripts/configs/cloth_sports_agent.json", "scripts/requirements-agent-evidence.txt",
    "scripts/bootstrap_agent_server.sh", "scripts/run_agent_evidence.sh",
    "scripts/README_agent_evidence.md", "scripts/collect_agent_feedback.py",
    "scripts/README_agent_feedback.md", "scripts/start_agent_vllm.sh",
    "CDRec/src/models/emcdr.py", "CDRec/src/common/abstract_recommender.py",
    "CDRec/src/common/init.py", "CDRec/src/common/loss.py"
]


def validate_content(bundle, manifest, source):
    for domain in ("source", "target"):
        catalog(Path(bundle) / (domain + "_catalog.jsonl"), manifest["counts"][domain + "_items"])
    pairs = set(map(tuple, source.tolist()))
    profile_pairs, users = set(), set()
    no_positive = 0
    for profile in rows(Path(bundle) / "source_profiles.jsonl"):
        user = profile["source_user_id"]
        if user in users or not 1 <= user <= manifest["counts"]["source_users"]:
            raise ValueError("Invalid profile identity")
        users.add(user)
        if not profile.get("candidate_blind", True) or profile.get("evidence_scope", "source_train_only") != "source_train_only":
            raise ValueError("Profile is not source-only")
        no_positive += not any(h.get("rating") is not None and h["rating"] >= 4 for h in profile["source_history"])
        for history in profile["source_history"]:
            pair = (user, history["item_id"])
            if pair not in pairs:
                raise ValueError("Profile contains a non-training source interaction")
            profile_pairs.add(pair)
    if users != set(range(1, manifest["counts"]["source_users"] + 1)) or profile_pairs != pairs:
        raise ValueError("Profiles do not reconstruct source training history")
    return {"catalog_id_coverage": True, "source_profile_train_alignment": True,
            "source_profiles": len(users), "users_without_positive_rating": no_positive}


def build(data_dir, bundle, archive):
    package_data(data_dir, bundle)
    manifest, groups, source, _, bundle_hash = load_bundle(bundle)
    content_checks = validate_content(bundle, manifest, source)
    bundle = Path(bundle)
    portable_names = ["manifest.json", "request.json", "status.json"] + list(manifest["files"])
    transfer = {"schema": "agent_server_transfer_v1", "bundle_sha256": bundle_hash,
                "code_files": file_records(ROOT, SERVER_FILES), "bundle_files": file_records(bundle, portable_names)}
    archive = Path(archive)
    archive.parent.mkdir(parents=True, exist_ok=True)
    transfer_path = archive.with_suffix(archive.suffix + ".contents.json")
    write_json(transfer_path, transfer)
    with tarfile.open(archive, "w:gz", compresslevel=6) as tar:
        for name in SERVER_FILES:
            tar.add(ROOT / name, arcname="MultiAgentCDR/" + name, recursive=False)
        for name in portable_names:
            tar.add(bundle / name, arcname="MultiAgentCDR/bundle/" + name, recursive=False)
        tar.add(transfer_path, arcname="MultiAgentCDR/transfer_manifest.json", recursive=False)
    result = {"state": "complete", "archive": str(archive.resolve()), "bytes": archive.stat().st_size,
              "sha256": sha256(archive), "bundle_sha256": bundle_hash, "counts": manifest["counts"],
              "groups": {name: len(groups[name]) for name in ("support", "prompt_dev", "prompt_val")},
              "scope": "prompt_visible_only", "content_checks": content_checks, "gpu_used": False}
    write_json(archive.with_suffix(archive.suffix + ".report.json"), result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "preflight"))
    parser.add_argument("--data-dir", type=Path, default=ROOT / "CDRec/data/agent_evidence/cloth_to_sports/v2")
    parser.add_argument("--bundle", type=Path, default=ROOT / "CDRec/data/agent_evidence/cloth_to_sports/server_bundle_v2")
    parser.add_argument("--archive", type=Path, default=ROOT / "doc/experiments/transfer/cloth_sports_server_v2.tar.gz")
    args = parser.parse_args()
    if args.command == "build":
        build(args.data_dir, args.bundle, args.archive)
    else:
        if (ROOT / "transfer_manifest.json").exists():
            transfer = read_json(ROOT / "transfer_manifest.json")
            verify_files(ROOT, {"files": transfer["code_files"]})
            verify_files(args.bundle, {"files": transfer["bundle_files"]})
        manifest, groups, source, _, digest = load_bundle(args.bundle)
        content_checks = validate_content(args.bundle, manifest, source)
        print(json.dumps({"state": "verified", "bundle_sha256": digest, "counts": manifest["counts"],
                          "groups": {key: len(groups[key]) for key in ("support", "prompt_dev", "prompt_val")},
                          "content_checks": content_checks,
                          "hidden_target_feedback_included": False}), flush=True)


if __name__ == "__main__":
    main()
