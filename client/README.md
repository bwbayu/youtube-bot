# Client

## Overview
The client is a React Vite-powered single-page application that surfaces moderation insights from the Bot Judol platform. It handles authentication, displays channel and video analytics, and exposes comment-level moderation workflows.

## Features
- Google OAuth login via `@react-oauth/google` with secure session cookies provided by the FastAPI backend.
- Dashboard that fetches the latest playlist uploads and historical video catalog, including pagination controls.
- Video detail workspace with comment filtering, IndoBERT prediction triggers, and bulk delete actions.

## Key Pages
- `HomePage.tsx` is entrypoint when user first open the web
- `DashboardPage.tsx` fetches playlist metadata, latest uploads, and the paginated video history for the signed-in channel.
- `VideoDetailPage.tsx` shows video metadata, comment streams, prediction results, and moderation tools.
- `LoadingPage.tsx` blocks the app until access tokens refresh and route guards settle.
- `NotFoundPage.tsx` provides a fallback route for unknown URLs.

## Repository Layout
- `src/api/` React hooks and helpers for calling FastAPI endpoints (videos, comments, moderation actions).
- `src/components/` shared UI primitives such as navigation, comment cards, and bulk action toolbars.
- `src/context/` React context for authenticated user state and playlist metadata.
- `src/lib/` utility helpers for formatting and display logic.
- `src/pages/` route-level components registered in `App.tsx`.

## Environment Variables
- `VITE_GOOGLE_CLIENT_ID` OAuth 2.0 client ID (web application) from Google Cloud.
- `VITE_GOOGLE_CLIENT_SECRET` Matching client secret used during the handshake with the backend.

Copy `client/.env.example` to `client/.env` and fill in both values before starting the dev server.

## Local Development
1. Install dependencies: `npm install` (or `pnpm install`).
2. Start the Vite dev server: `npm run dev`.
3. Visit http://localhost:5173 and sign in with a Google account that has access to the configured YouTube channel.
4. Keep the FastAPI backend running on http://localhost:8000 so API calls succeed.
