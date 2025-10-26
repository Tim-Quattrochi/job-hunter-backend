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

Test endpoints are available for verifying Stack Auth configuration:

1. **Check Stack Auth configuration status:**

   ```bash
   curl http://localhost:8000/api/auth/health
   ```

   Expected response:

   ```json
   {
     "status": "healthy",
     "service": "stack_auth",
     "message": "Stack Auth is configured"
   }
   ```

2. **Verify a JWT token** (requires a valid Stack Auth token):

   ```bash
   curl -H "Authorization: Bearer <your-jwt-token>" http://localhost:8000/api/auth/verify
   ```

   Expected response (if token is valid):

   ```json
   {
     "status": "valid",
     "message": "Token verified successfully",
     "payload": {
       "sub": "user-id-123",
       "email": "user@example.com",
       ...
     }
   }
   ```

   To obtain a test JWT token:
   - You'll need to implement the frontend login flow (Story 1.1)
   - Alternatively, use the Stack Auth dashboard to generate a test token
   - Or use a tool like jwt.io to inspect tokens (for debugging only)

3. **View all API endpoints:**

   Visit the interactive API documentation at <http://localhost:8000/docs>

**Note:** Full Stack Auth integration (user registration, login flows, protected routes) will be implemented in Story 1.1.

These test endpoints verify that:

- Stack Auth credentials are properly configured
- JWT tokens can be verified using Stack Auth's public keys
- The backend can communicate with Stack Auth's JWKS endpoint

### Upstash Redis (Task Queue Broker)

**Purpose:** Upstash Redis serves as the message broker for Celery task queues in production. For local development, we use the Redis container from Docker Compose.

#### Setup Instructions

1. Sign up for an Upstash account at [https://upstash.com](https://upstash.com)
2. Create a new Redis database:
   - Name: "job-hunter-celery"
   - Region: Choose closest to your backend hosting (or use default)
   - Type: Regional (recommended for production)
3. Copy the connection string from the Upstash dashboard
4. The connection string format will be: `rediss://default:password@host:port`
   - Note: `rediss://` with double 's' indicates SSL/TLS encryption (required by Upstash)

#### Environment Configuration

**For local development** (using Docker Compose Redis):

```bash
REDIS_URL=redis://redis:6379/0
```

**For production** (using Upstash):

```bash
REDIS_URL=rediss://default:your_password@your-host.upstash.io:port
```

**Testing Upstash connection:**

To test the Upstash connection locally before deploying:

1. Temporarily update `.env` with your Upstash connection string
2. Start the Celery worker:

   ```bash
   celery -A app.celery_app worker --loglevel=info
   ```

3. Trigger a test task:

   ```bash
   # In a Python shell or script
   from app.celery_app import test_task
   test_task.delay("Hello Upstash!")
   ```

4. Verify in the Upstash dashboard:
   - Check the "Metrics" tab for task execution
   - Monitor queue depth and throughput
   - View recent commands

5. Switch back to local Redis for development:

   ```bash
   REDIS_URL=redis://redis:6379/0
   ```

**Important Notes:**

- Use local Docker Redis for development (faster, no network latency)
- Use Upstash for production and staging environments
- The Celery worker automatically connects to the Redis URL specified in `.env`
- Upstash provides metrics and monitoring in their dashboard

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

**Local Docker Redis:**

- **Error: "connection timeout"** → Ensure Redis container is running with `docker-compose ps`
- **Error: "authentication failed"** → Verify `REDIS_URL` matches the Docker Compose configuration (`redis://redis:6379/0`)
- **Error: "connection refused"** → Check if Redis container is healthy with `docker-compose logs redis`

**Upstash Redis:**

- **Error: "connection timeout"** → Verify using `rediss://` (with double 's' for SSL) in connection string
- **Error: "authentication failed"** → Check password in connection string from Upstash dashboard
- **Error: "READONLY"** → Using read replica instead of primary (verify connection string)
- **Error: "SSL/TLS error"** → Ensure connection string uses `rediss://` (SSL required by Upstash)

## Next Steps

- Implement authentication flows starting with Story 1.1.
- Add automated tests and CI workflows.
