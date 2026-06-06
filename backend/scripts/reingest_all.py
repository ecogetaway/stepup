from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.pipeline import run_pipeline
from scripts.generate_sample_data import main as generate_sops
from scripts.generate_tickets import main as generate_tickets


def main() -> None:
    print("Generating sample SOP PDFs...")
    generate_sops()
    print("Generating sample tickets CSV...")
    generate_tickets()
    print("Running full ingestion pipeline (SOPs, IT docs, tickets)...")
    run_pipeline()
    print("Reingest complete.")


if __name__ == "__main__":
    main()
