import json
from datetime import datetime
from pathlib import Path

class ConversationLogger:
    def __init__(self, log_file="logs/conversation_log.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_interaction(self, query, result_count, latency_seconds, answer_generation_status="not_attempted", generation_latency_seconds=None,
        generation_attempts=0, model_call_attempted=False, error_type=None, validation_failure_stage=None, 
        model_generation_latency_seconds=None, validation_latency_seconds=None, 
        fallback_formatting_latency_seconds=None, generation_path_latency_seconds=None, 
        error_diagnostics=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query_length": len(query) if isinstance(query, str) else None,
            "result_count": result_count,
            "latency_seconds": latency_seconds,
            "answer_generation_status": answer_generation_status,
            "generation_latency_seconds": generation_latency_seconds,
            "generation_attempts": generation_attempts,
            "model_call_attempted": model_call_attempted,
            "error_type": error_type,
            "validation_failure_stage": validation_failure_stage,
            "model_generation_latency_seconds": model_generation_latency_seconds,
            "validation_latency_seconds": validation_latency_seconds,
            "fallback_formatting_latency_seconds": fallback_formatting_latency_seconds,
            "generation_path_latency_seconds": generation_path_latency_seconds,
            "error_diagnostics": error_diagnostics,
            }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")