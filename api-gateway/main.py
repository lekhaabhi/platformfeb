from fastapi import FastAPI # type: ignore
from pydantic import BaseModel
import requests

app = FastAPI(title="CODA API Gateway")

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def health_check():
    return {"status": "API Gateway running"}

@app.post("/query")
def handle_query(req: QueryRequest):
    # Call NL → SPARQL service
    resp = requests.post(
        "http://nl2sparql:9000/translate",
        json={"query": req.query},
        timeout=5
    )

    translation = resp.json()

    return {
        "nl_query": req.query,
        "sparql": translation["sparql"],
        "translation_status": translation["status"]
    }
