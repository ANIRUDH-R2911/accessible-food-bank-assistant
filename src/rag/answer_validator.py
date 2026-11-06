import re
from typing import Any

class AnswerValidator:
    ITEM_ID_PATTERN = re.compile(r"\bFBA-[A-Z0-9-]+\b", re.IGNORECASE)
    ALLERGEN_SAFETY_PATTERNS = (
        r"\ballergen[- ]free\b",
        r"\bsafe for (?:people with )?.{0,50}\ballerg(?:y|ies)\b",
        r"\bsafe for people allergic to\b",
        r"\b(?:completely )?free of\b",
        r"\bdoes not contain\b",
        r"\bcontains no\b",
    )

    def validate(self, answer: str, records: list[dict]) -> bool:
        if not isinstance(answer, str) or not answer.strip():
            return False
        if not isinstance(records, list) or not records:
            return False
        valid_records = [
            record
            for record in records
            if isinstance(record, dict) and record.get("item_id")
        ]
        if not valid_records:
            return False
        if not self.validate_item_ids(answer, valid_records):
            return False
        if not self.validate_nutrition_claims(answer, valid_records):
            return False
        if not self.validate_ingredient_claims(answer, valid_records):
            return False
        if not self.validate_allergen_claims(answer, valid_records):
            return False

        return True

    def validate_item_ids(self, answer: str, records: list[dict]) -> bool:
        mentioned_ids = {
            item_id.upper()
            for item_id in self.ITEM_ID_PATTERN.findall(answer)
        }
        if not mentioned_ids:
            return True
        available_ids = {
            str(record["item_id"]).upper()
            for record in records
        }
        return mentioned_ids.issubset(available_ids)

    def validate_nutrition_claims(self, answer: str, records: list[dict]) -> bool:
        answer_lower = answer.lower()
        for record in records:
            nutrition = record.get("nutrition")
            if not isinstance(nutrition, dict):
                continue
            for nutrient, recorded_value in nutrition.items():
                if not isinstance(nutrient, str):
                    continue
                nutrient_pattern = self._nutrient_pattern(nutrient)
                if not re.search(nutrient_pattern, answer_lower):
                    continue
                claims = self._extract_nutrition_claims(answer_lower, nutrient_pattern)
                for claimed_value in claims:
                    if recorded_value is None:
                        return False
                    try:
                        expected = float(recorded_value)
                    except (TypeError, ValueError):
                        return False
                    if abs(claimed_value - expected) > 0.01:
                        return False
        return True

    @staticmethod
    def _nutrient_pattern(nutrient: str) -> str:
        normalized = re.sub(r"[_\-]+", " ", nutrient.strip())
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = re.sub(r"\s+(?:g|mg|mcg|kcal)$", "", normalized)
        return r"\b" + re.escape(normalized) + r"\b"

    @staticmethod
    def _extract_nutrition_claims(answer: str, nutrient_pattern: str) -> list[float]:
        patterns = (
            rf"(\d+(?:\.\d+)?)\s*(?:g|mg|mcg|kcal)?\s*"
            rf"(?:of\s+)?{nutrient_pattern}",
            rf"{nutrient_pattern}\s*(?:is|:|of|=)?\s*"
            rf"(\d+(?:\.\d+)?)\s*(?:g|mg|mcg|kcal)?",
        )
        claims = []
        for pattern in patterns:
            for match in re.finditer(pattern, answer):
                try:
                    claims.append(float(match.group(1)))
                except (ValueError, IndexError):
                    continue
        return claims

    def validate_ingredient_claims(self, answer: str, records: list[dict]) -> bool:
        claims = re.findall(r"\bcontains\s+([^.!?;]+)", answer, flags=re.IGNORECASE)
        for claim in claims:
            if re.match(r"\s*\d+(?:\.\d+)?\s*(?:g|mg|mcg|kcal)\b", claim, re.I):
                continue
            if re.search(r"\b(?:free|safe|allerg|allergy|allergies)\b", claim, re.IGNORECASE):
                continue

            claimed_ingredients = self.split_ingredient_claim(claim)
            if not claimed_ingredients:
                continue
            available_ingredients = set()
            for record in records:
                ingredients = record.get("ingredients", [])
                if isinstance(ingredients, list):
                    available_ingredients.update(
                        self.normalize_term(item)
                        for item in ingredients
                        if isinstance(item, str)
                    )
            for ingredient in claimed_ingredients:
                if ingredient not in available_ingredients:
                    return False
        return True

    @staticmethod
    def split_ingredient_claim(claim: str) -> list[str]:
        claim = re.sub(r"\band\b", ",", claim, flags=re.IGNORECASE)
        parts = [AnswerValidator.normalize_term(part) for part in claim.split(",")]
        return [
            part for part in parts
            if part and not re.fullmatch(r"\d+(?:\.\d+)?", part)
        ]

    def validate_allergen_claims(self, answer: str, records: list[dict]) -> bool:
        answer_lower = answer.lower()
        has_safety_claim = any(
            re.search(pattern, answer_lower)
            for pattern in self.ALLERGEN_SAFETY_PATTERNS
        )
        if not has_safety_claim:
            return True
        recorded_allergens = set()
        for record in records:
            for field in ("contains_allergens", "may_contain"):
                values = record.get(field, [])
                if isinstance(values, list):
                    recorded_allergens.update(
                        self.normalize_term(value)
                        for value in values
                        if isinstance(value, str)
                    )
        if not recorded_allergens:
            return True
        if re.search(r"\ballergen[- ]free\b|\bsafe for\b", answer_lower):
            return False

        for allergen in recorded_allergens:
            if not allergen:
                continue
            escaped = re.escape(allergen)
            specific_patterns = (
                rf"\b{escaped}(?:s)?[- ]free\b",
                rf"\bfree of {escaped}(?:s)?\b",
                rf"\bdoes not contain {escaped}(?:s)?\b",
                rf"\bcontains no {escaped}(?:s)?\b",
                rf"\bsafe for (?:people with )?{escaped} allergies\b",
                rf"\bsafe for people allergic to {escaped}\b",
            )
            if any(re.search(pattern, answer_lower) for pattern in specific_patterns):
                return False
        return True

    @staticmethod
    def normalize_term(value: str) -> str:
        value = value.lower().strip()
        value = re.sub(r"[^a-z0-9\s]", "", value)
        value = re.sub(r"\s+", " ", value)
        return value
