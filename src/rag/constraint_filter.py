from src.rag.nutrient_config import (get_nutrient_threshold)

ALLERGEN_NORMALIZATION = {
    "peanut": "peanut",
    "peanuts": "peanut",
    "milk": "milk",
    "dairy": "milk",
    "egg": "egg",
    "eggs": "egg",
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
        filtered = []
        for item in results:
            item_allergens = [
                ALLERGEN_NORMALIZATION.get(allergen.lower(), allergen.lower())
                for allergen in item.get("contains_allergens", [])
            ]

            normalized_excluded = [
                ALLERGEN_NORMALIZATION.get(allergen.lower(), allergen.lower())
                for allergen in excluded_allergens
            ]
            contains_excluded = any(
                allergen in item_allergens
                for allergen in normalized_excluded
            )

            if not contains_excluded:
                filtered.append(item)

        return filtered
    
    def filter_nutrients(self, results, nutrient_constraints):
        filtered_results = results
        for constraint in nutrient_constraints:
            filtered_results = self.filter_single_nutrient(filtered_results, constraint)
        return filtered_results

    def filter_single_nutrient(self, results, constraint):
        nutrient = constraint["nutrient"]
        level = constraint["level"]
        threshold = get_nutrient_threshold(nutrient, level)
        if threshold is None:
            return results
        operator = threshold["operator"]
        value = threshold["value"]
        filtered = []
        for item in results:
            nutrient_value = (item.get("nutrition", {}).get(nutrient))
            if nutrient_value is None:
                continue
            try:
                nutrient_value = float(nutrient_value)
            except (TypeError, ValueError):
                continue
            if self.evaluate_operator(nutrient_value, operator, value):
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