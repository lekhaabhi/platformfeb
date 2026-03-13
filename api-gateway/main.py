# Backward-compatible entrypoint for uvicorn:
#   uvicorn main:app --host 0.0.0.0 --port 9000
from query_api import app  # noqa: F401
