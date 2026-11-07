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
        records_by_id = {
            str(record["item_id"]).upper(): record
            for record in records
            if isinstance(record, dict) and record.get("item_id")
        }
        nutrient_patterns = {}
        for record in records_by_id.values():
            nutrition = record.get("nutrition")
            if not isinstance(nutrition, dict):
                continue
            for nutrient in nutrition:
                if isinstance(nutrient, str):
                    nutrient_patterns[nutrient] = self.nutrient_pattern(nutrient)

        sentences = re.split(r"(?<=[.!?])\s+", answer)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            sentence_claims = {}
            for nutrient, pattern in nutrient_patterns.items():
                if re.search(pattern, sentence_lower):
                    claims = self.extract_nutrition_claims(sentence_lower, pattern)
                    if claims:
                        sentence_claims[nutrient] = claims
            if not sentence_claims:
                continue
            mentioned_ids = {
                item_id.upper()
                for item_id in self.ITEM_ID_PATTERN.findall(sentence)
            }
            if mentioned_ids:
                if len(mentioned_ids) != 1:
                    return False
                item_id = next(iter(mentioned_ids))
                record = records_by_id.get(item_id)
                if record is None:
                    return False
            else:
                if len(records_by_id) != 1:
                    return False
                record = next(iter(records_by_id.values()))
            nutrition = record.get("nutrition")
            if not isinstance(nutrition, dict):
                return False
            for nutrient, claims in sentence_claims.items():
                if nutrient not in nutrition:
                    return False
                recorded_value = nutrition[nutrient]
                if recorded_value is None:
                    return False
                try:
                    expected = float(recorded_value)
                except (TypeError, ValueError):
                    return False
                for claimed_value in claims:
                    if abs(claimed_value - expected) > 0.01:
                        return False
        return True

    @staticmethod
    def nutrient_pattern(nutrient: str) -> str:
        normalized = re.sub(r"[_\-]+", " ", nutrient.strip())
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = re.sub(r"\s+(?:g|mg|mcg|kcal)$", "", normalized)
        return r"\b" + re.escape(normalized) + r"\b"

    @staticmethod
    def extract_nutrition_claims(answer: str, nutrient_pattern: str) -> list[float]:
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
        records_by_id = {
            str(record["item_id"]).upper(): record
            for record in records
            if isinstance(record, dict) and record.get("item_id")
        }
        sentences = re.split(r"(?<=[.!?])\s+", answer)
        for sentence in sentences:
            claims = re.findall(r"\bcontains\s+([^.!?;]+)", sentence, flags=re.IGNORECASE)
            if not claims:
                continue
            mentioned_ids = {
                item_id.upper()
                for item_id in self.ITEM_ID_PATTERN.findall(sentence)
            }
            if mentioned_ids:
                if len(mentioned_ids) != 1:
                    return False
                item_id = next(iter(mentioned_ids))
                record = records_by_id.get(item_id)
                if record is None:
                    return False
            else:
                if len(records_by_id) != 1:
                    return False
                record = next(iter(records_by_id.values()))
            ingredients = record.get("ingredients", [])
            if not isinstance(ingredients, list):
                return False
            available_ingredients = {
                self.normalize_term(item)
                for item in ingredients
                if isinstance(item, str)
            }
            for claim in claims:
                if re.match(r"\s*\d+(?:\.\d+)?\s*(?:g|mg|mcg|kcal)\b", claim, re.IGNORECASE):
                    continue
                if re.search(r"\b(?:free|safe|allerg|allergy|allergies)\b", claim, re.IGNORECASE):
                    continue
                claimed_ingredients = self.split_ingredient_claim(claim)
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
        sentences = re.split(r"(?<=[.!?])\s+", answer)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            has_safety_claim = any(
                re.search(pattern, sentence_lower)
                for pattern in self.ALLERGEN_SAFETY_PATTERNS
            )
            has_specific_free_claim = bool(re.search(r"\b[a-z][a-z-]*[- ]free\b|\bfree of\b", sentence_lower))
            has_negative_allergen_claim = bool(re.search(r"\bdoes not contain\b|\bcontains no\b", sentence_lower))
            if (has_safety_claim or has_specific_free_claim or has_negative_allergen_claim):
                return False
        return True

    @staticmethod
    def normalize_term(value: str) -> str:
        value = value.lower().strip()
        value = re.sub(r"[^a-z0-9\s]", "", value)
        value = re.sub(r"\s+", " ", value)
        return value
