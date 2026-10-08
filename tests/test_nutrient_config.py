import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.rag.nutrient_config import (
    get_supported_nutrients,
    normalize_nutrient_name,
    get_nutrient_config,
    get_nutrient_threshold,
    get_nutrient_unit,
)

def test_supported_nutrients():
    nutrients = get_supported_nutrients()
    assert "protein" in nutrients
    assert "calories" in nutrients
    assert "sodium" in nutrients
    assert "sugar" in nutrients
    assert "fiber" in nutrients
    assert "fat" in nutrients
    assert "carbohydrates" in nutrients

def test_nutrient_alias_normalization():
    assert normalize_nutrient_name("protein") == "protein"
    assert normalize_nutrient_name("calorie") == "calories"
    assert normalize_nutrient_name("carbs") == "carbohydrates"
    assert normalize_nutrient_name("carb") == "carbohydrates"
    assert normalize_nutrient_name("fibre") == "fiber"
    assert normalize_nutrient_name("total fat") == "fat"


def test_case_insensitive_normalization():
    assert normalize_nutrient_name("PROTEIN") == "protein"
    assert normalize_nutrient_name("Carbs") == "carbohydrates"
    assert normalize_nutrient_name("SUGAR") == "sugar"


def test_unknown_nutrient():
    assert normalize_nutrient_name("unknown nutrient") is None


def test_get_nutrient_config():
    config = get_nutrient_config("protein")
    assert config is not None
    assert config["unit"] == "g"
    assert "thresholds" in config


def test_high_protein_threshold():
    threshold = get_nutrient_threshold("protein", "high")
    assert threshold is not None
    assert threshold["operator"] == ">="
    assert threshold["value"] == 10.0


def test_low_sodium_threshold():
    threshold = get_nutrient_threshold("sodium", "low")
    assert threshold is not None
    assert threshold["operator"] == "<="
    assert threshold["value"] == 140.0


def test_low_sugar_threshold():
    threshold = get_nutrient_threshold("sugar", "low")
    assert threshold is not None
    assert threshold["operator"] == "<="


def test_alias_threshold_lookup():
    threshold = get_nutrient_threshold("carbs", "low")
    assert threshold is not None
    assert threshold["operator"] == "<="


def test_unknown_constraint_level():
    threshold = get_nutrient_threshold("protein", "medium")
    assert threshold is None


def test_nutrient_units():
    assert get_nutrient_unit("protein") == "g"
    assert get_nutrient_unit("sodium") == "mg"
    assert get_nutrient_unit("calories") == "kcal"