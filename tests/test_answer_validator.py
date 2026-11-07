import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

import pytest
from src.rag.answer_validator import AnswerValidator

@pytest.fixture
def validator():
    return AnswerValidator()

@pytest.fixture
def inventory_record():
    return {
        "item_id": "FBA-SEC-001",
        "ingredients": ["oats"],
        "contains_allergens": [],
        "may_contain": ["peanuts"],
        "nutrition": {
            "protein": 5,
            "sugar": 2,
        },
    }

def test_accepts_answer_with_supported_nutrition(validator, inventory_record):
    answer = "Item FBA-SEC-001 contains 5g of protein."
    assert validator.validate(answer, [inventory_record]) is True

def test_rejects_contradictory_nutrition_claim(validator, inventory_record):
    answer = "Item FBA-SEC-001 contains 25g of protein."
    assert validator.validate(answer, [inventory_record]) is False

def test_rejects_unsupported_ingredient_claim(validator, inventory_record):
    answer = "Item FBA-SEC-001 contains oats, milk, and almonds."
    assert validator.validate(answer, [inventory_record]) is False

def test_rejects_allergen_free_claim_when_may_contain_is_recorded(validator, inventory_record):
    answer = "Item FBA-SEC-001 is completely peanut-free."
    assert validator.validate(answer, [inventory_record]) is False

def test_rejects_allergy_safety_claim_when_allergen_is_recorded(validator, inventory_record):
    answer = "Item FBA-SEC-001 is safe for people with peanut allergies."
    assert validator.validate(answer, [inventory_record]) is False

def test_rejects_unknown_item_id(validator, inventory_record):
    answer = "Item FBA-SEC-999 contains 5g of protein."
    assert validator.validate(answer, [inventory_record]) is False

def test_accepts_answer_with_matching_item_id(validator, inventory_record):
    answer = "Item FBA-SEC-001 contains oats."
    assert validator.validate(answer, [inventory_record]) is True

def test_accepts_unavailable_nutrition_as_unavailable(validator, inventory_record):
    inventory_record["nutrition"]["protein"] = None
    answer = "Protein information is unavailable for item FBA-SEC-001."
    assert validator.validate(answer, [inventory_record]) is True

def test_rejects_empty_answer(validator, inventory_record):
    assert validator.validate("", [inventory_record]) is False

def test_rejects_answer_without_inventory_evidence(validator):
    answer = "Item FBA-SEC-001 contains 5g of protein."
    assert validator.validate(answer, []) is False

@pytest.mark.parametrize(
    "answer",
    [
        "Item FBA-SEC-001 is peanut-free.",
        "Item FBA-SEC-001 is peanuts-free.",
        "Item FBA-SEC-001 is free of peanut.",
        "Item FBA-SEC-001 does not contain peanuts.",
    ],
)

def test_rejects_singular_and_plural_allergen_free_claims(validator, inventory_record, answer):
    assert validator.validate(answer, [inventory_record]) is False

@pytest.mark.parametrize("field", ["contains_allergens", "may_contain"])
def test_rejects_allergen_free_claim_for_both_allergen_fields(validator, inventory_record, field):
    inventory_record["contains_allergens"] = []
    inventory_record["may_contain"] = []
    inventory_record[field] = ["peanuts"]
    answer = "Item FBA-SEC-001 is peanut-free."
    assert validator.validate(answer, [inventory_record]) is False

def test_accepts_answer_that_only_mentions_an_allergen(validator, inventory_record):
    answer = "Item FBA-SEC-001 may contain peanuts."
    assert validator.validate(answer, [inventory_record]) is True

def test_rejects_numeric_nutrition_claim_when_value_is_unavailable(validator, inventory_record):
    inventory_record["nutrition"]["protein"] = None
    answer = "Item FBA-SEC-001 contains 10g of protein."
    assert validator.validate(answer, [inventory_record]) is False

def test_accepts_unavailable_nutrition_statement(validator, inventory_record):
    inventory_record["nutrition"]["protein"] = None
    answer = "Protein information is unavailable for item FBA-SEC-001."
    assert validator.validate(answer, [inventory_record]) is True

