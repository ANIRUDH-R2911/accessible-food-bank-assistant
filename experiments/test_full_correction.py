import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.postprocessing.text_corrector import (
    correct_text,
    generate_correction_report
)

raw_text = """
Ingredients
Whole Grain Oats
Sodlum 180mg
Viamin D
Contains Wheat
"""

print("\nRAW OCR OUTPUT")
print("-" * 50)
print(raw_text)

corrected_text = correct_text(raw_text)

print("\nCORRECTED OCR OUTPUT")
print("-" * 50)
print(corrected_text)

print("\nCORRECTION REPORT")
print("-" * 50)

report = generate_correction_report(raw_text)

for item in report:

    print(
        f"{item['original']:15}"
        f" -> "
        f"{item['corrected']:15}"
        f" | Score: {item['score']:6}"
        f" | Changed: {item['changed']}"
    )