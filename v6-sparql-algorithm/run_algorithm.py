import os
import sys
import glob
import json
import traceback
import requests

GRAPHDB_REPO_URL = os.environ.get(
    "GRAPHDB_REPO_URL",
    "http://172.17.0.1:7200/repositories/feb-sample"
)

SQUID_PROXY_URL = os.environ.get("SQUID_PROXY_URL", "http://squid:3128")


def log(msg: str) -> None:
    print(f"[ALG] {msg}")
    sys.stdout.flush()


def find_task_file(basename: str, root="/mnt/data"):
    pattern = os.path.join(root, "task-*", basename)
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def resolve_io():
    raw_in = os.environ.get("INPUT_FILE")
    raw_out = os.environ.get("OUTPUT_FILE")

    log(f"RAW INPUT_FILE env  = {raw_in}")
    log(f"RAW OUTPUT_FILE env = {raw_out}")

    input_path = find_task_file("input")
    output_path = find_task_file("output")

    log(f"Resolved INPUT path  = {input_path}")
    log(f"Resolved OUTPUT path = {output_path}")

    return input_path, output_path


def read_input(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.loads(f.read())
    except Exception as e:
        log(f"Failed to read input: {e}")
        traceback.print_exc()
        return None


def write_output(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        log(f"Wrote result JSON to {path}")
    except Exception as e:
        log(f"Failed to write output: {e}")
        traceback.print_exc()


def extract_query(payload):
    kwargs = payload.get("kwargs", {})
    if "query" in kwargs:
        return kwargs["query"]
    return None


def run_sparql(query):
    log(f"Sending SPARQL to {GRAPHDB_REPO_URL} via proxy {SQUID_PROXY_URL}")
    try:
        session = requests.Session()
        session.trust_env = False

        proxies = {
            "http": SQUID_PROXY_URL,
            "https": SQUID_PROXY_URL,
        }

        resp = session.post(
            GRAPHDB_REPO_URL,
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=60,
            proxies=proxies,  # <-- FIXED
        )

        log(f"GraphDB HTTP status: {resp.status_code}")
        resp.raise_for_status()
        return {"ok": True, "results": resp.json()}

    except Exception as e:
        log(f"SPARQL failed: {e}")
        traceback.print_exc()
        return {"ok": False, "error": str(e)}


def main():
    input_path, output_path = resolve_io()
    if not input_path or not output_path:
        log("Missing IO paths!")
        return

    payload = read_input(input_path)
    query = extract_query(payload)

    if not query:
        write_output(output_path, {"ok": False, "error": "No query in input"})
        return

    result = run_sparql(query)
    write_output(output_path, result)
    log("Done.")


if __name__ == "__main__":
    main()

