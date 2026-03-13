import base64
import json
import sys
from vantage6.client import Client

if len(sys.argv) < 2:
    print("Usage: python get_result.py <TASK_ID>")
    sys.exit(1)

TASK_ID = int(sys.argv[1])

c = Client("http://localhost", 7601, "/api", log_level="info")
c.authenticate("root", "root")
c.setup_encryption(None)

t = c.task.get(TASK_ID)
print("Task ID:", TASK_ID)
print("Task status:", t.get("status"))
print("Task complete:", t.get("complete"))

# Fetch results (robust across v6 versions)
resp = c.request("GET", "result", params={"task_id": TASK_ID})
results = resp["data"] if isinstance(resp, dict) and "data" in resp else resp

print("Num results:", len(results))

decoded = []
for r in results:
    blob = r.get("result") if isinstance(r, dict) else r
    try:
        s = base64.b64decode(blob).decode("utf-8")
        decoded.append(json.loads(s))
    except Exception:
        try:
            decoded.append(json.loads(blob))
        except Exception:
            decoded.append({"raw": blob})

print("\n--- DECODED RESULTS ---\n")
for i, d in enumerate(decoded, 1):
    print(f"Result #{i}:")
    print(json.dumps(d, indent=2))
