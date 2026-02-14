# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

CLI for the Oura Ring API (v2). Built with Click and httpx, managed with uv.

## Commands

```bash
uv sync              # install dependencies
uv run oura --help   # run the CLI
uv run oura auth     # OAuth2 browser flow (redirect URI: http://localhost:8976/callback)
```

No tests or linter currently configured.

## Architecture

Entry point: `oura:main` (defined in `pyproject.toml` `[project.scripts]`).

```
src/oura/
  __init__.py   # main() -> cli()
  cli.py        # Click command definitions
  client.py     # OuraClient - HTTP client for all API endpoints
  auth.py       # OAuth2 flow, token storage, .env loading
```

**cli.py** - Most data commands are generated dynamically via `_make_data_command()` from the `DATA_TYPES` list (maps CLI name -> API path). `heartrate` and `personal-info` are standalone commands because they have different parameter patterns. Webhooks are a `@cli.group()` subgroup. All commands use `_handle_errors` decorator for clean error output.

**client.py** - `OuraClient` wraps all Oura API v2 endpoints. User data endpoints use bearer auth (`_request()` with auto-refresh on 401). Webhook endpoints use client credentials via `x-client-id`/`x-client-secret` headers. `get_all_data()`/`get_all_heartrate()` handle cursor-based pagination automatically.

**auth.py** - Token resolution order: `OURA_ACCESS_TOKEN` env var / `.env` -> `~/.config/oura/credentials.json`. OAuth2 flow starts a local HTTP server on port 8976 to capture the callback. `load_env()` reads `CLIENT_ID`/`CLIENT_SECRET` from env or `.env` file.

## Key Details

- API base URL: `https://api.ouraring.com/v2/usercollection/`
- OAuth2 redirect URI must be registered in the Oura developer portal: `http://localhost:8976/callback`
- Credentials stored at `~/.config/oura/credentials.json` (outside repo)
- `.env` contains `CLIENT_ID` and `CLIENT_SECRET` - covered by `*.env` in `.gitignore`
- API spec is in `openapi-1.28.json` (404KB) - reference for adding new endpoints
- `heartrate` endpoint uses `start_datetime`/`end_datetime` (ISO 8601 with timezone); all other data endpoints use `start_date`/`end_date` (YYYY-MM-DD)
- To add a new data endpoint, append a tuple to `DATA_TYPES` in `cli.py` - no other changes needed
