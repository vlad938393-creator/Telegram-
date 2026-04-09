from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config import get_settings
from src.database import Database


def main() -> None:
    load_dotenv()
    settings = get_settings()
    database_path = Path(settings.database_path)
    Database(database_path)  # initialization seeds data
    print(f"База данных инициализирована по пути: {database_path.resolve()}")


if __name__ == "__main__":
    main()

