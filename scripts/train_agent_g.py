"""Train the unchanged repository EMCDR using a masked portable bundle."""
from __future__ import annotations

import argparse
from collections import defaultdict
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import time

import numpy as np

from agent_pipeline_common import ROOT, code_signature, complete_stage, load_bundle, read_json, save_arrays, sha256, stage


def instantiate(counts, config):
    sys.path.insert(0, str(ROOT / "CDRec/src"))
    path = ROOT / "CDRec/src/models/emcdr.py"
    spec = importlib.util.spec_from_file_location("agent_evidence_emcdr", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    dataset = SimpleNamespace(num_users_overlap=counts["support_users"],
                              num_users_src=counts["source_users"], num_users_tgt=counts["target_users"],
                              num_items_src=counts["source_items"], num_items_tgt=counts["target_items"])
    return module.EMCDR(config, SimpleNamespace(dataset=dataset))


def negative_samples(users, seen, item_count, rng):
    samples = rng.randint(1, item_count + 1, size=len(users))
    for idx, user in enumerate(users):
        observed = seen[int(user)]
        if len(observed) >= item_count:
            raise ValueError("No unobserved negative item for this training user")
        if len(observed) > item_count // 2:
            available = [item for item in range(1, item_count + 1) if item not in observed]
            samples[idx] = available[rng.randint(len(available))]
        else:
            while int(samples[idx]) in observed:
                samples[idx] = rng.randint(1, item_count + 1)
    return samples


def train(bundle, output, config):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch
    manifest, groups, source, target, bundle_hash = load_bundle(bundle)
    settings = {**config, "baseline_sha256": sha256(ROOT / "CDRec/src/models/emcdr.py"),
                "implementation_sha256": code_signature("scripts/train_agent_g.py", "CDRec/src/models/emcdr.py",
                    "CDRec/src/common/abstract_recommender.py", "CDRec/src/common/init.py", "CDRec/src/common/loss.py")}
    for key in ("source_epochs", "target_epochs", "mapping_epochs", "batch_size", "feature_dim"):
        if config[key] <= 0:
            raise ValueError("Training configuration must be positive: " + key)
    with stage(output, "emcdr_g", bundle_hash, settings) as run:
        if not run:
            return
        output = Path(output)
        device = config["device"]
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
        seed = config["seed"]
        torch.manual_seed(seed)
        np.random.seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        torch.use_deterministic_algorithms(True)
        rng = np.random.RandomState(seed)
        counts = {**manifest["counts"], "support_users": len(groups["support"])}
        model = instantiate(counts, {**config, "loss_type": "bpr"}).to(device)
        started = time.monotonic()
        (output / "training.jsonl").write_text("", encoding="utf-8")
        for stage_id, (data, epochs, lr) in enumerate([
                (source, config["source_epochs"], config["source_lr"]),
                (target, config["target_epochs"], config["target_lr"]),
                (np.asarray(groups["support"], dtype="int64"), config["mapping_epochs"], config["mapping_lr"])]):
            model.set_train_stage(stage_id)
            model.train()
            optimizer = torch.optim.Adam((p for p in model.parameters() if p.requires_grad), lr=lr)
            seen = defaultdict(set)
            if stage_id < 2:
                for user, item in data:
                    seen[int(user)].add(int(item))
                nitems = counts["source_items" if stage_id == 0 else "target_items"]
                data = data[[len(seen[int(user)]) < nitems for user in data[:, 0]]]
            if not len(data):
                raise ValueError("Empty eligible training stage")
            for epoch in range(epochs):
                losses, weights = 0.0, 0
                for indices in np.array_split(rng.permutation(len(data)),
                                             max(1, int(np.ceil(len(data) / config["batch_size"])) )):
                    batch = data[indices]
                    if stage_id < 2:
                        negatives = negative_samples(batch[:, 0], seen, nitems, rng)
                        interaction = {"users": torch.tensor(batch[:, 0], dtype=torch.long, device=device),
                                       "pos_items": torch.tensor(batch[:, 1], dtype=torch.long, device=device),
                                       "neg_items": torch.tensor(negatives, dtype=torch.long, device=device)}
                    else:
                        interaction = {"users_overlapped": torch.tensor(batch, dtype=torch.long, device=device)}
                    optimizer.zero_grad()
                    loss = model.calculate_loss(interaction, epoch)
                    if not torch.isfinite(loss):
                        raise RuntimeError("Nonfinite EMCDR training loss")
                    loss.backward()
                    optimizer.step()
                    losses += float(loss.detach().cpu()) * len(batch)
                    weights += len(batch)
                record = {"stage": stage_id, "epoch": epoch + 1, "loss": losses / weights}
                with (output / "training.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record) + "\n")
                if epoch == 0 or (epoch + 1) % 50 == 0 or epoch + 1 == epochs:
                    print(json.dumps(record), flush=True)
        model.eval()
        with torch.no_grad():
            users = model.source_user_embedding.weight
            mapped_users = model.mapping_mlp(model.source_user_mlp(users)).cpu().numpy()
            items = model.target_item_mlp(model.target_item_embedding.weight).cpu().numpy()
        if not np.isfinite(mapped_users).all() or not np.isfinite(items).all():
            raise RuntimeError("Nonfinite exported G vectors")
        torch.save({"state_dict": model.state_dict(), "config": config, "bundle_sha256": bundle_hash}, output / "checkpoint.pt")
        save_arrays(output / "vectors.npz", mapped_users=mapped_users, target_items=items)
        complete_stage(output, ["checkpoint.pt", "vectors.npz", "training.jsonl"],
                       baseline_source_sha256=sha256(ROOT / "CDRec/src/models/emcdr.py"),
                       training_scope="all_source_train;visible_target_train;support_only_mapping",
                       selection="fixed_epochs_no_hidden_feedback", support_users=len(groups["support"]),
                       score_definition="mapped_source_user dot target_item;not_a_probability",
                       torch_version=torch.__version__, elapsed_seconds=round(time.monotonic() - started, 3))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "scripts/configs/cloth_sports_agent.json")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    config = {**read_json(args.config)["g"], "device": args.device}
    train(args.bundle, args.output, config)


if __name__ == "__main__":
    main()