def test_accepts_multiple_known_item_ids(validator, inventory_record):
    second_record = {
        "item_id": "FBA-SEC-002",
        "ingredients": ["rice"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {},
    }
    answer = "Items FBA-SEC-001 and FBA-SEC-002 are in the inventory."
    assert validator.validate(answer, [inventory_record, second_record]) is True

def test_rejects_unknown_id_among_multiple_known_item_ids(validator, inventory_record):
    second_record = {
        "item_id": "FBA-SEC-002",
        "ingredients": ["rice"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {},
    }
    answer = "Items FBA-SEC-001 and FBA-SEC-999 are in the inventory."
    assert validator.validate(answer, [inventory_record, second_record]) is False


def test_validates_nutrition_claims_against_the_correct_item(validator):
    records = [
        {
            "item_id": "FBA-SEC-001",
            "ingredients": ["oats"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {"protein": 5},
        },
        {
            "item_id": "FBA-SEC-002",
            "ingredients": ["rice"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {"protein": 20},
        },
    ]
    answer = ("Item FBA-SEC-001 contains 5g of protein. Item FBA-SEC-002 contains 20g of protein.")
    assert validator.validate(answer, records) is True

def test_rejects_wrong_nutrition_value_for_specific_item(validator):
    records = [
        {
            "item_id": "FBA-SEC-001",
            "ingredients": ["oats"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {"protein": 5},
        },
        {
            "item_id": "FBA-SEC-002",
            "ingredients": ["rice"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {"protein": 20},
        },
    ]
    answer = ("Item FBA-SEC-001 contains 25g of protein. Item FBA-SEC-002 contains 20g of protein.")
    assert validator.validate(answer, records) is False

def test_rejects_allergen_free_claim_when_no_allergen_is_recorded(validator):
    records = [
        {
            "item_id": "FBA-SEC-001",
            "ingredients": ["oats"],
            "contains_allergens": [],
            "may_contain": ["peanuts"],
            "nutrition": {},
        },
        {
            "item_id": "FBA-SEC-002",
            "ingredients": ["rice"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {},
        },
    ]
    answer = "Item FBA-SEC-002 is peanut-free."
    assert validator.validate(answer, records) is False

def test_rejects_allergen_free_claim_for_the_correct_item(validator):
    records = [
        {
            "item_id": "FBA-SEC-001",
            "ingredients": ["oats"],
            "contains_allergens": [],
            "may_contain": ["peanuts"],
            "nutrition": {},
        },
        {
            "item_id": "FBA-SEC-002",
            "ingredients": ["rice"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {},
        },
    ]
    answer = "Item FBA-SEC-001 is peanut-free."
    assert validator.validate(answer, records) is False

def test_ingredient_claim_is_checked_against_the_correct_item(validator):
    records = [
        {
            "item_id": "FBA-SEC-001",
            "ingredients": ["oats"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {},
        },
        {
            "item_id": "FBA-SEC-002",
            "ingredients": ["rice"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {},
        },
    ]
    answer = "Item FBA-SEC-002 contains rice."
    assert validator.validate(answer, records) is True

def test_rejects_ingredient_from_another_item(validator):
    records = [
        {
            "item_id": "FBA-SEC-001",
            "ingredients": ["oats"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {},
        },
        {
            "item_id": "FBA-SEC-002",
            "ingredients": ["rice"],
            "contains_allergens": [],
            "may_contain": [],
            "nutrition": {},
        },
    ]
    answer = "Item FBA-SEC-002 contains oats."
    assert validator.validate(answer, records) is False

def test_rejects_peanut_free_claim_when_allergen_information_is_empty(validator):
    record = {
        "item_id": "FBA-SEC-020",
        "ingredients": ["rice"],
        "contains_allergens": [],
        "may_contain": [],
        "nutrition": {},
    }
    answer = "Item FBA-SEC-020 is peanut-free."
    assert validator.validate(answer, [record]) is False


def test_rejects_allergy_safety_claim_when_allergen_information_is_missing(validator):
    record = {
        "item_id": "FBA-SEC-021",
        "ingredients": ["rice"],
        "nutrition": {},
    }
    answer = "Item FBA-SEC-021 is safe for people with peanut allergies."
    assert validator.validate(answer, [record]) is False
