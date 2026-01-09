from fastapi import FastAPI
from pydantic import BaseModel
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CODA API Gateway")

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