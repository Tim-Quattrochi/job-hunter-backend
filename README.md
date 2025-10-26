# Job Hunter Backend

FastAPI-powered backend for the Job Hunter platform. The service exposes REST APIs, powers asynchronous task processing via Celery, and is containerized with Docker for consistent local development.

## Project Structure

```plaintext
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
   - See [External Services Setup](#external-services-setup) section below for detailed configuration instructions.

## Running the Application

### Option A: Docker Compose (recommended)

```bash
docker-compose up --build
```

- FastAPI service: <http://localhost:8000>
- Interactive docs: <http://localhost:8000/docs>
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

## External Services Setup

This backend requires configuration of external managed services. Follow these steps to set up each service.

### Neon DB (PostgreSQL Database)

1. Sign up for a Neon DB account at [https://neon.tech](https://neon.tech)
2. Create a new project named "job-hunter"
3. Create a database named "job_hunter_db"
4. Copy the connection string from the Neon dashboard
5. Add to `.env`:

   ```bash
   DATABASE_URL=postgresql://user:password@host/db_name?sslmode=require
   ```

**Testing the connection:**

```bash
curl http://localhost:8000/api/db-health
```

Expected response: `{"status":"connected","database":"neondb"}`

### Stack Auth (Authentication Service)

1. Sign up for a Stack Auth account at [https://stack-auth.com](https://stack-auth.com)
2. Create a new project named "Job Hunter"
3. Navigate to the **API Keys** section in the Stack Auth dashboard
4. Copy the following credentials:
   - **Project ID** → `NEXT_PUBLIC_STACK_PROJECT_ID`
   - **Secret Server Key** → `STACK_SECRET_SERVER_KEY`
5. Add to `.env`:

   ```bash
   NEXT_PUBLIC_STACK_PROJECT_ID=your_project_id_here
   STACK_SECRET_SERVER_KEY=your_secret_key_here
   ```

**Security Note:** Never commit your `.env` file. The `STACK_SECRET_SERVER_KEY` is private and should be kept confidential.

**Dashboard Configuration:**

- Enable Email/Password authentication
- Configure OAuth providers (Google, LinkedIn) if desired
- Set authorized redirect URLs:
  - Development: `http://localhost:3000/auth/callback`
  - Production: (to be updated when deployed)
- Configure CORS origins:
  - Development: `http://localhost:3000`
  - Production: (to be updated when deployed)

**Testing the integration:**

Full Stack Auth integration will be implemented in Story 1.1. For now, verify that credentials are correctly configured.

### Upstash Redis (Task Queue Broker)

**Note:** For local development, we use the Redis container from Docker Compose. Upstash Redis will be configured for production deployment in a future story.

For local development, the `.env` should have:

```bash
REDIS_URL=redis://redis:6379/0
```

## Documentation Links

- [Product Requirements](../docs/prd.md)
- [Architecture Overview](../docs/architecture.md)
- [Story 0.3: Service Configuration](../docs/stories/0.3.service-configuration.md)

## Troubleshooting

### Database Connection Issues

- **Error: "connection refused"** → Ensure SSL is enabled with `?sslmode=require` in the connection string
- **Error: "authentication failed"** → Verify the connection string is copied correctly from Neon dashboard
- **Error: "database does not exist"** → Create the database in the Neon dashboard

### Stack Auth Issues

- **Error: "invalid project ID"** → Verify `NEXT_PUBLIC_STACK_PROJECT_ID` is copied correctly
- **Error: "unauthorized"** → Check that `STACK_SECRET_SERVER_KEY` is correct
- **Error: "redirect URI mismatch"** → Add your app URL to allowed redirects in Stack Auth dashboard

### Redis Connection Issues

- **Error: "connection timeout"** → Ensure Redis container is running with `docker-compose ps`
- **Error: "authentication failed"** → Verify `REDIS_URL` matches the Docker Compose configuration

## Next Steps

- Implement authentication flows starting with Story 1.1.
- Add automated tests and CI workflows.
