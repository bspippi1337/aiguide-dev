import os
from openai import OpenAI
from .config import get_template
from .logger import log_conversation

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask(query, model="gpt-4", capture_reasoning=True):
    system = get_template().replace("{{OPPGAVE}}", query)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": query}]
    if capture_reasoning and "gpt-4" in model:
        messages[1]["content"] = query + "\n\nVennligst inkluder en kort 'REASONING:'-blokk før svaret."
    resp = client.chat.completions.create(model=model, messages=messages, temperature=0.2)
    content = resp.choices[0].message.content
    reasoning = None
    if capture_reasoning and "REASONING:" in content:
        parts = content.split("REASONING:", 1)
        reasoning = parts[1].split("\n\n", 1)[0] if len(parts) > 1 else None
        answer = parts[1].split("\n\n", 1)[1] if len(parts) > 1 else content
    else:
        answer = content
    log_conversation(query, content, reasoning, model)
    return answer, reasoning
