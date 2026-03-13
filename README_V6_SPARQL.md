# CODA: SPARQL through Vantage6 (Demo)

This repo contains:

- `v6-sparql-algorithm/` – the Vantage6 algorithm container code that sends SPARQL to GraphDB
- `api-gateway/` – a small FastAPI server that accepts a SPARQL query and **submits a Vantage6 task**
- helper scripts: `run_task.py`, `get_result.py`

## 1) Open GraphDB UI in your local browser (SSH tunnel)

GraphDB UI is running on **Himalaya** on port **7200** (as seen in `docker ps`).

From your **local laptop** (Annapurna or Windows), run:

```bash
ssh -L 7300:127.0.0.1:7200 lekha@117.251.28.255
```

Then open in your local browser:

- http://localhost:7300/

> Why 7300?  
> Port `7200` is already used on many machines; we forward local `7300` -> remote `7200`.
> You can choose any free local port.

## 2) Where to see algorithm output

When a task runs, the node writes input/output under the node **user volume**:

```bash
sudo ls -lh /var/lib/docker/volumes/vantage6-nodedemo-user-vol/_data/task-000000011
sudo cat /var/lib/docker/volumes/vantage6-nodedemo-user-vol/_data/task-000000011/output
```

## 3) Run a task (manual Python)

On **Himalaya**:

```bash
source demo/bin/activate
python run_task.py
python get_result.py <TASK_ID>
```

## 4) Run the API gateway (automated)

On **Himalaya**:

```bash
source demo/bin/activate
pip install -r api-gateway/requirements.txt

# run the API
uvicorn api-gateway.main:app --host 127.0.0.1 --port 9000
```

Test:

```bash
curl -s http://127.0.0.1:9000/health
curl -s -X POST "http://127.0.0.1:9000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "PREFIX ex: <http://example.org/schema#>\nSELECT ?patient ?visit ?diagnosisName WHERE { ?patient a ex:Patient ; ex:hasVisit ?visit . ?visit ex:hasDiagnosis ?d . ?d ex:diagnosisName ?diagnosisName . } LIMIT 10",
    "repository": "feb-sample",
    "wait": true
  }' | python3 -m json.tool
```

### Call the API from your local machine (Annapurna)

If you want to call it from your local browser/terminal, create an SSH tunnel:

```bash
ssh -L 9000:127.0.0.1:9000 lekha@117.251.28.255
```

Then from local:

```bash
curl -s http://127.0.0.1:9000/health
```

## 5) Notes

- This demo assumes your Vantage6 server is reachable at `http://localhost:7601` on Himalaya.
- If you run the API gateway in a different environment, set:
  - `V6_SERVER_URL`, `V6_SERVER_PORT`, `V6_API_PATH`, `V6_USER`, `V6_PASSWORD`, `V6_COLLAB_ID`, `V6_ORG_ID`, `V6_IMAGE`
