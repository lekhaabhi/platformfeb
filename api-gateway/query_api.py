import base64
import json
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import requests

# Vantage6 client
from vantage6.client import Client


app = FastAPI(title="CODA SPARQL API Gateway", version="1.0.0")


class RunRequest(BaseModel):
    query: str = Field(..., description="SPARQL query string")
    repository: str = Field("feb-sample", description="GraphDB repository name")
    wait: bool = Field(True, description="Wait for results before responding")
    timeout_sec: int = Field(120, ge=5, le=3600, description="Max seconds to wait when wait=true")
    limit_results: int = Field(50, ge=1, le=5000, description="Safety cap for response size")


class RunResponse(BaseModel):
    task_id: int
    status: str
    results: Optional[List[Dict[str, Any]]] = None


class NLQueryRequest(BaseModel):
    """Natural-language query coming from the web UI."""

    query: str = Field(..., description="Natural language question")
    wait: bool = Field(True, description="Wait for results before responding")
    timeout_sec: int = Field(120, ge=5, le=3600, description="Max seconds to wait when wait=true")


class NLQueryResponse(BaseModel):
    sparql: str
    task_id: int
    status: str
    results: Optional[List[Dict[str, Any]]] = None


def _nl_to_sparql(nl_query: str) -> str:
    """Convert NL -> SPARQL by calling the NL2SPARQL service.

    Expected NL2SPARQL response shapes we handle:
      - {"sparql": "..."}
      - {"query": "..."}  (some services name the key 'query')
      - {"sparql_query": "..."}
    """
    url = os.getenv("NL2SPARQL_URL", "http://127.0.0.1:8000/translate")
    try:
        r = requests.post(url, json={"query": nl_query}, timeout=30)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Failed to reach NL2SPARQL at {url}: {e}")

    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"NL2SPARQL error {r.status_code}: {r.text}")

    try:
        payload = r.json()
    except ValueError:
        raise HTTPException(status_code=502, detail=f"NL2SPARQL returned non-JSON: {r.text[:500]}")

    for k in ("sparql", "query", "sparql_query"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v

    raise HTTPException(status_code=502, detail=f"NL2SPARQL response missing SPARQL string. Keys: {list(payload.keys())}")


def _get_env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if not v:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _v6_client() -> Client:
    # NOTE:
    # - If you run this API on Himalaya host: use default http://localhost:7601
    # - If you run inside docker: set V6_SERVER_URL accordingly (e.g., http://<host-ip>:7601)
    server_url = os.getenv("V6_SERVER_URL", "http://127.0.0.1")
    port = _get_env_int("V6_SERVER_PORT", 7601)
    api_path = os.getenv("V6_API_PATH", "/api")

    user = os.getenv("V6_USER", "root")
    password = os.getenv("V6_PASSWORD", "root")

    c = Client(server_url, port, api_path, log_level=os.getenv("V6_LOG_LEVEL", "info"))
    c.authenticate(user, password)

    # In your setup encryption is disabled, so keep it disabled here too
    c.setup_encryption(None)
    return c


def _wait_for_task(c: Client, task_id: int, timeout_sec: int) -> Dict[str, Any]:
    start = time.time()
    while True:
        t = c.task.get(task_id)
        # different v6 versions expose completion differently; check both
        status = t.get("status") or ("completed" if t.get("complete") else None)
        if status in ("completed", "complete", "finished"):
            return t
        if time.time() - start > timeout_sec:
            return t
        time.sleep(2)


def _fetch_results(c: Client, task_id: int) -> List[Dict[str, Any]]:
    # v6 client API differs between versions, so try a few known methods.
    # Ultimately we want the list returned by GET /api/result?task_id=<id>
    if hasattr(c, "result") and hasattr(c.result, "list"):
        return c.result.list(task=task_id)  # older signature (some versions)
    if hasattr(c, "result") and hasattr(c.result, "list_results"):
        return c.result.list_results(task_id=task_id)  # hypothetical
    if hasattr(c, "result") and hasattr(c.result, "get"):
        # some versions: get(task=task_id) returns list
        try:
            r = c.result.get(task=task_id)
            if isinstance(r, list):
                return r
        except TypeError:
            pass

    # Fallback: raw HTTP call through the client.
    # Note: if the server replies with HTML (e.g., 404) the client may raise a
    # JSON decode error. We'll try a couple of endpoint names and then fail
    # with a clear message.
    last_error: Optional[Exception] = None
    for endpoint in ("result", "results"):
        try:
            resp = c.request("GET", endpoint, params={"task_id": task_id})
        except Exception as e:
            last_error = e
            continue

        if isinstance(resp, dict) and "data" in resp:
            return resp["data"]
        if isinstance(resp, list):
            return resp

    hint = (
        "Could not fetch task results from the Vantage6 server. "
        "Check V6_SERVER_URL/V6_SERVER_PORT/V6_API_PATH (should usually be '/api'), "
        "and verify the server is reachable (try: curl -s http://127.0.0.1:7601/api/version)."
    )
    if last_error:
        raise RuntimeError(f"{hint} Last error: {type(last_error).__name__}: {last_error}")
    raise RuntimeError(hint)


def _decode_result_blob(blob: Any) -> Dict[str, Any]:
    # Your algorithm returns base64 of a JSON string.
    # Sometimes the client already returns decoded dict; handle both.
    if isinstance(blob, dict):
        return blob
    if not isinstance(blob, str):
        return {"raw": blob}

    try:
        decoded = base64.b64decode(blob).decode("utf-8")
        return json.loads(decoded)
    except Exception:
        # Maybe it's already a JSON string, not base64
        try:
            return json.loads(blob)
        except Exception:
            return {"raw": blob}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
def run_query(req: RunRequest):
    # Create a Vantage6 task that will be executed by the node.
    c = _v6_client()

    collab_id = _get_env_int("V6_COLLAB_ID", 1)
    org_id = _get_env_int("V6_ORG_ID", 1)
    image = os.getenv("V6_IMAGE", "raru123/aeh-sparql-runner:latest")

    # Pass repository to algorithm (optional)
    input_kwargs = {"query": req.query, "repository": req.repository}

    task = c.task.create(
        organizations=[org_id],
        collaboration=collab_id,
        name="sparql-runner-api",
        image=image,
        description="SPARQL query submitted via API gateway",
        input_={"kwargs": input_kwargs},
    )

    # Some versions return {"id": ...}, others nest under "data"
    task_id = task.get("id") or task.get("data", {}).get("id")
    if not task_id:
        raise HTTPException(status_code=500, detail=f"Could not read task id from response: {task}")

    if not req.wait:
        return RunResponse(task_id=int(task_id), status="submitted", results=None)

    t = _wait_for_task(c, int(task_id), req.timeout_sec)
    status = t.get("status") or ("completed" if t.get("complete") else "unknown")

    results_raw = _fetch_results(c, int(task_id))

    decoded_results: List[Dict[str, Any]] = []
    for r in results_raw:
        # r can be dict with key "result" containing base64
        if isinstance(r, dict):
            blob = r.get("result")
            decoded = _decode_result_blob(blob)
            # attach run_id to be helpful
            decoded_results.append({
                "run_id": (r.get("run") or {}).get("id") if isinstance(r.get("run"), dict) else r.get("id"),
                "output": decoded
            })
        else:
            decoded_results.append({"output": _decode_result_blob(r)})

    # Safety cap
    decoded_results = decoded_results[: req.limit_results]

    return RunResponse(task_id=int(task_id), status=str(status), results=decoded_results)


@app.post("/query", response_model=NLQueryResponse)
def query_from_nl(req: NLQueryRequest):
    """Accept natural language, translate to SPARQL using NL2SPARQL, then execute via Vantage6.

    This matches the demo UI which expects a single API call.
    """
    sparql = _nl_to_sparql(req.query)
    run_req = RunRequest(query=sparql, wait=req.wait)
    run_resp: RunResponse = run_query(run_req)  # reuse the same logic
    return NLQueryResponse(sparql=sparql, task_id=run_resp.task_id, status=run_resp.status, results=run_resp.results)
