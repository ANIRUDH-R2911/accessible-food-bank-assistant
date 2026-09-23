import json
from pathlib import Path
from typing import Dict, List, Optional

from src.validation.schema_validator import SchemaValidator


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
        search_term = SchemaValidator.normalize_allergen(allergen)
        matches = []
        for item in self.inventory:
            allergens = [
                SchemaValidator.normalize_allergen(a)
                for a in item.get("contains_allergens", [])
        ]
            if search_term in allergens:
                matches.append(item)
        return matches
    
    def search_by_nutrition(self, nutrient, operator, value):
        results = []
        for item in self.inventory:
            nutrition = item.get("nutrition", {})
            if nutrient not in nutrition:
                continue
            nutrient_value = nutrition[nutrient]
            match = False
            if operator == ">":
                match = nutrient_value > value
            elif operator == ">=":
                match = nutrient_value >= value
            elif operator == "<":
                match = nutrient_value < value
            elif operator == "<=":
                match = nutrient_value <= value
            elif operator == "==":
                match = nutrient_value == value
            if match:
                results.append(item)
        return results
    
    def search_by_multiple_filters(self, ingredient=None, allergen=None, nutrient=None, operator=None, value=None):
        results = []
        for item in self.inventory:
            match = True
            if ingredient:
                ingredients = [i.lower() for i in item.get("ingredients", [])]
                if ingredient.lower() not in ingredients:
                    match = False
            if allergen:
                allergens = [a.lower() for a in item.get("contains_allergens", [])]
                if allergen.lower() not in allergens:
                    match = False
            if nutrient:
                nutrition = item.get("nutrition",{})
                if nutrient not in nutrition:
                    match = False
                else:
                    nutrient_value = nutrition[nutrient]
                    if operator == ">":
                        match = match and (nutrient_value > value)
                    elif operator == ">=":
                        match = match and (nutrient_value >= value)
                    elif operator == "<":
                        match = match and (nutrient_value < value)
                    elif operator == "<=":
                        match = match and (nutrient_value <= value)
                    elif operator == "==":
                        match = match and (nutrient_value == value)
            if match:
                results.append(item)
        return results