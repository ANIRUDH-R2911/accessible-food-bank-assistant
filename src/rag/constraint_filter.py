import re
from src.rag.nutrient_config import get_nutrient_threshold

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

INGREDIENT_ALLERGEN_TERMS = {
    "peanut": ("peanut", "peanuts", "groundnut", "groundnuts", "arachis"),
    "milk": ("milk", "dairy", "whey", "casein", "lactose", "buttermilk", "cream", "cheese", "yogurt", "yoghurt"),
    "egg": ("egg", "eggs", "albumen", "albumin"),
    "tree nuts": ("almond", "almonds", "cashew", "cashews", "walnut", "walnuts", "pistachio", "pistachios", "hazelnut", "hazelnuts", "pecan", "pecans", "macadamia", "brazil nut", "pine nut"),
    "soy": ("soy", "soya", "soybean", "soybeans", "tofu", "edamame"),
    "wheat": ("wheat", "durum", "semolina", "spelt", "farro", "bulgur"),
    "fish": ("fish", "anchovy", "anchovies", "salmon", "tuna", "cod"),
    "shellfish": ("shellfish", "shrimp", "prawn", "crab", "lobster", "crayfish"),
    "sesame": ("sesame", "tahini", "benne"),
}

def as_values(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def normalize_allergen(value):
    normalized = str(value).lower().strip()
    return ALLERGEN_NORMALIZATION.get(normalized, normalized)


def ingredient_text(item):
    ingredients = item.get("ingredients")
    values = as_values(ingredients)
    return " ".join(str(value) for value in values if value is not None).lower()


def ingredient_mentions_excluded_allergen(item, excluded_allergens):
    text = ingredient_text(item)
    if not text:
        return False

    for allergen in excluded_allergens:
        canonical = normalize_allergen(allergen)
        terms = INGREDIENT_ALLERGEN_TERMS.get(canonical, (canonical,))
        for term in terms:
            if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text):
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
        normalized_excluded = {
            normalize_allergen(allergen)
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
            item_allergens = {
                normalize_allergen(allergen)
                for allergen in as_values(contains_allergens) + as_values(may_contain)
            }

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