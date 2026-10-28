import json
from datetime import datetime
from pathlib import Path

class ConversationLogger:
    def __init__(self, log_file="logs/conversation_log.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_interaction(self, query, result_count, latency_seconds, answer_generation_status="not_attempted", generation_latency_seconds=None,
        generation_attempts=0, error_type=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "result_count": result_count,
            "latency_seconds": latency_seconds,
            "answer_generation_status": answer_generation_status,
            "generation_latency_seconds": generation_latency_seconds,
            "generation_attempts": generation_attempts,
            "error_type": error_type,
            }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")