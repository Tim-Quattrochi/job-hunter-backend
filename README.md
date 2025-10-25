# Job Hunter Backend

FastAPI-powered backend for the Job Hunter platform. The service exposes REST APIs, powers asynchronous task processing via Celery, and is containerized with Docker for consistent local development.

## Project Structure

```
job-hunter-backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── workers/
│   ├── __init__.py
│   ├── celery_app.py
│   └── main.py
├── tests/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11+
- Docker Desktop (or Docker Engine) with Docker Compose
- Make (optional, not required)

## Getting Started

1. **Clone the repository** (or add as submodule inside the mono-repo).
2. **Create a virtual environment (optional when using Docker):**

   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies (local Python workflow):**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Update values as required by the target environment (Neon DB, Stack Auth).
   - When running without Docker, set `REDIS_URL=redis://localhost:6379/0` so Celery connects to your local Redis instance.

## Running the Application

### Option A: Docker Compose (recommended)

```bash
docker-compose up --build
```

- FastAPI service: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Health check: `curl http://localhost:8000/api/health`
- Celery worker logs appear in the `worker` container output.

### Option B: Local Python (without Docker)

```bash
uvicorn app.main:app --reload
```

Start the Celery worker separately:

```bash
celery -A app.celery_app worker --loglevel=info
```

Ensure Redis is available locally (default `redis://localhost:6379/0`).

## Verifying the Setup

1. Start services with Docker Compose.
2. Confirm the API response:

   ```bash
   curl http://localhost:8000/api/health
   ```

   Expected response: `{"status": "healthy"}`

3. Confirm the root endpoint returns metadata:

   ```bash
   curl http://localhost:8000/
   ```

4. Watch the Celery worker logs for the startup banner showing `ready`.

5. (Optional) Trigger the sample task using an interactive shell:

   ```python
   from app.celery_app import test_task
   test_task.delay("Hello from Celery!")
   ```

## Documentation Links

- [Product Requirements](../docs/prd.md)
- [Architecture Overview](../docs/architecture.md)

## Next Steps

- Configure managed services (Neon DB, Stack Auth, Upstash Redis) in Story 0.3.
- Implement authentication flows starting with Story 1.1.
- Add automated tests and CI workflows.
