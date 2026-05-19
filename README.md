# ♠️ Poker Coach

A Monte Carlo–powered poker hand analyzer and bankroll tracker.  
**Not a GTO/Nash solver** — simplified ranges + MC simulation for learning and leak detection.

---

## Quick Start (Local)

### 1. Install Dependencies (Python 3.11+ required)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set a strong SECRET_KEY
```

### 3. Run the API (Terminal 1)

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 4. Run the UI (Terminal 2)

```bash
streamlit run ui/app.py --server.port 8501
```

Open http://localhost:8501

---

## Docker (one command)

```bash
cp .env.example .env   # set SECRET_KEY
docker compose up --build
```

- UI:  http://localhost:8501
- API: http://localhost:8000

---

## Deploy to Railway (~10 min)

### Step 1 — Push to GitHub

```bash
git init && git add . && git commit -m "Initial commit"
gh repo create poker-coach --private --push
```

### Step 2 — API service on Railway

1. railway.app → New Project → Deploy from GitHub
2. Dockerfile: `Dockerfile.api`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Env vars:
   - `SECRET_KEY` — run `python -c "import secrets; print(secrets.token_hex(32))"`
   - `DATABASE_URL` — leave blank for SQLite, or add Railway PostgreSQL plugin
5. Deploy → copy your API URL

### Step 3 — UI service on Railway

1. Same project → New Service → same GitHub repo
2. Dockerfile: `Dockerfile.ui`
3. Start command: `streamlit run ui/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
4. Env vars:
   - `API_BASE` = your API URL from Step 2 (e.g. `https://api-xxx.railway.app`)
5. Deploy → open UI URL

---

## Deploy to Render

**API service:** Docker, `Dockerfile.api`, env vars: `SECRET_KEY`, `DATABASE_URL`  
**UI service:** Docker, `Dockerfile.ui`, env vars: `API_BASE`

---

## Project Structure

```
poker-coach/
├── gto_advisor/      # Monte Carlo engine: evaluator, ranges, preflop, postflop
├── app/              # FastAPI backend
│   ├── main.py
│   ├── config.py     # Reads .env
│   ├── db/           # SQLAlchemy ORM models
│   ├── api/routers/  # auth, tables, sessions, hands, stats
│   └── services/     # advisor, alignment, bankroll, stats logic
├── ui/               # Streamlit frontend
│   ├── app.py        # Entry point + sidebar navigation
│   ├── api_client.py # HTTP client (API_BASE from env)
│   └── pages/        # 5 pages: auth, tables, sessions, new hand, dashboard
├── Dockerfile.api
├── Dockerfile.ui
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

---

> ⚠️ Poker Coach uses Monte Carlo simulation and simplified ranges — not a GTO/Nash solver. Use as a learning tool.
