# CODA Platform (Feb) — End-to-end Run Guide (Himalaya + Local Laptop)

This repo gives you a **demo pipeline**:

1) **UI** (browser) → user types **Natural Language (NL)** question  
2) UI calls **API Gateway** (`/query`)  
3) API Gateway calls **NL2SPARQL** (`/translate`) to get **SPARQL**  
4) API Gateway submits a **Vantage6 task** with the SPARQL as input  
5) **Node algorithm container** runs SPARQL against **GraphDB**  
6) Result comes back as a Vantage6 **task result** and is returned to UI/API caller.

---

## What you need running on Himalaya

### A) Vantage6 demo network (server + node)
You already have these containers running (example):
- `vantage6-serverdemo-system-server` (port **7601** mapped to server API)
- `vantage6-nodedemo-user` (node attached)
- Docker volumes like `vantage6-nodedemo-user-vol`

> If you ever need to recreate: `v6 dev create-demo-network` (not repeated here).

### B) GraphDB
Container `graphdb` exposing **7200** on Himalaya.

### C) UI + API Gateway + NL2SPARQL
Run with docker compose from this repo:
- UI on **8080**
- API Gateway on **8000**
- NL2SPARQL on **9000** (internal only)

---

## Terminals you should use

### Terminal-1 (Himalaya): check / start docker services
```bash
ssh lekha@<HIMALAYA_IP>
cd ~/coda-platform-feb
docker compose up -d --build
docker ps
```

### Terminal-2 (Himalaya): keep an eye on logs (optional but recommended)
```bash
ssh lekha@<HIMALAYA_IP>
cd ~/coda-platform-feb
docker compose logs -f api-gateway nl2sparql ui
```

### Terminal-3 (Your Laptop / Annapurna): SSH tunnels so you can open UI + GraphDB + API locally
```bash
# UI
ssh -N -L 8080:127.0.0.1:8080 lekha@<HIMALAYA_IP>

# API Gateway
ssh -N -L 8000:127.0.0.1:8000 lekha@<HIMALAYA_IP>

# GraphDB UI
ssh -N -L 7200:127.0.0.1:7200 lekha@<HIMALAYA_IP>
```

Now open in your **local browser**:
- UI: `http://127.0.0.1:8080`
- API health: `http://127.0.0.1:8000/health`
- GraphDB: `http://127.0.0.1:7200`

---

## Configure API Gateway → Vantage6 (IMPORTANT)

API Gateway must talk to the Vantage6 server **on Himalaya**.

Edit `api-gateway/.env` (or export env vars) on **Himalaya**:

```env
V6_SERVER_URL=http://127.0.0.1
V6_SERVER_PORT=7601
V6_API_PATH=/api
V6_USER=root
V6_PASSWORD=root
V6_COLLAB_ID=1
V6_ORG_ID=1
V6_IMAGE=raru123/aeh-sparql-runner:latest

# NL2SPARQL is another compose service (internal hostname)
NL2SPARQL_URL=http://nl2sparql:9000/translate
```

Then restart API Gateway:
```bash
cd ~/coda-platform-feb
docker compose restart api-gateway
docker compose logs -f api-gateway
```

---

## How to run end-to-end (NO curl SPARQL typing)

### Option 1 (Recommended demo): use UI
1. Open `http://127.0.0.1:8080`
2. Type a Natural Language question
3. UI calls `POST http://localhost:8000/query`
4. You see results on the page (and in logs)

### Option 2: call API Gateway from laptop (curl with NL, not SPARQL)
```bash
curl -s -X POST "http://127.0.0.1:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query":"show patient and visit and diagnosis name","wait":true}' | python3 -m json.tool
```

---

## Where the final result is stored in Himalaya

Even though UI/API returns it, the Vantage6 node also stores per-task data in the node volume:

```bash
# On Himalaya
docker volume inspect vantage6-nodedemo-user-vol | grep Mountpoint
sudo ls -lh /var/lib/docker/volumes/vantage6-nodedemo-user-vol/_data/task-0000000XXX
sudo cat /var/lib/docker/volumes/vantage6-nodedemo-user-vol/_data/task-0000000XXX/output
```

---

## Troubleshooting quick fixes

### Port already in use (8000/8080/9000)
```bash
# On Himalaya
ss -lntp | egrep ':8000|:8080|:9000'
docker compose ps
docker compose restart
```

### API Gateway returns 500
Check its logs:
```bash
docker compose logs -n 200 api-gateway
```

Most common reasons:
- Wrong Vantage6 URL/port (`V6_SERVER_PORT=7601`)
- Wrong collaboration/org id
- V6 task image name mismatch

### UI loads but shows error
Open browser devtools console and verify it calls:
- `http://localhost:8000/query`

---

## What endpoints exist

API Gateway:
- `GET /health` → status ok
- `POST /run` → run **SPARQL directly** (debug endpoint)
- `POST /query` → run **Natural Language** (UI uses this)

NL2SPARQL:
- `POST /translate` → returns `{ "sparql": "..." }`
