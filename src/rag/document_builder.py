class DocumentBuilder:
    def build_document(self, item):
        item_id = item.get("item_id", "UNKNOWN")
        ingredients = item.get("ingredients", [])
        allergens = item.get("contains_allergens", [])
        nutrition = item.get("nutrition", {})
        document_lines = [
            f"Item ID: {item_id}",
            "",
            "Ingredients:",
            ", ".join(ingredients) if ingredients else "None",
            "",
            "Allergens:",
            ", ".join(allergens) if allergens else "None",
            "",
            "Nutrition:"
        ]
        if nutrition:
            for nutrient, value in nutrition.items():
                document_lines.append(f"{nutrient}: {value}")
        else:
            document_lines.append("None")

        semantic_descriptions = self._generate_semantic_descriptions(nutrition=nutrition, allergens=allergens)
        if semantic_descriptions:
            document_lines.extend(["", "Food Characteristics:"])
            document_lines.extend(semantic_descriptions)

        document_text = "\n".join(document_lines)
        metadata = {
            "item_id": item_id,
            "ingredient_count": len(ingredients),
            "allergen_count": len(allergens)
        }

        return {
            "id": item_id,
            "document": document_text,
            "metadata": metadata
        }

    def build_documents(self, inventory_items):
        return [
            self.build_document(item)
            for item in inventory_items
        ]

    def _generate_semantic_descriptions(self, nutrition, allergens):
        descriptions = []
        protein = self._safe_float(nutrition.get("protein"))
        calories = self._safe_float(nutrition.get("calories"))
        if protein is not None:
            if protein >= 15:
                descriptions.append("This food is a high protein food.")

            elif protein >= 8:
                descriptions.append("This food is a moderate protein food.")

            else:
                descriptions.append("This food is a low protein food.")

        if calories is not None:
            if calories >= 300:
                descriptions.append("This food is high in calories.")

            elif calories <= 120:
                descriptions.append("This food is lower in calories.")

        if allergens:
            descriptions.append("This food contains allergens.")

            for allergen in allergens:
                descriptions.append(f"This food contains {allergen}.")

        else:
            descriptions.append("No allergens were detected.")

        return descriptions

    def _safe_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None