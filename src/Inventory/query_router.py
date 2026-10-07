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

    SEMANTIC_TERMS = {
        "healthy",
        "snack",
        "snacks",
        "meal",
        "breakfast",
        "lunch",
        "dinner",
        "energy",
        "foods",
        "food",
        "similar",
        "recommend",
        "options"
    }

    CONSTRAINT_TERMS = {
        "without",
        "free",
        "free from",
        "safe",
        "allergy",
        "allergic",
        "avoid",
        "exclude"
    }
    
    ALLERGEN_EXCLUSION_PATTERNS = {
        "without",
        "free",
        "free from",
        "avoid",
        "exclude"
    }
    
    ALLERGEN_NORMALIZATION = {
        "peanut": "peanuts",
        "peanuts": "peanuts",
        "milk": "milk",
        "dairy": "milk",
        "egg": "eggs",
        "eggs": "eggs",
        "almond": "tree nuts",
        "almonds": "tree nuts",
        "tree nut": "tree nuts",
        "tree nuts": "tree nuts",
        "soy": "soy",
        "wheat": "wheat",
        "fish": "fish",
        "shellfish": "shellfish",
        "sesame": "sesame"
    }


    def detect_query_type(self, query: str) -> str:
        query = query.lower()
        constraints = self.extract_constraints(query)
        if any(value for value in constraints.values()):
            return "hybrid"
        
        has_constraint = any(term in query for term in self.CONSTRAINT_TERMS)
        has_allergen = any(allergen in query for allergen in self.ALLERGENS)
        has_semantic = any(term in query for term in self.SEMANTIC_TERMS)
        has_nutrient = any(nutrient in query for nutrient in self.NUTRIENTS)

        if (has_constraint and (has_allergen or has_semantic or has_nutrient)):
            return "hybrid"
        if has_nutrient:
            return "nutrition"
        if has_allergen:
            return "allergen"
        if has_semantic:
            return "semantic"
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

    def parse_hybrid_query(self, query: str) -> Dict:
        query = query.lower()
        allergens = [
            allergen
            for allergen in self.ALLERGENS
            if allergen in query
        ]
        nutrients = [
            nutrient
            for nutrient in self.NUTRIENTS
            if nutrient in query
        ]
        return {
            "query_type": "hybrid",
            "filters": {
                "query": query
            },
            "constraints": self.extract_constraints(query)
        }

    def parse_semantic_query(self, query: str) -> Dict:
        return {
            "query_type": "semantic",
            "filters": {
                "query": query.lower()
            }
        }
        
    def extract_constraints(self, query: str) -> Dict:
        query = query.lower()
        constraints = {
            "allergen_exclude": [],
            "protein": None,
            "calories": None,
            "sodium": None
            }
        has_exclusion_pattern = any(
            pattern in query
            for pattern in self.ALLERGEN_EXCLUSION_PATTERNS
            )
        if has_exclusion_pattern:
            detected_allergens = set()
            for allergen in self.ALLERGENS:
                if allergen in query:
                    canonical = self.ALLERGEN_NORMALIZATION.get(allergen, allergen)
                    detected_allergens.add(canonical)
            constraints["allergen_exclude"] = list(detected_allergens)
                    
        if "high protein" in query:
            constraints["protein"] = "high"
        elif "low protein" in query:
            constraints["protein"] = "low"
    
        if "high calorie" in query:
            constraints["calories"] = "high"
        elif "low calorie" in query:
            constraints["calories"] = "low"
            
        if "high sodium" in query:
            constraints["sodium"] = "high"
        elif "low sodium" in query:
            constraints["sodium"] = "low"
        
        return constraints
    
    def has_constraints(self, query: str) -> bool:
        constraints = self.extract_constraints(query)
        return any(
            value
            for value in constraints.values()
            )

    def route(self, query: str) -> Dict:
        query_type = self.detect_query_type(query)
        if query_type == "ingredient":
            return self.parse_ingredient_query(query)
        if query_type == "allergen":
            return self.parse_allergen_query(query)
        if query_type == "nutrition":
            return self.parse_nutrition_query(query)
        if query_type == "hybrid":
            return self.parse_hybrid_query(query)
        if query_type == "semantic":
            return self.parse_semantic_query(query)

        return {
            "query_type": "unknown",
            "filters": {}
        }