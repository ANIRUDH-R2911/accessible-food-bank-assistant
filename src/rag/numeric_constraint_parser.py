
import re
from typing import Dict, List, Optional

from src.rag.nutrient_config import (NUTRIENT_CONFIG, get_nutrient_unit, normalize_nutrient_name)


class NumericConstraintParser:
    COMPARATOR_PATTERNS = [
        (r"greater\s+than\s+or\s+equal\s+to", "gte"),
        (r"less\s+than\s+or\s+equal\s+to", "lte"),
        (r"at\s+least", "gte"),
        (r"no\s+less\s+than", "gte"),
        (r"greater\s+than", "gt"),
        (r"more\s+than", "gt"),
        (r"above", "gt"),
        (r"over", "gt"),
        (r"at\s+most", "lte"),
        (r"no\s+more\s+than", "lte"),
        (r"less\s+than", "lt"),
        (r"fewer\s+than", "lt"),
        (r"below", "lt"),
        (r"under", "lt"),
        (r">=", "gte"),
        (r"<=", "lte"),
        (r">", "gt"),
        (r"<", "lt"),
    ]

    UNIT_ALIASES = {
        "g": "g",
        "gram": "g",
        "grams": "g",
        "mg": "mg",
        "milligram": "mg",
        "milligrams": "mg",
        "kcal": "kcal",
        "calorie": "kcal",
        "calories": "kcal",
        "kilocalorie": "kcal",
        "kilocalories": "kcal",
    }

    def __init__(self):
        comparator_regex = "|".join(
            f"(?:{pattern})"
            for pattern, _ in self.COMPARATOR_PATTERNS
        )

        nutrient_aliases = {}

        for canonical, config in NUTRIENT_CONFIG.items():
            for alias in [canonical] + config.get("aliases", []):
                nutrient_aliases[alias.lower()] = canonical

        aliases = sorted(nutrient_aliases, key=len, reverse=True)
        nutrient_regex = "|".join(
            re.escape(alias).replace(r"\ ", r"\s+")
            for alias in aliases
        )
        unit_regex = "|".join(
            sorted((re.escape(unit) for unit in self.UNIT_ALIASES), key=len, reverse=True))

        self.pattern = re.compile(
            rf"\b(?P<nutrient>{nutrient_regex})\b"
            rf"\s*(?P<comparator>{comparator_regex})"
            rf"\s*(?P<value>\d+(?:\.\d+)?)"
            rf"\s*(?P<unit>{unit_regex})?\b",
            re.IGNORECASE,
        )

        self.nutrient_aliases = nutrient_aliases
        self.comparator_lookup = {
            pattern: operator
            for pattern, operator in self.COMPARATOR_PATTERNS
        }

    def _normalize_operator(self, comparator: str) -> str:
        normalized = re.sub(r"\s+", " ", comparator.lower().strip())
        for pattern, operator in self.COMPARATOR_PATTERNS:
            if re.fullmatch(pattern, normalized):
                return operator
        raise ValueError(f"Unsupported comparator: {comparator}")

    def _normalize_value(self, nutrient: str, value: float, supplied_unit: Optional[str]) -> Optional[Dict]:
        canonical_unit = get_nutrient_unit(nutrient)
        if canonical_unit is None:
            return None

        input_unit = (
            self.UNIT_ALIASES.get(supplied_unit.lower())
            if supplied_unit
            else canonical_unit
        )
        if input_unit is None:
            return None

        if input_unit != canonical_unit:
            if input_unit == "g" and canonical_unit == "mg":
                value *= 1000
            elif input_unit == "mg" and canonical_unit == "g":
                value /= 1000
            else:
                return None

        return {
            "value": value,
            "unit": canonical_unit,
        }

    def parse(self, query: str) -> List[Dict]:
        if not query or not query.strip():
            return []

        constraints = []
        seen = set()
        for match in self.pattern.finditer(query.lower()):
            alias = match.group("nutrient").lower()
            nutrient = self.nutrient_aliases.get(alias)
            nutrient = normalize_nutrient_name(nutrient or alias)
            if nutrient is None:
                continue

            operator = self._normalize_operator(match.group("comparator"))
            raw_value = float(match.group("value"))
            supplied_unit = match.group("unit")
            normalized = self._normalize_value(nutrient, raw_value, supplied_unit)
            if normalized is None:
                continue

            constraint = {
                "nutrient": nutrient,
                "operator": operator,
                "value": normalized["value"],
                "unit": normalized["unit"],
                "source": "numeric",
            }

            identity = (
                constraint["nutrient"],
                constraint["operator"],
                constraint["value"],
                constraint["unit"],
            )

            if identity not in seen:
                constraints.append(constraint)
                seen.add(identity)

        return constraints
