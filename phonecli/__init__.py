# phonecli — Coordinate-based phone agent with CLI abstraction layer.

import os
from pathlib import Path


def _load_dotenv(path: str = None):
    """Load KEY=VALUE pairs from a .env file into os.environ.

    Searches (in order):
      1. *path* argument
      2. PHONECLI_ENV environment variable
      3. .env in the current working directory
      4. .env in the phonecli package directory
    """
    candidates = []
    if path:
        candidates.append(path)
    if os.getenv("PHONECLI_ENV"):
        candidates.append(os.getenv("PHONECLI_ENV"))
    candidates.append(".env")
    candidates.append(str(Path(__file__).parent.parent / ".env"))

    for candidate in candidates:
        p = Path(candidate)
        if not p.is_file():
            continue
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except Exception:
            pass


# Auto-load .env on import (only sets vars that aren't already in the environment)
_load_dotenv()
