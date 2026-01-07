from fastapi import FastAPI # type: ignore
from pydantic import BaseModel

app = FastAPI(title="NL to SPARQL Service")

class NLQuery(BaseModel):
    query: str

@app.post("/translate")
def translate(nl: NLQuery):
    text = nl.query.lower()

    if "oct" in text:
        sparql = """
        SELECT ?patient ?image
        WHERE {
            ?patient :hasOCT ?image .
        }
        """
    else:
        sparql = "SELECT * WHERE { ?s ?p ?o } LIMIT 10"

    return {
        "sparql": sparql,
        "status": "SUCCESS"
    }
