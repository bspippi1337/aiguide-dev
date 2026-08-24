import json
from datetime import datetime
from pathlib import Path
LOG_DIR = Path.home() / ".aiguide_logs"
LOG_DIR.mkdir(exist_ok=True)
def log_conversation(user_msg, assistant_msg, reasoning=None, model=None):
    entry = {"timestamp": datetime.utcnow().isoformat(), "user": user_msg, "assistant": assistant_msg, "reasoning": reasoning, "model": model}
    log_file = LOG_DIR / f"{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
