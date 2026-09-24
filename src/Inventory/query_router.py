import re
from typing import Dict

class QueryRouter:
    ALLERGENS = {
        "milk",
        "dairy",
        "peanut",
        "peanuts",
        "tree nut",
        "tree nuts",
        "almond",
        "almonds",
        "soy",
        "wheat",
        "egg",
        "eggs",
        "fish",
        "shellfish",
        "sesame"
    }

    NUTRIENTS = {
        "protein",
        "sodium",
        "fiber",
        "fat",
        "sugar",
        "calories",
        "calorie"
    }

    def detect_query_type(self, query: str) -> str:
        query = query.lower()
        if any(word in query for word in self.NUTRIENTS):
            return "nutrition"
        if any(word in query for word in self.ALLERGENS):
            return "allergen"
        return "ingredient"

    def parse_ingredient_query(self, query: str) -> Dict:
        query = query.lower()
        stop_words = {
            "show",
            "find",
            "foods",
            "food",
            "items",
            "with",
            "containing",
            "contains"
        }
        tokens = query.split()
        ingredient_tokens = [
            token for token in tokens
            if token not in stop_words
        ]
        ingredient = " ".join(ingredient_tokens).strip()
        return {
            "query_type": "ingredient",
            "filters": {
                "ingredient": ingredient
            }
        }

    def parse_allergen_query(self, query: str) -> Dict:
        query = query.lower()
        for allergen in self.ALLERGENS:
            if allergen in query:
                return {
                    "query_type": "allergen",
                    "filters": {
                        "allergen": allergen
                    }
                }

        return {
            "query_type": "allergen",
            "filters": {}
        }

    def parse_nutrition_query(self, query: str) -> Dict:
        query = query.lower()
        nutrient = None
        for n in self.NUTRIENTS:
            if n in query:
                nutrient = n
                break

        if nutrient is None:
            return {
                "query_type": "nutrition",
                "filters": {}
            }

        if "high" in query:
            operator = ">"
            value = 10
        elif "low" in query:
            operator = "<"
            value = 10
        else:
            match = re.search(r"(\d+)", query)
            if match:
                value = float(match.group(1))
                if any(
                    phrase in query
                    for phrase in [
                        "more than",
                        "greater than",
                        "above"
                    ]
                ):
                    operator = ">"
                elif any(
                    phrase in query
                    for phrase in [
                        "less than",
                        "below",
                        "under"
                    ]
                ):
                    operator = "<"
                else:
                    operator = ">"
            else:
                operator = ">"
                value = 10

        return {
            "query_type": "nutrition",
            "filters": {
                "nutrient": nutrient,
                "operator": operator,
                "value": value
            }
        }

    def route(self, query: str) -> Dict:
        query_type = self.detect_query_type(query)
        if query_type == "ingredient":
            return self.parse_ingredient_query(query)
        if query_type == "allergen":
            return self.parse_allergen_query(query)
        if query_type == "nutrition":
            return self.parse_nutrition_query(query)
        return {
            "query_type": "unknown",
            "filters": {}
        }