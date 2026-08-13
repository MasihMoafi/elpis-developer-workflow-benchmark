#!/usr/bin/env python3
"""Small tests for the benchmark's external-agent adapters."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_task import direct_codex_config
from score import score_exact


class DirectCodexConfigTests(unittest.TestCase):
    def test_config_routes_direct_arm_to_same_openrouter_model_without_a_literal_key(self):
        config = direct_codex_config("inclusionai/ling-3.0-flash")
        self.assertIn('model = "inclusionai/ling-3.0-flash"', config)
        self.assertIn('model_provider = "openrouter"', config)
        self.assertIn('base_url = "https://openrouter.ai/api/v1"', config)
        self.assertIn('env_key = "OPENROUTER_API_KEY"', config)
        self.assertIn('wire_api = "responses"', config)
        self.assertNotIn("sk-", config)

    def test_tui_transcript_accepts_one_exact_model_line_when_prompt_was_not_echoed(self):
        task = {"expected": '{"status":"ready"}'}
        with tempfile.TemporaryDirectory() as directory:
            transcript = Path(directory) / "transcript.txt"
            transcript.write_text("assistant\n{" + '"status":"ready"' + "}\n", encoding="utf-8")
            self.assertEqual(score_exact(task, None, transcript)[0], "pass")


if __name__ == "__main__":
    unittest.main()
