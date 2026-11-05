# back_end_core

A FastAPI + PostgreSQL (psycopg 3, async) starter to reuse across web projects. It contains no
business APIs; only the shared infrastructure every project needs:

- Settings from environment / `.env` (`src/core/config/settings.py`)
- Async PostgreSQL pool with per-request connection and commit/rollback (`src/core/database.py`)
- Logging to console and rotating files (`src/core/logging.py`)
- One JSON error format and exception classes (`src/core/exceptions.py`)
- Password hashing and JWT helpers (`src/core/security.py`)
- Middleware: request id, access logging, CORS, security headers, per-IP rate limit
- Base repository/service, pagination params, `Page[T]` response
- Health probes: `GET /health` and `GET /health/ready`

## Run

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

copy src\core\config\secrets\.env.example src\core\config\secrets\.env   # then fill in PG_*
python scripts/init_db.py      # create database/schema, apply scripts/sql/*.sql
python -m src.main             # or: uvicorn src.main:app --reload --port 5000
```

On Windows with uvicorn >= 0.36 from the command line, add
`--loop core.asyncio_platform:selector_loop_factory` (psycopg async needs a selector loop).
`python -m src.main` does this for you.

Docs at `http://localhost:5000/docs` (off in production unless `API_DOCS_ENABLED=true`).

## Layout

```
src/
  main.py                 app factory: middleware, error handlers, routers, lifespan
  core/                   framework-level code, no business logic
    config/settings.py    all settings
    database.py           pool, get_db, pool_connection, transaction
    exceptions.py         AppError, NotFoundError, ... + handlers
    logging.py            setup_logging, get_logger, Loggers
    security.py           bcrypt, JWT, random tokens
  middleware/             ASGI / Starlette middleware
  base/                   application layers
    routes/registry.py    the one place routers are registered
    routes/               APIRouter per feature
    controllers/          request -> service -> response; deps.py = shared dependencies
    services/             business rules
    repositories/         SQL
    models/ requests/ responses/
scripts/
  init_db.py, check_db.py, sql/
```

## Adding a feature

Example `items`, following route -> controller -> service -> repository.

1. SQL: `scripts/sql/001_items.sql`

   ```sql
   CREATE TABLE IF NOT EXISTS items (
       id         SERIAL PRIMARY KEY,
       name       VARCHAR(200) NOT NULL,
       created_at TIMESTAMPTZ NOT NULL DEFAULT now()
   );
   ```

2. Repository: `src/base/repositories/item_repository.py`

   ```python
   from base.repositories.base import BaseRepository

   class ItemRepository(BaseRepository):
       async def get(self, item_id: int):
           return await self._fetch_one("SELECT * FROM items WHERE id = %(id)s", {"id": item_id})

       async def page(self, limit: int, offset: int):
           return await self._fetch_page("SELECT * FROM items ORDER BY id", limit=limit, offset=offset)

       async def create(self, name: str):
           return await self._fetch_one("INSERT INTO items (name) VALUES (%(name)s) RETURNING *", {"name": name})
   ```

3. Service: `src/base/services/item_service.py`

   ```python
   from base.repositories.item_repository import ItemRepository
   from base.services.base import BaseService
   from core.exceptions import NotFoundError

   class ItemService(BaseService):
       def __init__(self, db):
           super().__init__(db)
           self.items = ItemRepository(db)

       async def get(self, item_id: int):
           row = await self.items.get(item_id)
           if row is None:
               raise NotFoundError("Item not found")
           return row
   ```

4. Schemas in `requests/item_request.py` and `responses/item_response.py` (Pydantic).

5. Dependency in `src/base/controllers/deps.py`

   ```python
   def get_item_service(db: DbConn) -> ItemService:
       return ItemService(db)

   ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]
   ```

6. Route `src/base/routes/item_route.py`, then add `item_route.router` to `API_ROUTERS` in
   `src/base/routes/registry.py`.

   ```python
   router = APIRouter(prefix="/items", tags=["items"])

   @router.get("/{item_id}", response_model=ItemResponse)
   async def get_item(item_id: int, service: ItemServiceDep):
       return await service.get(item_id)

   @router.get("", response_model=Page[ItemResponse])
   async def list_items(params: PageParamsDep, service: ItemServiceDep):
       rows, total = await service.items.page(params.limit, params.offset)
       return Page.build(rows, total, params)
   ```

   Served at `/api/v1/items`.

## Built-in APIs: config, permissions, menus

Tables: `scripts/sql/001_config.sql`, `002_permissions.sql`, `003_menus.sql` (run `python scripts/init_db.py`).

Admin endpoints need header `X-API-Key: <ADMIN_API_KEY>`. Without `ADMIN_API_KEY` they are open in
development and refused in production. When the project adds login, replace `require_admin` in
`base/controllers/deps.py` with a permission check on the current user.

| Method | Path (under `/api/v1`) | Admin key | |
|---|---|---|---|
| GET | `/config?type=&q=&page=&page_size=` | yes | paged list; secret values shown as `********` |
| GET | `/config/types` | yes | distinct groups |
| GET / POST / PATCH / DELETE | `/config/{key}`, `/config` | yes | CRUD |
| POST | `/config/cache/refresh` | yes | reload the in-process cache |
| GET | `/permissions?module=&is_active=&q=` | yes | paged list |
| GET | `/permissions/grouped?active_only=` | yes | grouped by module (permission matrix) |
| GET | `/permissions/{id}`, `/permissions/code/{code}` | yes | one permission |
| POST / PATCH / DELETE | `/permissions`, `/permissions/{id}` | yes | `code` is fixed after create; module/action default from it |
| GET | `/menus?active_only=`, `/menus/{id}` | no | flat list / one |
| GET | `/menus/tree?active_only=true` | no | nested tree for the sidebar |
| POST / PATCH | `/menus`, `/menus/{id}` | yes | checks parent and permission exist, blocks cycles |
| PUT | `/menus/reorder` | yes | bulk `[{id, sort_order, parent_id}]`, all or nothing |
| DELETE | `/menus/{id}?cascade=` | yes | 409 if it has children, unless `cascade=true` |

Reading config from code (cached for `CONFIG_CACHE_TTL_SECONDS`):

```python
async def handler(config: ConfigServiceDep):
    name = await config.get_value("app_name", "My app")
    limit = await config.get_int("upload_max_mb", 10)
    enabled = await config.get_bool("feature_x_enabled", False)
```

Menus filtered by what a user may see (when auth exists):
`await menu_service.tree(active_only=True, allowed_permissions=user_permission_codes)`.

## Errors

Raise `core.exceptions` classes from any layer. Every error, including validation errors and
`HTTPException`, returns:

```json
{"error": {"code": "not_found", "message": "Item not found", "details": null}}
```

## Notes

- `get_db` keeps one connection for the whole request and commits at the end. For endpoints that
  wait on slow external calls, borrow per step with `pool_connection(request_pool(request))`.
- The rate limiter is in-memory per process. With several workers or servers, move it to Redis.
- Add per-endpoint limits in `RATE_LIMIT_RULES` in `src/main.py`.
