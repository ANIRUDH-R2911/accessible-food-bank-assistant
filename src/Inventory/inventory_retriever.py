import json
from pathlib import Path
from typing import Dict, List, Optional


class InventoryRetriever:
    def __init__(self,inventory_path: str = "data/inventory/inventory.json"):
        self.inventory_path = Path(inventory_path)
        self.inventory = self._load_inventory()

    def _load_inventory(self) -> List[Dict]:
        if not self.inventory_path.exists():
            return []
        with open(self.inventory_path, "r", encoding="utf-8") as f:
            database = json.load(f)
        return database.get("items", [])

    def reload_inventory(self) -> None:
        self.inventory = self._load_inventory()

    def get_all_items(self) -> List[Dict]:
        return self.inventory

    def get_item_by_id(self, item_id: str) -> Optional[Dict]:
        for item in self.inventory:
            if item.get("item_id") == item_id:
                return item
        return None

    def search_by_ingredient(self, keyword: str) -> List[Dict]:
        keyword = keyword.lower().strip()
        matches = []
        for item in self.inventory:
            ingredients = item.get("ingredients", [])
            if any(
                keyword in ingredient.lower()
                for ingredient in ingredients
            ):
                matches.append(item)
        return matches

    def search_by_allergen(self, allergen: str) -> List[Dict]:
        allergen = allergen.lower().strip()
        matches = []
        for item in self.inventory:
            allergens = item.get("contains_allergens", [])
            if any(
                allergen in entry.lower()
                for entry in allergens
            ):
                matches.append(item)
        return matches