# gmail-job-tracker

AI-powered Gmail triage system for tracking job search email (interviews, rejections, follow-ups) with a FastAPI backend, Celery workers, and LangChain-powered classification.

## Local setup (dev)

### 1) Start dependencies

Run Postgres + Redis:

```bash
docker compose up -d db redis
```

### 2) Install Python deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure env

```bash
cp .env.example .env
```

Edit `.env` and set at least:
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- (optional) `OPENAI_API_KEY` for AI classification
- (optional) Gmail sync via either:
  - `GMAIL_CLIENT_SECRET_JSON` + `GMAIL_TOKEN_JSON` (JSON strings), or
  - `GMAIL_CLIENT_SECRET_PATH` + `GMAIL_TOKEN_PATH` (paths to JSON files, e.g. `secrets/credentials.json` + `secrets/token.json`)

### 4) Run API + worker

API:

```bash
uvicorn app.main:app --reload
```

Worker (new terminal):

```bash
celery -A app.workers.celery_app.celery_app worker -l INFO
```

Optional scheduler (beat):

```bash
celery -A app.workers.celery_app.celery_app beat -l INFO
```

## Notes

- In development, the API can auto-create tables at startup (`AUTO_CREATE_TABLES=true`).
- If `OPENAI_API_KEY` is not configured, classification falls back to a keyword-based heuristic.
- Keep Google OAuth files like `credentials.json`/`token.json` out of git (use `secrets/` or another ignored folder and point `GMAIL_*_PATH` at them).

## API quickstart

Register:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"me@example.com","password":"change-me-now"}'
```

Login (get JWT):

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/token \
  -H 'content-type: application/x-www-form-urlencoded' \
  -d 'username=me@example.com&password=change-me-now' | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

Trigger Gmail sync (Celery task):

```bash
curl -X POST http://localhost:8000/api/emails/sync -H "authorization: Bearer $TOKEN"
```

List stored emails:

```bash
curl http://localhost:8000/api/emails -H "authorization: Bearer $TOKEN"
```

Classify one stored email:

```bash
curl -X POST http://localhost:8000/api/emails/1/classify -H "authorization: Bearer $TOKEN"
```

Fetch the HTML dashboard with auth header:

```bash
curl http://localhost:8000/api/dashboard/ -H "authorization: Bearer $TOKEN"
```
