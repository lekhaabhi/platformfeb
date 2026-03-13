import json
import os
import sys

from algorithm import sparql_query


def read_input(input_path: str) -> dict:
    with open(input_path, "r") as f:
        return json.load(f)


def write_output(output_path: str, obj) -> None:
    with open(output_path, "w") as f:
        json.dump(obj, f)


def main():
    # Vantage6 passes these env vars into the container
    input_file = os.getenv("INPUT_FILE")
    output_file = os.getenv("OUTPUT_FILE")

    # Debug prints – you saw these as [ALG] lines in the node log
    print(f"[ALG] INPUT_FILE={input_file}", flush=True)
    print(f"[ALG] OUTPUT_FILE={output_file}!!!!!!", flush=True)

    if not input_file or not output_file:
        print("[ALG] ERROR: INPUT_FILE or OUTPUT_FILE not set!", file=sys.stderr, flush=True)
        sys.exit(1)

    payload = read_input(input_file)
    method = payload.get("method")
    args = payload.get("args", [])
    kwargs = payload.get("kwargs", {})

    if method != "sparql_query":
        print(f"[ALG] ERROR: Unsupported method '{method}'", file=sys.stderr, flush=True)
        sys.exit(1)

    query = kwargs.get("query", "")
    if not query.strip():
        print("[ALG] ERROR: Empty SPARQL query!", file=sys.stderr, flush=True)
        sys.exit(1)

    # Call the algorithm function
    try:
        result = sparql_query(query)
    except Exception as e:
        print(f"[ALG] ERROR during SPARQL execution: {e}", file=sys.stderr, flush=True)
        # You can also write a JSON error result if you like
        write_output(output_file, {"error": str(e)})
        sys.exit(1)

    # Write successful result for the node to pick up
    write_output(output_file, result)
    print(f"[ALG] Wrote result to {output_file}!!!!!!", flush=True)


if __name__ == "__main__":
    main()

