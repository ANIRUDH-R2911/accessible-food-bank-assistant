import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from src.postprocessing.text_corrector import correct_text

sample = """
MI
Mlik
Honcy
Cheerlos
OATS
"""

print("RAW")
print(sample)

print("\nCORRECTED")
print(correct_text(sample))