"""Render only the source pages needed for the species feasibility audit."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
POPPLER = Path(r"C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe")
OUT = ROOT / "tmp" / "pdfs" / "species_feasibility"
OUT.mkdir(parents=True, exist_ok=True)

jobs = [
    ("etosha_aerial_census_2015.pdf", 5, 12, "census"),
    ("etosha_aerial_census_2015.pdf", 16, 16, "distribution"),
    ("nature_conservation_annotated_tradeportal.pdf", 78, 80, "law"),
    ("nature_conservation_annotated_tradeportal.pdf", 83, 84, "plants_law"),
]
for filename, first, last, prefix in jobs:
    subprocess.run(
        [str(POPPLER), "-f", str(first), "-l", str(last), "-scale-to", "1800",
         "-png", str(ROOT / "data" / "species" / "raw" / filename), str(OUT / prefix)],
        check=True, capture_output=True,
    )
print(f"Rendered {sum(last - first + 1 for _, first, last, _ in jobs)} source pages to {OUT}")
