import sys
from pathlib import Path

# The FastAPI package lives in backend/ (module "app"), mirroring how
# uvicorn is run from that directory.
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
