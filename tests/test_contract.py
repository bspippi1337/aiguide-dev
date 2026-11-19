"""Offline tests; no API key, billing or model responses required."""
import os
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from aiguide.core import _model_options, ask


class AiguideContractTests(TestCase):
    def test_new_model_skips_unsupported_temperature(self):
        for model in ("gpt-6.1-terra", "gpt-6.2-sol", "gpt-6.2-astra",
                      "gpt-5.6-sol"):
            self.assertNotIn("temperature", _model_options(model))
        self.assertEqual("none", _model_options("gpt-6.1-terra")["reasoning_effort"])
        self.assertNotIn("reasoning_effort", _model_options("gpt-6.2-astra"))

    def test_legacy_nonreasoning_model_retains_sampling(self):
        self.assertEqual(0.2, _model_options("gpt-4.1")["temperature"])

    def test_ask_does_not_require_key_to_be_stored(self):
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"version":1}'))]
        )
        with patch("aiguide.core.OpenAI") as client, patch(
            "aiguide.core.log_conversation"
        ) as log, patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-only"}):
            client.return_value.chat.completions.create.return_value = response
            answer, note = ask("Make an original composition")
            self.assertEqual('{"version":1}', answer)
            self.assertIsNone(note)
            kwargs = client.return_value.chat.completions.create.call_args.kwargs
            self.assertEqual("gpt-6.1-terra", kwargs["model"])
            self.assertEqual("none", kwargs["reasoning_effort"])
            self.assertNotIn("temperature", kwargs)
            log.assert_called_once()
            self.assertNotIn("sk-test-only", str(log.call_args))

    def test_explanation_is_visible_text_not_hidden_reasoning(self):
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="A short answer.\nREASONING: Visible public explanation."
            ))]
        )
        with patch("aiguide.core.OpenAI") as client, patch(
            "aiguide.core.log_conversation"
        ) as log:
            client.return_value.chat.completions.create.return_value = response
            answer, explanation = ask("Simple question", capture_reasoning=True)
            self.assertEqual("A short answer.", answer)
            self.assertEqual("Visible public explanation.", explanation)
            self.assertEqual(explanation, log.call_args.args[2])

    def test_rejects_empty_queries_without_external_calls(self):
        with patch("aiguide.core.OpenAI") as client:
            with self.assertRaises(ValueError):
                ask("")
            client.assert_not_called()
