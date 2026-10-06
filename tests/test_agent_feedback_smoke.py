"""HTTP-level smoke test for the four-agent feedback collector.

The fake server checks request/response wiring only. It does not stand in for
model quality, tokenization of Qwen, or GPU execution.
"""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from argparse import Namespace
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from scripts.collect_agent_feedback import PipelineError, ROLES, run


class FakeVLLM(BaseHTTPRequestHandler):
    calls: list[tuple[str, dict]] = []
    omit_last_label = False

    def log_message(self, *_args: object) -> None:
        pass

    def _send(self, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/v1/models":
            self._send({"data": [{"id": "mock-model"}]})
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(length))
        type(self).calls.append((self.path, body))
        if self.path == "/tokenize":
            # Deliberately character-level, so the first suffix option needs
            # two tokens and the collector must find the second valid option.
            content = body["messages"][-1]["content"]
            self._send({"tokens": [ord(char) for char in content]})
        elif self.path == "/v1/chat/completions" and body.get("logprobs"):
            ids = body["logprob_token_ids"]
            values = [-0.2, -3.0, -4.0]
            selected = 2 if type(self).omit_last_label else 3
            top = [
                {"token": f"token_id:{ids[i]}", "logprob": values[i]}
                for i in range(selected)
            ]
            self._send(
                {
                    "choices": [
                        {
                            "logprobs": {
                                "content": [
                                    {"token": f"token_id:{ids[0]}", "top_logprobs": top}
                                ]
                            }
                        }
                    ]
                }
            )
        elif self.path == "/v1/chat/completions":
            self._send(
                {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"content": "Reasoning: The supplied evidence gives some support."},
                        }
                    ]
                }
            )
        else:
            self.send_error(404)


class FeedbackSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        FakeVLLM.calls = []
        FakeVLLM.omit_last_label = False
        self.server = HTTPServer(("127.0.0.1", 0), FakeVLLM)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        example = Path(__file__).parents[1] / "scripts" / "synthetic_agent_input.jsonl"
        self.input = self.path / "input.jsonl"
        self.input.write_bytes(example.read_bytes())

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def args(self, output: str) -> Namespace:
        return Namespace(
            base_url=f"http://127.0.0.1:{self.server.server_port}/v1",
            model="mock-model",
            input=str(self.input),
            output=str(self.path / output),
            limit=1,
            timeout=5.0,
            min_label_mass=0.5,
            overwrite=False,
        )

    def test_four_agents_and_role_isolation(self) -> None:
        args = self.args("output.jsonl")
        self.assertEqual(run(args), 1)
        result = json.loads(Path(args.output).read_text(encoding="utf-8"))
        self.assertEqual(set(result["agents"]), set(ROLES))
        for agent in result["agents"].values():
            self.assertEqual(agent["prediction"], "A")
            self.assertEqual(set(agent["label_probabilities"]), {"A", "B", "C"})
            self.assertAlmostEqual(sum(agent["label_probabilities"].values()), 1.0)
            self.assertGreater(agent["label_mass"], 0.5)
        scoring = [body for path, body in FakeVLLM.calls if path.endswith("chat/completions") and body.get("logprobs")]
        self.assertEqual(len(scoring), 4)
        role_signals = {
            "semantic": "matched_concepts",
            "collaborative": "g_score",
            "overlap": "At most 3 of the 10 provide any support",
            "popularity_bias": "target_popularity_percentile",
        }
        for request in scoring:
            self.assertTrue(request["continue_final_message"])
            self.assertFalse(request["add_generation_prompt"])
            self.assertEqual(len(request["logprob_token_ids"]), 3)
            self.assertTrue(request["messages"][-1]["content"].endswith("Prediction: "))
            user_text = request["messages"][1]["content"]
            own = [role for role, signal in role_signals.items() if signal in user_text]
            self.assertEqual(len(own), 1)
            self.assertIn(f"Your {own[0]} evidence only:", user_text)

    def test_missing_label_score_fails(self) -> None:
        FakeVLLM.omit_last_label = True
        with self.assertRaisesRegex(PipelineError, "need A/B/C"):
            run(self.args("partial.jsonl"))


if __name__ == "__main__":
    unittest.main()
