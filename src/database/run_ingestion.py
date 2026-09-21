from src.pipeline.gemini_pipeline import (InventoryPipeline)

pipeline = InventoryPipeline()

results = pipeline.process_directory_batched(directory="data/evaluation_images", batch_size=15, wait_seconds=60)

print("\n")
print("-" * 60)
print("FINAL INGESTION SUMMARY")
print("-" * 60)

print(f"Processed: " f"{results['processed']}")

print(f"Failed: " f"{results['failed']}")