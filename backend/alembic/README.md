
# Database Setup and Migrations

## 1. First Time Setup

After cloning the project:

1. Create a `.env` file in the project root (see `.example.env` for required variables).
2. Install dependencies and activate your virtual environment.
3. Run the following commands from the project root:

```bash
# Apply the latest database migrations
alembic upgrade head

# Seed the database with initial data (run as a module!)
python -m backend.database.seed
```

## 2. Making Changes to the Database

Whenever you change models:

1. **Generate a new migration:**
  ```bash
  alembic revision --autogenerate -m "description of your change"
  ```
2. **Apply the migration:**
  ```bash
  alembic upgrade head
  ```

## 3. Troubleshooting

- Always run seed and migration scripts as modules (with `python -m ...`) to avoid import errors.
- If Alembic does not detect your models, ensure they are imported in `alembic/env.py` (e.g., `from backend.database.migrations import user, organization`).
- If you get `ModuleNotFoundError: No module named 'backend'`, use `python -m backend.database.seed` instead of running the script directly.
- If you see migration errors about missing revisions, you may need to reset the `alembic_version` table in your database (for dev only).

---
For more, see the main project README or ask your team lead.
