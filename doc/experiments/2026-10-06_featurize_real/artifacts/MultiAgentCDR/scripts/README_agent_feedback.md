# Four evidence Agent feedback probe

`collect_agent_feedback.py` sends each candidate pair to four role prompts backed by one local vLLM model. It returns one short `reasoning`, `prediction` (A/B/C), and entropy `confidence` per role. This is a feedback-link probe; it does not recall candidates, compute evidence, select pseudo-interactions, or evaluate CDRec.

## Input

UTF-8 JSONL with one object per candidate pair:

```json
{
  "pair_id": "unique_pair_1",
  "source_user_id": "optional_source_id",
  "target_item_id": "optional_target_id",
  "source_preference": "Text summary of the source-side user preference",
  "candidate_description": "Text summary of the target candidate",
  "evidence": {
    "semantic": "Semantic similarity and matched or unmatched concepts",
    "collaborative": "Train-only G score, neighbor support, structural statistics",
    "overlap": "Train-only related overlap users' target behavior",
    "popularity_bias": "Target popularity, exposure, and personalized support"
  }
}
```

Each evidence value can also be a nonempty JSON object or list. The script passes each role only the shared pair context and its own evidence. Upstream data preparation must ensure that evidence and summaries cannot contain validation or test outcomes. A synthetic example is in `synthetic_agent_input.jsonl`.

## Run

Serve the same frozen model for all four roles. Use a recent vLLM version with `/tokenize`, `continue_final_message`, `logprob_token_ids`, and `return_tokens_as_token_ids`. Keep the server's default `raw_logprobs` mode. Do not apply guided decoding, allowed token IDs, logit bias, or other score-changing processors to the scoring request.

Start the project server in one terminal (after setting `MODEL_PATH` and `VLLM_BIN` if their defaults differ):

```bash
bash scripts/start_agent_vllm.sh
```

Then run the one-pair synthetic probe in another terminal:

```bash
python scripts/collect_agent_feedback.py \
  --base-url http://127.0.0.1:8000/v1 \
  --model Qwen/Qwen3-30B-A3B-Instruct-2507-FP8 \
  --input scripts/synthetic_agent_input.jsonl \
  --output /tmp/synthetic_agent_feedback.jsonl \
  --limit 1
```

The model ID must exactly match `/v1/models`. If the server has an API key, set `VLLM_API_KEY` in the environment. The script validates the **actual rendered chat prefix** with `/tokenize` to ensure A/B/C each corresponds to a distinct single next token, then explicitly requests all three token log probabilities at that position. Missing scores or incompatible tokenization cause an error instead of a guessed confidence.

`confidence = 1 - H(p_A,p_B,p_C)/ln(3)` where `p` is the softmax over the three returned label log probabilities. `label_mass` is the sum of the three raw probabilities across the full vocabulary; the output sets `low_label_mass` when it is below `--min-label-mass` (default 0.5). A high entropy confidence is **not** a calibrated probability that the label is correct. Review reasoning quality and label mass before using feedback as supervision.

The output JSONL contains one object per pair, with four entries under `agents`. The script refuses to overwrite an existing output file unless `--overwrite` is supplied. It writes completed lines as it proceeds; if a later pair fails, earlier output lines remain and the process exits with an error.
