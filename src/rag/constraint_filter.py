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
        normalized_excluded = {
            ALLERGEN_NORMALIZATION.get(str(allergen).lower().strip(), str(allergen).lower().strip())
            for allergen in excluded_allergens
            }
        filtered = []
        for item in results:
            if ("contains_allergens" not in item and "allergens" not in item):
                continue
            contains_allergens = item.get("contains_allergens")
            if contains_allergens is None:
                contains_allergens = item.get("allergens")

            may_contain = item.get("may_contain")
            if isinstance(contains_allergens, str):
                contains_allergens = [contains_allergens]
            if isinstance(may_contain, str):
                may_contain = [may_contain]

            contains_allergens = contains_allergens or []
            may_contain = may_contain or []
            item_allergens = set()
            for allergen in list(contains_allergens) + list(may_contain):
                normalized = ALLERGEN_NORMALIZATION.get(str(allergen).lower().strip(), str(allergen).lower().strip())
                item_allergens.add(normalized)
            if normalized_excluded.intersection(item_allergens):
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