import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.conversation.conversation_logger import (ConversationLogger)

def test_log_interaction(tmp_path):
    log_file = tmp_path / "conversation_log.jsonl"
    logger = ConversationLogger(log_file=str(log_file))

    logger.log_interaction(query="foods with milk", result_count=14, latency_seconds=0.001)
    assert log_file.exists()
    lines = log_file.read_text().splitlines()
    assert len(lines) == 1
    assert "foods with milk" in lines[0]
    assert "14" in lines[0]