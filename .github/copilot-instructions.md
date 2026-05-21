<<<<<<< Updated upstream
## Build, test, and lint

All commands use `make` targets. Python deps are managed by `uv`; frontend deps by `npm`.

```bash
uv sync                     # install Python deps (run once after clone)
make install                # npm install for frontend (run once after clone)
make dev                    # backend on :8000, frontend on :5173
make test                   # run all pytest tests
uv run pytest backend/tests/test_brewing.py            # single test file
uv run pytest backend/tests/test_brewing.py::test_name # single test
make lint                   # ruff check (backend) + tsc --noEmit (frontend)
make format                 # ruff format
make type                   # mypy (strict mode)
make seed                   # upsert content JSON into SQLite
make db-reset               # delete SQLite and re-seed
```

## Architecture

**Backend** — FastAPI (Python 3.12, strict mypy).

- `backend/apothecaria/api/` — FastAPI routers (inventory, recipes, customers, brew, ws). Each router uses `Depends()` for DB sessions and app state.
- `backend/apothecaria/domain/` — Pure business logic and Pydantic models. Domain functions like `combine_ingredients()`, `determine_outcome()`, and `pick_next_template()` are side-effect-free and testable in isolation.
- `backend/apothecaria/db/` — SQLAlchemy 2.0 ORM models and session management. Separate from domain Pydantic models.
- `backend/apothecaria/events/` — In-memory async pub/sub (`Broadcaster`) for WebSocket fan-out.
- `backend/apothecaria/content/` — JSON seed files (`ingredients.json`, `recipes.json`, `customers.json`) are the source of truth for game content. Seeding is idempotent (upsert by slug).
- `backend/apothecaria/{agents,mcp}/` — Stub packages for workshop extensions (AI agents, MCP server).

Active customers live **in memory** (`CustomerStore`), not in the database. Brew/serve events are persisted to `brew_history` for analytics.

**Frontend** — Vite + vanilla TypeScript (no framework). Plain DOM with factory functions returning typed component objects (e.g., `createShelf()`, `createCauldron()`). State uses a simple observer pattern in `state/session.ts`. Vite proxies `/api/*` and `/ws/*` to the backend.

## Conventions

### Python docstrings
=======
## Docstrings
>>>>>>> Stashed changes

When writing or updating a Python function or method, give it a docstring in this exact format:

    Short one-line summary of what the function does.
    Use this when <when a caller should reach for this>.
    :param <name>: <description>
    :return: <description>

- Use reST `:param:` / `:return:` fields — not Google-style "Args:"/"Returns:".
- Skip `:return:` for functions that return `None`.
<<<<<<< Updated upstream
- Skip `self` from the parameter list on methods.

### Two model layers

Pydantic models (`domain/models.py`) define data contracts and business logic types. SQLAlchemy models (`db/models.py`) define persistence. Don't mix them — convert between them at the API/DB boundary using `from_attributes`.

### Testing patterns

- Tests live in `backend/tests/`. Fixtures in `conftest.py` provide an in-memory SQLite engine, a DB session, and a `TestClient` with dependency overrides.
- `asyncio_mode = "auto"` — async test functions are detected automatically, no decorator needed.
- Domain logic tests call pure functions directly. API tests use the `client` fixture and assert HTTP status + JSON structure.

### Configration

All settings via env vars with `APOTHECARIA_` prefix (see `config.py`). Pydantic Settings loads from `.env` if present.

### Content changes

To add or modify game content (ingredients, recipes, customers), edit the JSON files in `backend/apothecaria/content/` and run `make seed`. Pydantic seed schemas validate the JSON at load time.
=======
- Skip `self` from the parameter list on methods.
>>>>>>> Stashed changes
