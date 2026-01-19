from fastapi import FastAPI
from pydantic import BaseModel
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CODA API Gateway")

GRAPHDB_ENDPOINT = "http://graphdb:7200/repositories/feb-sample"

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Lets allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def health_check():
    return {"status": "API Gateway running"}

@app.post("/query")
def handle_query(req: QueryRequest):
    resp = requests.post(
        "http://nl2sparql:9000/translate",
        json={"query": req.query},
        timeout=5
    )

    translation = resp.json()

    return {
        "nl_query": req.query,
        "sparql": translation["sparql"],
        "status": translation["status"]
    }

@app.get("/test-graph")
def test_graphdb():
    sparql_query = """
    PREFIX ex: <http://example.org/schema#>

    SELECT ?patient ?diagnosis
    WHERE {
        ?patient a ex:Patient ;
                ex:hasVisit ?visit .
        ?visit ex:hasDiagnosis ?diagnosis .
    }
    LIMIT 10
    """

    headers = {
        "Accept": "application/sparql+json",
        "Content-Type": "application/sparql-query"
    }

    response = requests.post(
        GRAPHDB_ENDPOINT,
        data=sparql_query,
        headers=headers
    )

    return response.json()