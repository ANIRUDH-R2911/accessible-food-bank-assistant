import re
from src.rag.allergen_config import (CANONICAL_ALLERGENS, expand_excluded_allergens, allergen_ingredient_pattern, normalize_allergen_label)
from src.rag.nutrient_config import get_nutrient_threshold

def as_values(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]

def ingredient_text(item):
    ingredients = item.get("ingredients")
    values = as_values(ingredients)
    return " ".join(str(value) for value in values if value is not None).lower()


def ingredient_mentions_excluded_allergen(item, excluded_allergens):
    text = ingredient_text(item)
    if not text:
        return False

    for allergen in excluded_allergens:
        canonical = normalize_allergen_label(allergen)
        pattern = allergen_ingredient_pattern(canonical)
        if pattern.search(text):
            return True
    return False
class ConstraintFilter:
    def apply_constraints(self, results, constraints):
        filtered_results = results
        excluded_allergens = constraints.get("allergen_exclude", [])
        if excluded_allergens:
            filtered_results = self.filter_allergens(filtered_results, excluded_allergens)
        nutrient_constraints = constraints.get("nutrient_constraints", [])
        if nutrient_constraints:
            filtered_results = self.filter_nutrients(filtered_results, nutrient_constraints)
        return filtered_results

    def filter_allergens(self, results, excluded_allergens):
        normalized_excluded = expand_excluded_allergens(excluded_allergens)            
        filtered = []
        for item in results:
            contains_metadata_available = (
                ("contains_allergens" in item and item.get("contains_allergens") is not None) or 
                ("allergens" in item and item.get("allergens") is not None))
            may_contain_metadata_available = ("may_contain" in item and item.get("may_contain") is not None)
            if not contains_metadata_available or not may_contain_metadata_available:
                continue
            contains_allergens = (as_values(item.get("contains_allergens")) + as_values(item.get("allergens")))
            may_contain = as_values(item.get("may_contain"))
            item_allergens = {
                normalize_allergen_label(allergen)
                for allergen in contains_allergens + may_contain
                if allergen is not None
            }
            has_unknown_allergen = any(
                allergen not in CANONICAL_ALLERGENS
                for allergen in item_allergens
            )
            if has_unknown_allergen:
                continue
            if normalized_excluded.intersection(item_allergens):
                continue
            if ingredient_mentions_excluded_allergen(item, normalized_excluded):
                continue
            filtered.append(item)
        return filtered
    
    def filter_nutrients(self, results, nutrient_constraints):
        filtered_results = results
        for constraint in nutrient_constraints:
            filtered_results = self.filter_single_nutrient(filtered_results, constraint)
        return filtered_results

    def filter_single_nutrient(self, results, constraint):
        nutrient = constraint["nutrient"]
        if (constraint.get("source") == "numeric" or ("operator" in constraint and "value" in constraint)):
            operator_aliases = {
                "gt": ">",
                "lt": "<",
                "gte": ">=",
                "lte": "<=",
                }
            operator = operator_aliases.get(constraint["operator"], constraint["operator"])
            value = constraint["value"]
        else:
            level = constraint.get("level")
            if level is None:
                return []
            threshold = get_nutrient_threshold(nutrient, level)
            if threshold is None:
                return []
            operator = threshold["operator"]
            value = threshold["value"]
        
        filtered = []
        for item in results:
            nutrient_value = (item.get("nutrition", {}).get(nutrient))
            if nutrient_value is None:
                continue
            try:
                nutrient_value = float(nutrient_value)
                threshold_value = float(value)
            except (TypeError, ValueError):
                continue
            if self.evaluate_operator(nutrient_value, operator, threshold_value):
                filtered.append(item)
        return filtered
    
    def evaluate_operator(self, actual_value, operator, threshold):
        if operator == ">=":
            return actual_value >= threshold
        if operator == "<=":
            return actual_value <= threshold
        if operator == ">":
            return actual_value > threshold
        if operator == "<":
            return actual_value < threshold
        if operator == "==":
            return actual_value == threshold
        return False