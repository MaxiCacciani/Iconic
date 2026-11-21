# Iconic

API REST (FastAPI + SQLModel) sobre PostgreSQL 16. Las reglas de negocio y el stack están referenciados en `CLAUDE.md`.

## Requisitos

- [uv](https://docs.astral.sh/uv/) (instala Python 3.13 solo)
- Docker, para correr con PostgreSQL

## Backend local (SQLite, sin Docker)

```bash
cd backend
uv sync                          # crea .venv e instala dependencias
cp .env.example .env             # completar JWT_SECRET (openssl rand -hex 32)
uv run python -m app.scripts.crear_admin --nombre "Admin" --email admin@iconic.com
uv run fastapi dev app/main.py   # http://localhost:8000/docs
```

Con SQLite las tablas salen de los modelos (`app/modules/models.py`).

## Con Docker (PostgreSQL)

```bash
docker compose up --build        # db + api + frontend
                                 # app:     http://localhost:8080 (Nginx sirve el front y reenvía /api a la API)
                                 # swagger: http://localhost:8000/docs
docker compose exec api python -m app.scripts.crear_admin --nombre "Admin" --email admin@iconic.com
```

El esquema lo crean `backend/sql/schema.sql` y `backend/sql/catalogos.sql` la primera vez que se levanta el volumen.
Si cambia el esquema: `docker compose down -v` y volver a levantar.

## Frontend local

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173 (necesita la API en :8000; /api se reenvía solo)
npm run gen:api                  # regenera los tipos desde http://localhost:8000/openapi.json
npx shadcn@latest add <componente>   # componentes de UI (quedan en src/shared/ui)
```

La UI usa shadcn/ui. Claude Code tiene el MCP `shadcn` en `.mcp.json` y las skills de diseño en `.claude/skills/` (UI UX Pro Max, Frontend Design, UX/UI Skills, Web Design Guidelines y shadcn). Las reglas del front y cuándo usar cada skill están en `frontend/CLAUDE.md`. Para actualizar las skills: `npx skills update -p`.

## Tests y lint

```bash
cd backend
uv run pytest
uv run ruff check . && uv run ruff format .
```

## Estructura

```
backend/
  app/
    core/        config, sesión de base, Unit of Work, JWT, dependencias por rol, excepciones
    common/      RepositorioBase[M] + paginación, Value Objects (USD, IMEI, DNI, Telefono), ENUMs
    modules/     un módulo por dominio: router · schemas · service · repository · models
    scripts/     tareas de consola (crear_admin)
  sql/           schema.sql (DER) y catalogos.sql
  tests/         pytest + httpx, SQLite en memoria
frontend/
  src/
    app/         router, providers, layouts, guards y menú (navegacion.ts)
    features/    una carpeta por módulo del backend
    shared/      ui/ (shadcn), api/, hooks/, lib/
```
