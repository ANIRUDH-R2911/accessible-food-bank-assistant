HIGH_PROTEIN_THRESHOLD = 10

LOW_CALORIE_THRESHOLD = 200
HIGH_CALORIE_THRESHOLD = 400

LOW_SODIUM_THRESHOLD = 140
HIGH_SODIUM_THRESHOLD = 400


class ConstraintFilter:
    def apply_constraints(self, results, constraints):
        filtered_results = results
        excluded_allergens = constraints.get("exclude_allergens", [])
        if excluded_allergens:
            filtered_results = self.filter_allergens(filtered_results, excluded_allergens)

        protein_constraint = constraints.get("protein")
        if protein_constraint:
            filtered_results = self.filter_protein(filtered_results, protein_constraint)

        calorie_constraint = constraints.get("calories")
        if calorie_constraint:
            filtered_results = self.filter_calories(filtered_results, calorie_constraint)

        sodium_constraint = constraints.get("sodium")
        if sodium_constraint:
            filtered_results = self.filter_sodium(filtered_results, sodium_constraint)

        return filtered_results

    def filter_allergens(self, results, excluded_allergens):
        filtered = []
        for item in results:
            item_allergens = [
                allergen.lower()
                for allergen in item.get("contains_allergens", [])
            ]

            contains_excluded = any(
                allergen.lower() in item_allergens
                for allergen in excluded_allergens
            )

            if not contains_excluded:
                filtered.append(item)

        return filtered

    def filter_protein(self, results, level):
        filtered = []
        for item in results:
            protein = (item.get("nutrition", {}).get("protein", 0))
            if level == "high":
                if protein >= HIGH_PROTEIN_THRESHOLD:
                    filtered.append(item)
        return filtered

    def filter_calories(self, results, level):
        filtered = []
        for item in results:
            calories = (item.get("nutrition", {}).get("calories", 0))
            if level == "low":
                if calories <= LOW_CALORIE_THRESHOLD:
                    filtered.append(item)

            elif level == "high":
                if calories >= HIGH_CALORIE_THRESHOLD:
                    filtered.append(item)

        return filtered

    def filter_sodium(self, results, level):
        filtered = []
        for item in results:
            sodium = (item.get("nutrition", {}).get("sodium", 0))
            if level == "low":
                if sodium <= LOW_SODIUM_THRESHOLD:
                    filtered.append(item)

            elif level == "high":
                if sodium >= HIGH_SODIUM_THRESHOLD:
                    filtered.append(item)

        return filtered