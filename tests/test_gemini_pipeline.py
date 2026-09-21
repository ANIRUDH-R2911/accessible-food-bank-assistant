import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.pipeline.gemini_pipeline import (InventoryPipeline)

def test_batch_ingestion():
    pipeline = InventoryPipeline()
    results = (pipeline.process_directory_batched(directory="data/evaluation_images", batch_size=15, wait_seconds=60))
    print("\n")
    print("-" * 60)
    print("INGESTION SUMMARY")
    print("-" * 60)
    print(f"Processed: " f"{results['processed']}")
    print(f"Failed: " f"{results['failed']}")
    assert (results["processed"] > 0)
    print("\nPIPELINE TEST PASSED")

if __name__ == "__main__":
    test_batch_ingestion()