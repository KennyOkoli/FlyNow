# Flights app

Flight search (Wakanow-style landing page, results, itinerary detail) with a FastAPI server that talks to Sabre's Bargain Finder Max API and a Vue 3 client. No booking in this version: Sabre's free developer tier allows search only.

- `server/` — FastAPI, Python 3.12, managed with uv. See `server/README.md`.
- `web/` — Vue 3 + Vite + TypeScript + Tailwind. See `web/README.md`.
- `API.md` — the contract between the two. Change it first.

## Run

```bash
# terminal 1
cd server && cp .env.example .env && uv run uvicorn server.main:app --reload
# terminal 2
cd web && pnpm install && pnpm dev
```

Without Sabre credentials in `server/.env` the server runs in mock mode and returns realistic generated itineraries, so the whole UI works before credentials arrive.
