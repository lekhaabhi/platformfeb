import time
from vantage6.client import Client

# Run on Himalaya (same machine where v6 server is mapped to port 7601)
c = Client("http://localhost", 7601, "/api", log_level="info")
c.authenticate("root", "root")
c.setup_encryption(None)

COLLAB_ID = 1
ORG_ID = 1  # node org is root in your demo network
IMAGE = "raru123/aeh-sparql-runner:latest"

query = """PREFIX ex: <http://example.org/schema#>
SELECT ?patient ?visit ?diagnosisName
WHERE {
    ?patient a ex:Patient ;
             ex:hasVisit ?visit .
    ?visit ex:hasDiagnosis ?d .
    ?d ex:diagnosisName ?diagnosisName .
}
LIMIT 10
"""

task = c.task.create(
    organizations=[ORG_ID],
    collaboration=COLLAB_ID,
    name="sparql-runner-cli",
    image=IMAGE,
    description="Run SPARQL via vantage6 node",
    input_={"kwargs": {"query": query, "repository": "feb-sample"}},
)

tid = task["id"]
print("Created task id:", tid)

while True:
    t = c.task.get(tid)
    if (t.get("status") == "completed") or t.get("complete") is True:
        break
    time.sleep(2)

print("Task completed. Now run:")
print(f"  python get_result.py {tid}")
