# Useful Commands

## Docker

```bash
# Start PostgreSQL (pgvector)
docker compose up -d

# Stop PostgreSQL
docker compose down

# Stop and remove volumes (reset DB)
docker compose down -v

# View database logs
docker compose logs db
```

## Poetry

```bash
# Install dependencies
poetry install

# Add a new dependency
poetry add <package>

# Run a command in the virtual environment
poetry run <command>
```

## Alembic (Database Migrations)

```bash
# Apply all migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# Auto-generate a new migration
poetry run alembic revision --autogenerate -m "description"

# Show current migration version
poetry run alembic current

# Show migration history
poetry run alembic history
```

## FastAPI Server

```bash
# Start dev server with auto-reload
poetry run uvicorn app.main:app --reload

# Start on a specific host/port
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Database (psql via Docker)

```bash
# Open psql shell
docker exec -it pa_backend-db-1 psql -U pa_user -d pa_db

# List tables
docker exec pa_backend-db-1 psql -U pa_user -d pa_db -c "\dt"

# Run a query
docker exec pa_backend-db-1 psql -U pa_user -d pa_db -c "SELECT * FROM users"
```

## Quick Start

```bash
docker compose up -d
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```
