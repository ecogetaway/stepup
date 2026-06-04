from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import settings
from ingestion.pipeline import run_pipeline


def main() -> None:
    print(f"Running ingestion for {settings.APP_NAME} in {settings.APP_ENV} mode")
    run_pipeline()


if __name__ == "__main__":
    main()
