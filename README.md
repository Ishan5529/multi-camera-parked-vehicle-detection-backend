# multi-camera-parked-vehicle-detection-backend
FAST API Server for multi-camera-parked-vehicle-detection project.

## Local Run

1. Install dependencies:
	`pip install -r requirements.txt`
2. Run the API:
	`uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

## Render PostgreSQL Setup

1. In Render, create a PostgreSQL service.
2. Open the database service and copy the **Internal Database URL**.
3. In your Render Web Service (this backend), add environment variable:
	`DATABASE_URL=<your-internal-database-url>`
4. Redeploy the web service.

The app auto-creates required tables on startup.

## Render Web Service Settings

1. Build command:
	`pip install -r requirements.txt`
2. Start command:
	`uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Health check path:
	`/health`

## Notes

1. If `DATABASE_URL` is not set, the app falls back to local SQLite (`app.db`) for development.
2. Endpoint `/update_config` now saves and updates configuration rows in the database.
