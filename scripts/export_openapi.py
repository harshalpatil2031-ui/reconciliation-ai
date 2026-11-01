"""Export the canonical FastAPI OpenAPI document to contracts/openapi.json."""

import json
from pathlib import Path

from backend.main import app

destination = Path(__file__).resolve().parents[1] / "contracts" / "openapi.json"
destination.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
print(f"Wrote {destination}")
