import json


def compare_nutrition(expected, predicted):
    missing_fields = []
    incorrect_fields = []
    correct_fields = []
    for key, expected_value in expected.items():
        if key not in predicted:
            missing_fields.append(key)
            continue
        predicted_value = predicted[key]
        if predicted_value == expected_value:
            correct_fields.append(key)
        else:
            incorrect_fields.append((key, expected_value, predicted_value))

    extra_fields = []
    for key in predicted:
        if key not in expected:
            extra_fields.append(key)

    return (
        correct_fields,
        missing_fields,
        incorrect_fields,
        extra_fields
    )


def main():
    with open(
        "data/evaluation_dataset.json",
        "r",
        encoding="utf-8"
    ) as f:
        dataset = json.load(f)

    total_expected = 0
    total_correct = 0

    missing_counter = {}
    incorrect_counter = {}

    print("\n" + "----" * 40)
    print("NUTRITION ERROR REPORT")
    print("----" * 40)
    for item in dataset:
        image_name = item["image_name"]
        expected = item.get("expected_nutrition", {})
        predicted = item.get("predicted_nutrition", {})

        (correct_fields, missing_fields, incorrect_fields, extra_fields) = compare_nutrition(expected, predicted)
        total_expected += len(expected)
        total_correct += len(correct_fields)

        for field in missing_fields:
            missing_counter[field] = (missing_counter.get(field, 0) + 1)

        for field, _, _ in incorrect_fields:
            incorrect_counter[field] = (incorrect_counter.get(field, 0) + 1)

        print("\n" + "-" * 40)
        print(f"IMAGE: {image_name}")
        print("-" * 40)

        print("\nEXPECTED:")
        print(json.dumps(expected, indent=4))

        print("\nPREDICTED:")
        print(json.dumps(predicted, indent=4))

        print("\nCORRECT FIELDS:")
        print(
            correct_fields
            if correct_fields
            else "None"
        )

        print("\nMISSING FIELDS:")
        print(
            missing_fields
            if missing_fields
            else "None"
        )

        print("\nINCORRECT FIELDS:")

        if incorrect_fields:
            for (field, expected_value, predicted_value) in incorrect_fields:
                print(
                    f"{field}: "
                    f"expected={expected_value}, "
                    f"predicted={predicted_value}"
                )
        else:
            print("None")

        print("\nEXTRA FIELDS:")
        print(
            extra_fields
            if extra_fields
            else "None"
        )

    accuracy = (
        total_correct / total_expected
        if total_expected > 0
        else 0
    )

    print("\n" + "-" * 40)
    print("SUMMARY")
    print("-" * 40)
    print(f"\nTotal Expected Fields: " f"{total_expected}")
    print(f"Total Correct Fields: " f"{total_correct}")
    print(f"Field Accuracy: "f"{accuracy:.4f}")

    print("\nMOST COMMON MISSING FIELDS:")
    for field, count in sorted(missing_counter.items(),key=lambda x: x[1],reverse=True):
        print(f"{field}: {count}")

    print("\nMOST COMMON INCORRECT FIELDS:")
    for field, count in sorted(incorrect_counter.items(),key=lambda x: x[1], reverse=True):
        print(f"{field}: {count}")

if __name__ == "__main__":
    main()