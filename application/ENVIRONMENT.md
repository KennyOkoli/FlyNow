# Fly Now: environment, ports and endpoints

Everything the two containers need, in one place. No real values live in the repo: secrets go in
`server/.env` locally (gitignored) and in Secrets Manager / the task definition on AWS.

## How a request flows

```
Browser ──> frontend container (nginx :80)
              ├─ /            static Vue build (index.html, /assets/*)
              └─ /api/*  ───> backend container (FastAPI :8000) ───> Sabre API (HTTPS)
                                                  └────────────────> MySQL (RDS :3306)
```

The Vue app never calls the backend by hostname. It calls `/api/...` on the same origin it was
loaded from, and nginx forwards those requests to the backend. So:

- the **frontend build has no env variables** (nothing is baked into the JS),
- the frontend **container** needs one variable, `ENDPOINT`, telling nginx where the backend is,
- no CORS setup is needed in production, because the browser only ever talks to one origin.

## Ports

| Container | Listens on | Health check |
|---|---|---|
| frontend (nginx) | **80** | `GET /` → 200 |
| backend (uvicorn) | **8000** | `GET /api/health` → `{"status":"ok","provider":"sabre" or "mock"}` |
| MySQL (RDS) | **3306** | — |

## Frontend container

| Variable | Required | Example | What it does |
|---|---|---|---|
| `ENDPOINT` | yes | `http://backend:8000` | Where nginx forwards `/api/*`. Scheme + host + port, **no trailing slash, no path**. Must be reachable from the frontend task (Cloud Map / service discovery name). Default in the image: `http://backend:8000`. |

nginx config: `web/nginx/default.conf.template`. The official nginx image substitutes `${ENDPOINT}`
at container start. The proxy read timeout is 90s because a live Sabre search can take up to a minute;
if there is a load balancer in front, give it an idle timeout of at least 90s too.

## Backend container

### Sabre

| Variable | Required | Secret | Example | Notes |
|---|---|---|---|---|
| `SABRE_USER_ID` | yes* | no | `V1:abc123:DEVCENTER:EXT` | From Sabre's test credentials page. If it already starts with `V1:` it is used as the client ID as-is. |
| `SABRE_PASSWORD` | yes* | **yes** | | The password shown next to the user ID. |
| `SABRE_PCC` | yes* | no | `ABCD` | Pseudo City Code. |
| `SABRE_CLIENT_ID` | no | **yes** | | Only if Sabre gives a ready-made client ID. Overrides the three above. |
| `SABRE_CLIENT_SECRET` | no | **yes** | | Pair of `SABRE_CLIENT_ID`. |
| `SABRE_BASE_URL` | no | no | `https://api.cert.platform.sabre.com` | **Host only.** The app appends `/v2/auth/token` and `/v5/offers/shop`. Production Sabre is `https://api.platform.sabre.com`. |
| `USE_MOCK` | no | no | `false` | `true` = sample flights, no Sabre calls. If unset: mock when credentials are missing, Sabre otherwise. |

\* Either `SABRE_USER_ID` + `SABRE_PASSWORD` (+ `SABRE_PCC`), or `SABRE_CLIENT_ID` + `SABRE_CLIENT_SECRET`.

### Database

The backend saves every search to one table, `searches` (created automatically on start-up).
It accepts the connection in either of two forms:

**A. The parts** (what `infrastructure/modules/ecs/taskDefinition.tf` already passes):

| Variable | Example | Notes |
|---|---|---|
| `DB_HOST` | `flynow-dev.xxxx.eu-west-2.rds.amazonaws.com` | The RDS endpoint address: `aws_db_instance.flynow_db.address`. |
| `DB_PORT` | `3306` | Default 3306. |
| `DB_NAME` | `flynow_db_dev` | `aws_db_instance.flynow_db.db_name` (Terraform makes `flynow_db_${env}`). |
| `DB_USERNAME` | | From the `flynow-secrets<env>` secret. |
| `DB_PASSWORD` | | **Secret.** From the same secret. Special characters are fine; the app escapes them. |
| `DB_DRIVER` | `mysql+aiomysql` | Default. Only change it for a different database engine. |

**B. One URL** (wins over the parts if set):

| Variable | Example |
|---|---|
| `DATABASE_URL` | `mysql+aiomysql://user:password@host:3306/flynow_db_dev` |

With neither, the backend uses a local SQLite file (`./flynow.db`), which is fine for development
but is lost when a container restarts.

### Optional

| Variable | Default | Notes |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated. Only matters if the frontend is served from a different origin than `/api` (not the case behind the nginx proxy). |
| `SEARCH_TTL_MINUTES` | `30` | How long search results stay cached in memory for the detail page. With more than one backend task, a detail request can land on a task that never saw the search; run one task or use sticky sessions until the cache moves to a shared store. |

## API endpoints (backend)

All under `/api`. Full request/response shapes are in [API.md](./API.md).

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness + which provider is active. Use for target-group / ECS health checks. |
| GET | `/api/airports?q=lag` | Airport autocomplete. |
| POST | `/api/flights/search` | Search flights (calls Sabre). Saves a row in `searches`. |
| GET | `/api/flights/{searchId}/itineraries/{itineraryId}` | One itinerary from a cached search. |

## Running it locally

```
cd application
cp server/.env.example server/.env    # fill in the Sabre values, or leave USE_MOCK=true
docker compose up --build
```

- App: http://localhost:3000
- API directly: http://localhost:8000/api/health
- MySQL: `localhost:3306`, database `flynow_db_local`, user `flynow` (local throwaway values in `docker-compose.yaml`)

Compose runs the same three pieces as AWS (nginx → FastAPI → MySQL 8.4) with the same variable names.

## Checklist for the AWS side

These live in Terraform, so they are left for the infrastructure owner:

- [ ] Backend task definition: `DB_HOST` should be the RDS address (`aws_db_instance.flynow_db.address`), not `"mysql"`.
- [ ] One backend port everywhere: the container listens on **8000**. The backend security group (`backend_service.tf`) and the frontend's `ENDPOINT` currently say **8080**.
- [ ] Frontend `ENDPOINT` = the backend's service discovery name + `:8000`, e.g. `http://backend.<namespace>:8000`.
- [ ] Pass `SABRE_PASSWORD`, `SABRE_CLIENT_SECRET` and `DB_PASSWORD` with the task definition's `secrets` (`valueFrom` a Secrets Manager ARN) instead of `environment`, so they don't show in plain text in the console or Terraform state.
- [ ] RDS security group: allow 3306 from the backend's security group only, not `0.0.0.0/0`.
- [ ] Images: replace `nginx:latest` in both task definitions with the built frontend/backend images.
