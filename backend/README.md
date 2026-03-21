# Chusmeator Backend

FastAPI backend for the Chusmeator interactive map application.

## Features

- **RESTful API** with FastAPI
- **SQLite/PostgreSQL** database support
- **User authentication** via X-User-Id header
- **Ownership validation** for delete/update operations
- **Address search** proxy to LocationIQ API
- **CORS enabled** for frontend integration

## API Endpoints

### General
- `GET /api/user` - Get current user ID
- `GET /api/map-data` - Get all pins and areas
- `GET /api/search?q={query}` - Search for addresses

### Pins
- `POST /api/pins` - Create a new pin
- `DELETE /api/pins/{pinId}` - Delete a pin (owner only)

### Areas
- `POST /api/areas` - Create a new area
- `DELETE /api/areas/{areaId}` - Delete an area (owner only)

## Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the server:**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

   Or directly with uv:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

## Development

- **API Documentation:** Visit `http://localhost:8000/docs` for interactive Swagger UI
- **Health Check:** `http://localhost:8000/health`
- **OpenAPI Spec:** Generated automatically at `http://localhost:8000/openapi.json`

## Database

By default, the backend uses SQLite (`chusmeator.db`). For PostgreSQL:

1. **Start the database container:**
   ```bash
   docker compose up -d
   ```

2. **Update `DATABASE_URL` in `.env`:**
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chusmeator
   ```

3. Install PostgreSQL dependencies (already included in pyproject.toml)

The database schema is automatically created on startup.

## Testing

Run tests with:
```bash
uv run pytest
```

## Authentication

All endpoints (except health check and root) require the `X-User-Id` header:

```bash
curl -H "X-User-Id: user_abc123" http://localhost:8000/api/map-data
```
