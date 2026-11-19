import unittest
from types import SimpleNamespace
from unittest.mock import patch

from aiguide import core


class AiguideModernApiContract(unittest.TestCase):
    def test_reasoning_models_have_no_sampling_temperature(self):
        for model in ("gpt-6.1-terra", "gpt-6.1-sol", "gpt-6-luna",
                      "gpt-5", "o3", "o4-mini"):
            options = core._model_options(model)
            self.assertNotIn("temperature", options)
            self.assertEqual(model, options["model"])
            self.assertTrue(options["max_completion_tokens"] >= 12000)

    def test_legacy_sampling_remains_supported(self):
        options = core._model_options("gpt-4o-mini")
        self.assertEqual(0.2, options["temperature"])
        self.assertNotIn("reasoning_effort", options)

    def test_ask_returns_visible_answer_and_logs_only_visible_data(self):
        fake = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="Art output from the model"
            ))]
        )
        with patch.object(core, "OpenAI") as constructor, \
             patch.object(core, "log_conversation") as log:
            constructor.return_value.chat.completions.create.return_value = fake
            answer, reasoning = core.ask("Create an unusual scene",
                                         model="gpt-6.1-terra")
            self.assertEqual("Art output from the model", answer)
            self.assertIsNone(reasoning)
            kwargs = constructor.return_value.chat.completions.create.call_args.kwargs
            self.assertNotIn("temperature", kwargs)
            self.assertEqual("gpt-6.1-terra", kwargs["model"])
            self.assertEqual("system", kwargs["messages"][0]["role"])
            self.assertEqual("user", kwargs["messages"][1]["role"])
            log.assert_called_once_with(
                "Create an unusual scene", "Art output from the model",
                None, "gpt-6.1-terra"
            )

    def test_visible_explanation_must_be_explicitly_enabled(self):
        fake = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(
                content="Visible result\nREASONING: Public short explanation."
            ))]
        )
        with patch.object(core, "OpenAI") as constructor, \
             patch.object(core, "log_conversation") as log:
            constructor.return_value.chat.completions.create.return_value = fake
            answer, explanation = core.ask(
                "Test", model="gpt-6.1-terra", capture_reasoning=True
            )
            self.assertEqual("Visible result", answer)
            self.assertEqual("Public short explanation.", explanation)
            log.assert_called_once()

    def test_missing_visible_output_is_an_error_not_a_false_success(self):
        fake = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
        )
        with patch.object(core, "OpenAI") as constructor, \
             patch.object(core, "log_conversation") as log:
            constructor.return_value.chat.completions.create.return_value = fake
            with self.assertRaisesRegex(RuntimeError, "visible text"):
                core.ask("Test")
            log.assert_not_called()

    def test_empty_prompt_rejected_before_any_network_request(self):
        with patch.object(core, "OpenAI") as constructor:
            with self.assertRaises(ValueError):
                core.ask(" ")
            constructor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
