from typing import Dict, List, Optional

NUTRIENT_CONFIG: Dict[str, Dict] = {
    "protein": {
        "aliases": [
            "protein",
        ],
        "unit": "g",
        "thresholds": {
            "high": {
                "operator": ">=",
                "value": 10.0,
            },
            "low": {
                "operator": "<=",
                "value": 5.0,
            },
        },
    },

    "calories": {
        "aliases": [
            "calorie",
            "calories",
            "kcal",
        ],
        "unit": "kcal",
        "thresholds": {
            "low": {
                "operator": "<=",
                "value": 200.0,
            },
            "high": {
                "operator": ">=",
                "value": 400.0,
            },
        },
    },

    "sodium": {
        "aliases": [
            "sodium",
            "salt",
        ],
        "unit": "mg",
        "thresholds": {
            "low": {
                "operator": "<=",
                "value": 140.0,
            },
            "high": {
                "operator": ">=",
                "value": 400.0,
            },
        },
    },

    "sugar": {
        "aliases": [
            "sugar",
            "sugars",
        ],
        "unit": "g",
        "thresholds": {
            "low": {
                "operator": "<=",
                "value": 5.0,
            },
            "high": {
                "operator": ">=",
                "value": 15.0,
            },
        },
    },

    "fiber": {
        "aliases": [
            "fiber",
            "fibre",
            "dietary fiber",
            "dietary fibre",
        ],
        "unit": "g",
        "thresholds": {
            "low": {
                "operator": "<=",
                "value": 2.0,
            },
            "high": {
                "operator": ">=",
                "value": 5.0,
            },
        },
    },

    "fat": {
        "aliases": [
            "fat",
            "total fat",
        ],
        "unit": "g",
        "thresholds": {
            "low": {
                "operator": "<=",
                "value": 3.0,
            },
            "high": {
                "operator": ">=",
                "value": 17.5,
            },
        },
    },

    "carbohydrates": {
        "aliases": [
            "carbohydrate",
            "carbohydrates",
            "carb",
            "carbs",
            "total carbohydrate",
            "total carbohydrates",
        ],
        "unit": "g",
        "thresholds": {
            "low": {
                "operator": "<=",
                "value": 20.0,
            },
            "high": {
                "operator": ">=",
                "value": 50.0,
            },
        },
    },
}

def get_supported_nutrients() -> List[str]:
    return list(NUTRIENT_CONFIG.keys())


def normalize_nutrient_name(nutrient_name: str) -> Optional[str]:
    normalized_input = nutrient_name.lower().strip()
    for canonical_name, config in NUTRIENT_CONFIG.items():
        if normalized_input == canonical_name:
            return canonical_name

        aliases = config.get("aliases", [])
        if normalized_input in aliases:
            return canonical_name
    return None


def get_nutrient_config(nutrient_name: str) -> Optional[Dict]:
    canonical_name = normalize_nutrient_name(nutrient_name)
    if canonical_name is None:
        return None
    return NUTRIENT_CONFIG.get(canonical_name)


def get_nutrient_threshold(nutrient_name: str, level: str) -> Optional[Dict]:
    config = get_nutrient_config(nutrient_name)
    if config is None:
        return None

    thresholds = config.get("thresholds", {})
    return thresholds.get(level.lower().strip())


def get_nutrient_unit(nutrient_name: str) -> Optional[str]:
    config = get_nutrient_config(nutrient_name)
    if config is None:
        return None
    return config.get("unit")