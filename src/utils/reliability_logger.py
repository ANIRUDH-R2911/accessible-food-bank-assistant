import json
from pathlib import Path
from datetime import datetime

class ReliabilityLogger:
    def __init__(self, log_file="logs/extraction_log.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, image_path, model_used, success, fallback_triggered):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "image_path": str(image_path),
            "model_used": model_used,
            "success": success,
            "fallback_triggered": fallback_triggered
        }

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry))
            f.write("\n")