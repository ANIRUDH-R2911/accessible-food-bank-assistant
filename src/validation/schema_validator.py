from copy import deepcopy

class SchemaValidator:
    DEFAULT_SCHEMA = {
        "item_id": "",
        "ingredients": [],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {}
    }

    ALLERGEN_MAP = {
        "almond": "tree nuts",
        "almonds": "tree nuts",
        "cashew": "tree nuts",
        "cashews": "tree nuts",
        "walnut": "tree nuts",
        "walnuts": "tree nuts",
        "pecan": "tree nuts",
        "pecans": "tree nuts",
        "hazelnut": "tree nuts",
        "hazelnuts": "tree nuts",
        "pistachio": "tree nuts",
        "pistachios": "tree nuts",
        "soybean": "soy",
        "soybeans": "soy",
        "egg": "egg",
        "eggs": "egg",
        "milk": "milk",
        "wheat": "wheat",
        "peanut": "peanut",
        "peanuts": "peanut",
        "fish": "fish",
        "shellfish": "shellfish",
        "sesame": "sesame"
    }

    def validate(self, data):
        try:
            if not isinstance(data, dict):
                return deepcopy(self.DEFAULT_SCHEMA)

            validated = deepcopy(self.DEFAULT_SCHEMA)
            validated["item_id"] = self._validate_item_id(data.get("item_id", ""))
            validated["ingredients"] = self._normalize_ingredients(data.get("ingredients", []))
            validated["contains_allergens"] = self._normalize_allergens(data.get("contains_allergens", []))
            validated["may_contain"] = self._normalize_allergens(data.get("may_contain", []))
            validated["nutrition"] = self._validate_nutrition(data.get("nutrition", {}))
            return validated

        except Exception:
            return deepcopy(self.DEFAULT_SCHEMA)

    def _validate_item_id(self, item_id):
        if isinstance(item_id, str):
            return item_id.strip()
        return ""

    def _normalize_ingredients(self, ingredients):
        if isinstance(ingredients, str):
            ingredients = ingredients.split(",")

        if not isinstance(ingredients, list):
            return []

        normalized = []
        for ingredient in ingredients:
            if not isinstance(ingredient, str):
                continue

            ingredient = ingredient.strip().lower()
            if not ingredient:
                continue

            normalized.append(ingredient)
        return sorted(list(set(normalized)))

    def _normalize_allergens(self, allergens):
        if isinstance(allergens, str):
            allergens = allergens.split(",")

        if not isinstance(allergens, list):
            return []

        normalized = []
        for allergen in allergens:
            if not isinstance(allergen, str):
                continue

            allergen = allergen.strip().lower()
            if not allergen:
                continue
            allergen = self.normalize_allergen(allergen)
            normalized.append(allergen)
        return sorted(list(set(normalized)))

    def _validate_nutrition(self, nutrition):
        if isinstance(nutrition, dict):
            return nutrition
        return {}
    
    @classmethod
    def normalize_allergen(cls, allergen):
        if not isinstance(allergen, str): 
            return ""
        allergen = allergen.lower().strip()
        return cls.ALLERGEN_MAP.get(allergen, allergen)