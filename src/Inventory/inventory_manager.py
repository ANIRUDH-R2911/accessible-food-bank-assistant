import json
from pathlib import Path
from typing import Dict, List, Optional


class InventoryManager:
    def __init__(self, db_path: str = "data/inventory/inventory.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            self._initialize_database()

    def _initialize_database(self) -> None:
        initial_data = {"items": []}
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=4)

    def _load_database(self) -> Dict:
        with open(self.db_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_database(self, data: Dict) -> None:
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def add_item(self, item: Dict) -> bool:
        database = self._load_database()
        item_id = item.get("item_id")
        for existing_item in database["items"]:
            if existing_item["item_id"] == item_id:
                raise ValueError(f"Item with ID '{item_id}' already exists.")

        database["items"].append(item)
        self._save_database(database)
        return True

    def get_item(self, item_id: str) -> Optional[Dict]:
        database = self._load_database()
        for item in database["items"]:
            if item["item_id"] == item_id:
                return item
        return None

    def get_all_items(self) -> List[Dict]:
        database = self._load_database()
        return database["items"]

    def update_item(self, item_id: str, updated_item: Dict) -> bool:
        database = self._load_database()
        for index, item in enumerate(database["items"]):
            if item["item_id"] == item_id:
                updated_item["item_id"] = item_id
                database["items"][index] = updated_item
                self._save_database(database)
                return True
        return False

    def delete_item(self, item_id: str) -> bool:
        database = self._load_database()
        original_count = len(database["items"])
        database["items"] = [
            item
            for item in database["items"]
            if item["item_id"] != item_id
        ]
        if len(database["items"]) == original_count:
            return False
        self._save_database(database)
        return True