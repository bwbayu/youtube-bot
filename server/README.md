# Server (FastAPI)

## Overview
The FastAPI server brokers authentication, orchestrates YouTube data collection, persists channel insights to PostgreSQL, and exposes ML-powered moderation endpoints consumed by the React client.

## Features
- Google OAuth 2.0 login with secure session management and token refresh flow where access token stored in redis and refresh token stored in PostgreSQL.
- YouTube playlist ingestion that syncs latest uploads and persists video metadata.
- Comment retrieval, storage, and moderation utilities backed by PostgreSQL.
- IndoBERT inference endpoint that scores comments and writes predictions in bulk.
- Comment deletion endpoint that relays moderation actions back to YouTube via authorized API calls.

## API Endpoints
- **GET /health** health probe.
- **GET /auth/login** redirect to Google OAuth consent.
- **GET /auth/callback** exchange authorization code, persist user, seed playlist info.
- **POST /auth/logout** clear session cookies and refresh tokens.
- **POST /auth/refresh** rotate access tokens using the stored refresh token.
- **GET /content/users** fetch the authenticated channel owner profile and playlist ID.
- **GET /content/fetch-latest-videos** pull newest playlist items and enqueue comment syncs.
- **GET /content/user_videos** paginate stored video history.
- **GET /content/video/{video_id}** return video metadata plus paginated comments.
- **POST /content/comments/delete** remove selected comments (and mark them moderated in the DB).
- **POST /content/predict** run IndoBERT classification against stored comments and write predictions.

## Repository Layout
- `app.py` FastAPI entrypoint, CORS, lifespan handlers, and router registration.
- `src/router/` route definitions split by domain (`auth.py`, `content.py`).
- `src/handlers/` request orchestration layer bridging services and HTTP responses.
- `src/services/` core business logic, YouTube API calls, and ML inference utilities.
- `src/database/` SQLAlchemy models, async session factory, and CRUD helpers.
- `src/middleware/` `RequireLoginMiddleware` guard that enforces authenticated access.
- `src/schemas/` Pydantic models for request and response validation.
- `src/utils/` preprocessing helpers shared by services.
- `models/` shipped PyTorch checkpoints loaded at startup.
- `keys/` OAuth client JSON files (kept out of version control in production).

## Environment Variables
- `GOOGLE_CLIENT_ID` OAuth client ID matching the Google Cloud credentials.
- `GOOGLE_CLIENT_SECRET` OAuth client secret.
- `GOOGLE_API_KEY` YouTube Data API key for playlist and comment requests.
- `REDIS_URL` connection string for caching (default `redis://localhost:6379/0`).
- `POSTGRESQL_URL` async SQLAlchemy DSN (default `postgresql+asyncpg://root:12345678@localhost:5433/botjudol`).
- `FERNET_KEY` base64 key used to encrypt stored refresh tokens.

Create the file `server/.env` from `server/.env.example` and populate each value before launching the API.

## Setup
1. Create a Python 3.10+ virtual environment and activate it.
2. Install dependencies: `pip install -r requirements.txt`.
3. Ensure PostgreSQL and Redis are reachable at the URLs defined in `.env` (or run `docker compose up postgres redis`).
4. Confirm `models/best_indobert.pt` exists; download or train one via the engine project if missing.

## Running Locally
- Start the API with `uvicorn app:app --reload --host 0.0.0.0 --port 8000`, this will automatically create database schema in PostgreSQL. If you want to add column to existing table, you need to delete the table from PostgreSQL first.

## Notes
- The server expects to run behind HTTPS in production; configure CORS and cookie settings accordingly.
- IndoBERT checkpoints are loaded into memory on startup; GPU availability is auto-detected but optional.
- API quota errors from Google are surfaced as HTTP 429/403 responses; monitor logs for details.
