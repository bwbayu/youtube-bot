# Bot Judol
## Demo
[Watch Demo Video](https://www.youtube.com/watch?v=y13QeAKSAXA)

## Overview
Bot Judol is a full-stack toolkit for moderating YouTube comments, specifically targeting online gambling promotion. It works similarly to YouTube Studio but is enhanced with AI-powered classification, allowing creators to delete spammy comments in just two clicks, run the AI and delete the flagged content.

## Features
- Full OAuth-based sign-in with Google for authenticated access to YouTube data.
- Comment ingestion pipeline that fetches videos and comments, persists them, and tracks moderation status.
- Predicts online gambling promotion using an IndoBERT-powered classification engine with batch moderation directly from the dashboard.

## Tech Stack
- Client: React 19, TypeScript, Vite, Tailwind CSS.
- Server: FastAPI, SQLAlchemy Async, Redis, PostgreSQL, Transformers, Hugging Face models.
- Engine: Python tooling for scraping, EDA, model training, and benchmarking with Transformers, PyTorch, MLflow.

## Repository Layout
- client/ - React SPA and reusable components.
- engine/ - Data collection, experimentation, model training, and benchmarking scripts.
- server/ - FastAPI service, async database layer, and ML inference helpers.
- docker-compose.yml - Orchestrates Postgres, Redis, FastAPI, and React containers.

## Prerequisites
- Docker and Docker Compose.
- Python 3.10+ and Node 18+ (only required for running services outside Docker).
- Access to a Google Cloud project with YouTube Data API v3 enabled.

## Environment Setup
1. Copy each example file to a working `.env`:
   - `cp client/.env.example client/.env`
   - `cp engine/.env.example engine/.env`
   - `cp server/.env.example server/.env`
2. Fill in the placeholders with the credentials described below. The same Google OAuth client ID, client secret, and API key are shared across services.
3. Generate a `FERNET_KEY` for the server (see section below).

## Running with Docker Compose
1. Ensure `docker-compose.yml` is updated with desired port bindings.
2. Start the stack:
   - `docker compose up --build`
3. The services expose:
   - React client at http://localhost:5173
   - FastAPI backend at http://localhost:8000
   - PostgreSQL at localhost:5433
   - Redis at localhost:6379
4. Use `docker compose down` to stop the stack and `docker compose down -v` to drop volumes.

## Credential Setup

### Google OAuth Client (Client + Server)
1. Visit https://console.cloud.google.com/apis/credentials and create an OAuth 2.0 Client ID (type: Web application).
2. Add authorized JavaScript origin `http://localhost:5173` and redirect URI `http://localhost:5173`.
3. Download the credentials. Use the `client_id` for `VITE_GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_ID`, and the `client_secret` values for `VITE_GOOGLE_CLIENT_SECRET` and `GOOGLE_CLIENT_SECRET`.
4. Store them in the corresponding `.env` files.

### Google API Key (Server + Engine)
1. In the same project, create an API key with access to YouTube Data API v3.
2. Restrict the key to the YouTube Data API if desired.
3. Use the key for `GOOGLE_API_KEY` (server `.env`) and `API_KEY` (engine `.env`).

### Authorized Redirect URI for Backend
- If you deploy the backend, add the public URL to the OAuth client as an authorized redirect URI. The FastAPI callback endpoint expects `<backend-url>/auth/callback`.

## Generate a Fernet key
Go to python REPL/CLI where fernet already installed. Run the following command and copy the printed value into `server/.env` as `FERNET_KEY`: 
```
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```
