
import copy
import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_INVENTORY = (PROJECT_ROOT / "data" / "inventory" / "inventory.json")
OUTPUT_DIRECTORY = PROJECT_ROOT / "data" / "synthetic"
TARGET_SIZES = [1000, 2500, 5000, 10000]
RANDOM_SEED = 42

class SyntheticDatasetGenerator:
    def __init__(self, source_path=SOURCE_INVENTORY, seed=RANDOM_SEED):
        self.source_path = Path(source_path)
        self.seed = seed

    def load_source_inventory(self):
        if not self.source_path.exists():
            raise FileNotFoundError(f"Source inventory not found: {self.source_path}")
        with self.source_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        items = data.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError("Source inventory must contain a non-empty items list.")
        self._validate_source(items)
        return items

    @staticmethod
    def _validate_source(items):
        required_fields = {
            "item_id",
            "ingredients",
            "contains_allergens",
            "may_contain",
            "nutrition",
        }
        seen_ids = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"Invalid record at index {index}.")
            missing = required_fields - item.keys()
            if missing:
                raise ValueError(f"Record at index {index} is missing fields: {missing}")
            item_id = item["item_id"]
            if not isinstance(item_id, str) or not item_id.strip():
                raise ValueError(f"Invalid item_id at index {index}.")
            if item_id in seen_ids:
                raise ValueError(f"Duplicate source ID: {item_id}")
            seen_ids.add(item_id)
            if not isinstance(item["ingredients"], list):
                raise ValueError(f"Invalid ingredients for {item_id}.")
            if not isinstance(item["contains_allergens"], list):
                raise ValueError(f"Invalid contains_allergens for {item_id}.")
            if not isinstance(item["may_contain"], list):
                raise ValueError(f"Invalid may_contain for {item_id}.")
            if not isinstance(item["nutrition"], dict):
                raise ValueError(f"Invalid nutrition for {item_id}.")

    @staticmethod
    def _create_variation(source_item, synthetic_id, rng):
        synthetic_item = copy.deepcopy(source_item)
        synthetic_item["item_id"] = synthetic_id
        varied_nutrition = {}
        for nutrient, value in source_item["nutrition"].items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                factor = rng.uniform(0.95, 1.05)
                varied_nutrition[nutrient] = round(value * factor, 2)
            else:
                varied_nutrition[nutrient] = value
        synthetic_item["nutrition"] = varied_nutrition
        return synthetic_item

    def generate_dataset(self, source_items, target_size):
        if target_size < len(source_items):
            raise ValueError(f"Target size {target_size} is smaller than the source inventory size {len(source_items)}.")

        dataset = copy.deepcopy(source_items)
        rng = random.Random(self.seed)
        synthetic_count = target_size - len(source_items)
        for index in range(synthetic_count):
            source_item = rng.choice(source_items)
            synthetic_id = f"SYN-{index + 1:06d}"
            variation = self._create_variation(source_item=source_item, synthetic_id=synthetic_id, rng=rng)
            dataset.append(variation)
        self._validate_source(dataset)
        if len(dataset) != target_size:
            raise RuntimeError("Generated dataset has an incorrect record count.")
        return dataset

    def generate_all(self):
        source_items = self.load_source_inventory()
        OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
        reports = []
        for target_size in TARGET_SIZES:
            dataset = self.generate_dataset(source_items=source_items, target_size=target_size)
            output_path = (OUTPUT_DIRECTORY / f"synthetic_inventory_{target_size}.json")
            with output_path.open("w", encoding="utf-8") as file:
                json.dump({"items": dataset}, file, indent=2, ensure_ascii=False)
            reports.append({
                "target_size": target_size,
                "original_records": len(source_items),
                "synthetic_records": target_size - len(source_items),
                "output_path": str(output_path),
            })
        return reports

def main():
    generator = SyntheticDatasetGenerator()
    reports = generator.generate_all()
    print("\nSynthetic Dataset Generation Complete")
    print("-" * 50)
    for report in reports:
        print(f"Target records:    {report['target_size']}")
        print(f"Original records:  {report['original_records']}")
        print(f"Synthetic records: {report['synthetic_records']}")
        print(f"Output:            {report['output_path']}")
        print("-" * 50)

if __name__ == "__main__":
    main()
