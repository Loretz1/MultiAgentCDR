"""Resumable pair-level scheduling of the unchanged four-evidence v4 prompts."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import time

import httpx
from agent_pipeline_common import read_json, rows, sha256, write_json
from collect_agent_feedback import (PROMPT_VERSION, ROLES, PipelineError, VLLMClient,
                                   generate_reason, score_label, validate_record)


def collect_pair(record, base_url, model, timeout, min_mass):
    started = time.monotonic()
    with VLLMClient(base_url, model, timeout) as client:
        agents = {}
        for role in ROLES:
            reason = generate_reason(client, record, role)
            agents[role] = score_label(client, record, role, reason, min_mass)
    return {"pair_id": record["pair_id"], "source_user_id": record["source_user_id"],
            "target_item_id": record["target_item_id"], "model": model, "prompt_version": PROMPT_VERSION,
            "confidence_definition": "1-H(A,B,C)/ln(3)", "agents": agents,
            "elapsed_seconds": round(time.monotonic()-started, 3)}


def run(args):
    records = [validate_record(record, n) for n, record in enumerate(rows(args.input), 1)]
    identifiers = {r["pair_id"] for r in records}
    if len(identifiers) != len(records):
        raise PipelineError("Duplicate input pair ID")
    request = {"input_sha256": sha256(args.input), "model": args.model, "prompt_version": PROMPT_VERSION,
               "workers": args.workers, "min_label_mass": args.min_label_mass,
               "collector_source_sha256":sha256(Path(__file__)),
               "prompt_source_sha256":sha256(Path(__file__).with_name('collect_agent_feedback.py')),
               "scope": "same_v4_reasoning_and_label_requests;pair_parallelism_only"}
    request_path = args.output.with_suffix(".request.json")
    if request_path.exists() and read_json(request_path) != request:
        raise PipelineError("Resume configuration/input changed")
    if args.output.exists() and not request_path.exists():
        raise PipelineError("Existing output has no resume request")
    write_json(request_path, request)
    completed = list(rows(args.output)) if args.output.exists() else []
    done = {record["pair_id"] for record in completed}
    if len(done) != len(completed) or not done.issubset(identifiers) or any(r["model"] != args.model or r["prompt_version"] != PROMPT_VERSION or set(r["agents"]) != set(ROLES) for r in completed):
        raise PipelineError("Invalid partial feedback file")
    with VLLMClient(args.base_url, args.model, args.timeout) as client:
        client.check_model()
    pending = [record for record in records if record["pair_id"] not in done]
    summary_path=args.output.with_suffix('.summary.json')
    previous=read_json(summary_path) if summary_path.exists() else {}
    if not pending and previous.get('state')=='complete':
        if previous['output_sha256']!=sha256(args.output):
            raise PipelineError('Completed output was modified')
        print('Already complete',flush=True)
        return
    failures = []
    started = time.monotonic()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8") as stream, ThreadPoolExecutor(max_workers=args.workers) as pool:
        tasks = {pool.submit(collect_pair, record, args.base_url, args.model, args.timeout, args.min_label_mass):record for record in pending}
        for task in as_completed(tasks):
            record = tasks[task]
            try:
                result = task.result()
            except Exception as exc:
                failures.append({"pair_id": record["pair_id"], "error": str(exc), "type": type(exc).__name__})
                print(json.dumps(failures[-1]), flush=True)
                continue
            stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False)+"\n")
            stream.flush()
            done.add(result["pair_id"])
            print(json.dumps({"completed":len(done),"total":len(records),"pair_id":result["pair_id"],
                              "pair_seconds":result["elapsed_seconds"],"run_seconds":round(time.monotonic()-started,2)}), flush=True)
    write_json(args.output.with_suffix(".summary.json"), {"state":"complete" if not failures else "partial",
        "request":request,"completed":len(done),"expected":len(records),"failures":failures,
        "elapsed_seconds":round(previous.get('elapsed_seconds',0)+time.monotonic()-started,3),"output_sha256":sha256(args.output),
        "output_order":"completion_order;join_by_pair_id"})
    if failures:
        raise PipelineError(str(len(failures))+" failed pairs; successful outputs retained")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--base-url",default="http://127.0.0.1:8000/v1")
    parser.add_argument("--model",default="Qwen/Qwen3-30B-A3B-Instruct-2507-FP8")
    parser.add_argument("--workers",type=int,default=4)
    parser.add_argument("--timeout",type=float,default=180)
    parser.add_argument("--min-label-mass",type=float,default=.5)
    args=parser.parse_args()
    if not 1 <= args.workers <= 4:
        parser.error("workers must be 1-4 for this pilot server")
    try: run(args)
    except (PipelineError,httpx.HTTPError) as exc: parser.exit(1,str(exc)+"\n")
