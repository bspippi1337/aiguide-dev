"""Aiguide request/response contract with modern OpenAI model compatibility.

Only externally visible output is loggable. Internal model reasoning is neither
available nor requested by this client.
"""
import os

from openai import OpenAI

from .config import get_template
from .logger import log_conversation


def _model_options(model):
    """Keep unsupported sampling parameters off reasoning-model requests."""
    options = {"model": model}
    if model.startswith(("gpt-6", "gpt-5", "o1", "o3", "o4")):
        options["max_completion_tokens"] = 12000
        # Do not guess model-specific reasoning_effort availability.
        # Defaults are safer than shipping unsupported model arguments.
    else:
        options["temperature"] = 0.2
    return options


def ask(query, model="gpt-6.1-terra", capture_reasoning=False):
    """Ask via the user's API key and log only the observable request/response.

    capture_reasoning requests an optional SHORT, VISIBLE explanation. It is not
    internal chain-of-thought or hidden model reasoning; that is not exposed.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a nonempty string")
    if not isinstance(model, str) or not model:
        raise ValueError("model must be a nonempty model ID")
    system = get_template().replace("{{OPPGAVE}}", query)
    user = query
    if capture_reasoning:
        user += (
            "\n\nEtter svaret, gi eventuelt en kort, offentlig forklaring "
            "på valgene dine under etiketten REASONING:. Ikke oppgi intern "
            "tankeprosess."
        )
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": user}]
    # Construct lazily so importing the library or testing it needs no API key.
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    options = _model_options(model)
    response = client.chat.completions.create(messages=messages, **options)
    content = response.choices[0].message.content
    if not isinstance(content, str) or not content:
        raise RuntimeError("Model returned no visible text")
    answer, explanation = content, None
    if capture_reasoning and "\nREASONING:" in content:
        answer, explanation = content.rsplit("\nREASONING:", 1)
        answer = answer.strip()
        explanation = explanation.strip() or None
    log_conversation(query, content, explanation, model)
    return answer, explanation
