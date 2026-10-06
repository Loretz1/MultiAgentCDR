"""Small, credential-free probe for an OpenAI-compatible Agent endpoint.

Run from a terminal. The API key is read without echo and never saved.
This uses synthetic evidence only; it does not produce research data.
"""

from __future__ import annotations

import argparse
import getpass
import math
import os
import re

import httpx


BASE_URL = "https://api.openlux.ai/v1"
MODEL = "gpt-5.6-luna"

COMMON = (
    "Source user preference: enjoys science-fiction films about space exploration. "
    "Target candidate: a science-fiction film about an interstellar expedition."
)
CASES = {
    "semantic": "Semantic similarity is high; matched concepts: space, exploration, science fiction.",
    "collaborative": "Train-only collaborative score is 0.78; 6 of 10 similar source users support the item.",
    "overlap": "Among 10 similar training overlap users, 7 interacted with the target item or its close neighbors.",
    "popularity_bias": "The item is in the 99th popularity percentile, but personalized support is low (1 of 10 similar users).",
}
ROLE_RULES = {
    "semantic": "Use only the semantic fit between user preference and candidate description.",
    "collaborative": "Use only the collaborative score, neighbor support, and structural evidence. Ignore semantic similarity.",
    "overlap": "Use only support from training overlap users. Ignore semantic similarity and global popularity.",
    "popularity_bias": (
        "Evaluate whether apparent support comes from popularity bias. "
        "High popularity alone never implies Strong. If personalized support is low, choose Weak or Reject. "
        "Ignore the semantic match in the common context as evidence."
    ),
}


def safe_error(response: httpx.Response, key: str) -> str:
    try:
        body = response.json()
        error = body.get("error", body) if isinstance(body, dict) else {}
        code = error.get("code") or error.get("type") or "unknown"
        message = str(error.get("message", ""))
    except (ValueError, AttributeError):
        code, message = "unknown", ""
    message = message.replace(key, "[REDACTED]")
    message = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED]", message)
    return f"HTTP {response.status_code}, code={code}, message={message[:240]}"


def label_result(text: str, token_records: list[dict]) -> dict:
    match = re.search(r"Prediction:\s*([ABC])\s*$", text)
    prediction = match.group(1) if match else None
    label_record = None
    for record in token_records:
        if str(record.get("token", "")).strip() in {"A", "B", "C"}:
            label_record = record
    scores = {}
    if label_record and prediction:
        for candidate in label_record.get("top_logprobs") or []:
            label = str(candidate.get("token", "")).strip()
            if label in {"A", "B", "C"} and isinstance(candidate.get("logprob"), (int, float)):
                scores[label] = float(candidate["logprob"])
        sampled = str(label_record.get("token", "")).strip()
        if sampled in {"A", "B", "C"} and isinstance(label_record.get("logprob"), (int, float)):
            scores[sampled] = float(label_record["logprob"])

    result = {"text": text[:400], "prediction": prediction, "found_labels": sorted(scores)}
    if label_record:
        candidates = label_record.get("top_logprobs") or []
        result["top_candidate_count"] = len(candidates)
        result["top_candidate_tokens"] = [str(item.get("token", "")) for item in candidates[:20]]
    if len(scores) == 3:
        offset = max(scores.values())
        weights = {k: math.exp(v - offset) for k, v in scores.items()}
        total = sum(weights.values())
        probabilities = {k: weights[k] / total for k in "ABC"}
        entropy = -sum(p * math.log(p) for p in probabilities.values() if p > 0)
        result["probabilities"] = probabilities
        result["confidence"] = 1 - entropy / math.log(3)
    return result


def prompt(role: str, evidence: str) -> tuple[str, str]:
    system = (
        f"You are the {role} evidence agent. Judge only your own evidence. {ROLE_RULES[role]} "
        "A=Strong evidence for a pseudo-interaction; B=Weak support; "
        "C=Reject because evidence does not support it or suggests unreliability. "
        "Return a short evidence-grounded reasoning followed by exactly one prediction token. "
        "Use precisely this format: Reasoning: one short sentence\nPrediction: <A|B|C>. "
        "Do not write anything after the prediction letter."
    )
    user = COMMON + "\nYour role's evidence: " + evidence
    return system, user


def probe_responses(client: httpx.Client, role: str, evidence: str, key: str) -> tuple[bool, dict | str]:
    system, user = prompt(role, evidence)
    payload = {
        "model": MODEL,
        "instructions": system,
        "input": user,
        "reasoning": {"effort": "none"},
        "include": ["message.output_text.logprobs"],
        "top_logprobs": 20,
        "temperature": 1,
        "max_output_tokens": 96,
    }
    response = client.post("responses", json=payload)
    if response.status_code != 200:
        return False, safe_error(response, key)
    body = response.json()
    texts, records = [], []
    for item in body.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    texts.append(part.get("text", ""))
                    records.extend(part.get("logprobs") or [])
    result = label_result("".join(texts), records)
    result["response_status"] = body.get("status")
    result["model_returned"] = body.get("model")
    result["usage"] = body.get("usage")
    result["logprob_positions"] = len(records)
    return True, result


def probe_chat(client: httpx.Client, role: str, evidence: str, key: str) -> tuple[bool, dict | str]:
    system, user = prompt(role, evidence)
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "logprobs": True,
        "top_logprobs": 20,
        "reasoning_effort": "none",
        "temperature": 1,
        "max_tokens": 96,
    }
    response = client.post("chat/completions", json=payload)
    if response.status_code != 200:
        return False, safe_error(response, key)
    body = response.json()
    choice = (body.get("choices") or [{}])[0]
    content = choice.get("message", {}).get("content") or ""
    records = (choice.get("logprobs") or {}).get("content") or []
    result = label_result(content, records)
    result["finish_reason"] = choice.get("finish_reason")
    result["model_returned"] = body.get("model")
    result["usage"] = body.get("usage")
    result["logprob_positions"] = len(records)
    return True, result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chat", action="store_true", help="Probe Chat Completions instead of Responses")
    parser.add_argument("--all", action="store_true", help="Probe all four roles (four paid calls)")
    parser.add_argument("--role", choices=CASES, default="semantic", help="Role selected for one paid call")
    args = parser.parse_args()
    key = os.environ.get("OPENAI_API_KEY") or getpass.getpass("API key (hidden): ")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    with httpx.Client(base_url=BASE_URL + "/", headers=headers, timeout=90) as client:
        try:
            models = client.get("models")
            if models.status_code == 200:
                ids = [item.get("id") for item in models.json().get("data", [])]
                print("models:", {"exact_model_listed": MODEL in ids, "listed_count": len(ids)})
            else:
                print("models:", safe_error(models, key))
            method = probe_chat if args.chat else probe_responses
            cases = CASES.items() if args.all else [(args.role, CASES[args.role])]
            for role, evidence in cases:
                success, result = method(client, role, evidence, key)
                if not args.chat and role == "semantic" and (not success or (isinstance(result, dict) and not result["logprob_positions"])):
                    print("responses/semantic:", result)
                    method = probe_chat
                    success, result = method(client, role, evidence, key)
                    print("chat/semantic:", result)
                else:
                    print(f"{method.__name__}/{role}:", result)
                if not success:
                    break
        except httpx.HTTPError as exc:
            print("transport_error:", type(exc).__name__)


if __name__ == "__main__":
    main()
