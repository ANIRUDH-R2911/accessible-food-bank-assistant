import json
from pathlib import Path


class EvaluationDataset:

    def __init__(self,dataset_path="data/evaluation_dataset.json"):
        self.dataset_path = Path(dataset_path)
        if not self.dataset_path.exists():
            self._create_empty_dataset()

    def _create_empty_dataset(self):
        with open(self.dataset_path, "w") as f:
            json.dump([], f, indent=4)

    def load(self):
        with open(self.dataset_path, "r") as f:
            return json.load(f)

    def save(self, records):
        with open(self.dataset_path, "w") as f:
            json.dump(records, f, indent=4)
    
    def validate_record(self, record):
        required_fields = [
            "image_name",
            "ground_truth_ocr",
            "ocr_output",
            "corrected_output",
            "expected_product",
            "predicted_product",
            "expected_ingredients",
            "predicted_ingredients",
            "expected_nutrition",
            "predicted_nutrition",
            "expected_allergens",
            "predicted_allergens"
            ]
        for field in required_fields:
            if field not in record:
                raise ValueError(f"Missing field: {field}")

    def add_record(self, record):
        self.validate_record(record)
        records = self.load()
        records.append(record)
        self.save(records)
        print("Record added successfully.")