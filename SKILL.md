# Oura CLI

Command-line interface for the Oura Ring API. Installed as `oura` via `uv run oura`.

## Authentication

OAuth2 credentials (`CLIENT_ID`, `CLIENT_SECRET`) are in `.env`. Access tokens are stored in `~/.config/oura/credentials.json` after auth. Tokens auto-refresh on 401.

```bash
# First-time setup: opens browser for OAuth2 authorization
uv run oura auth

# Or set a token directly
uv run oura auth --token <TOKEN>
```

If `OURA_ACCESS_TOKEN` is set in `.env` or environment, it is used automatically (no auth command needed).

## Commands

### Personal Info

```bash
uv run oura personal-info
```

Returns: id, age, weight, height, biological_sex, email.

### Data Commands

All data commands share the same options:

| Flag | Description |
|---|---|
| `-s, --start DATE` | Start date (`YYYY-MM-DD`) |
| `-e, --end DATE` | End date (`YYYY-MM-DD`) |
| `--id ID` | Fetch a single document by ID |
| `--all` | Auto-paginate through all pages |
| `--next-token TOKEN` | Manual pagination token |

Available commands:

| Command | API Resource | Description |
|---|---|---|
| `sleep` | sleep | Sleep period data (phases, efficiency, HR) |
| `daily-sleep` | daily_sleep | Daily sleep summary with score |
| `activity` | daily_activity | Daily activity (steps, calories, MET) |
| `readiness` | daily_readiness | Readiness score and contributors |
| `stress` | daily_stress | Daily stress data |
| `resilience` | daily_resilience | Daily resilience data |
| `spo2` | daily_spo2 | Blood oxygen (SpO2) during sleep |
| `cardiovascular-age` | daily_cardiovascular_age | Cardiovascular age |
| `vo2-max` | vO2_max | VO2 max data |
| `workout` | workout | Workout data (type, calories, intensity) |
| `session` | session | Guided/unguided session data |
| `tag` | tag | User-entered tags |
| `enhanced-tag` | enhanced_tag | Enhanced tag data |
| `sleep-time` | sleep_time | Sleep time recommendations |
| `rest-mode` | rest_mode_period | Rest mode periods |
| `ring` | ring_configuration | Ring config (color, size, serial) |

Examples:

```bash
# Last week of sleep data
uv run oura sleep -s 2026-02-06 -e 2026-02-13

# All activity data for January (auto-paginate)
uv run oura activity -s 2026-01-01 -e 2026-01-31 --all

# Single document by ID
uv run oura sleep --id abc123

# Readiness scores, no date filter (API default range)
uv run oura readiness
```

### Heart Rate

Uses datetime (not date) parameters:

```bash
uv run oura heartrate -s 2026-02-12T00:00:00 -e 2026-02-13T00:00:00
uv run oura heartrate -s 2026-02-12T00:00:00 -e 2026-02-13T00:00:00 --all
```

### Webhooks

Uses client credentials (`CLIENT_ID`/`CLIENT_SECRET` from `.env`) — no bearer token needed.

```bash
# List all subscriptions
uv run oura webhook list

# Create a subscription
uv run oura webhook create --url https://example.com/hook --token mytoken --event create --data-type sleep

# Get/delete/renew by ID
uv run oura webhook get <ID>
uv run oura webhook delete <ID>
uv run oura webhook renew <ID>
```

Valid `--event` values: `create`, `update`, `delete`

Valid `--data-type` values: `tag`, `enhanced_tag`, `workout`, `session`, `sleep`, `daily_sleep`, `daily_readiness`, `daily_activity`, `daily_spo2`, `sleep_time`, `rest_mode_period`, `ring_configuration`, `daily_stress`, `daily_cardiovascular_age`, `daily_resilience`, `vo2_max`

## Output

All commands output JSON to stdout. Pipe to `jq` for filtering:

```bash
# Get just sleep scores
uv run oura daily-sleep -s 2026-02-01 -e 2026-02-13 | jq '.data[].score'

# Get today's step count
uv run oura activity -s 2026-02-13 | jq '.data[0].steps'
```

## Response Format

Multi-document endpoints return:
```json
{
  "data": [...],
  "next_token": "string or null"
}
```

Single document endpoints (with `--id`) return the object directly.

## Errors

Errors are printed to stderr with the HTTP status code and detail message. Common codes:
- **401**: Token expired or invalid (auto-refresh is attempted)
- **403**: Scope not authorized
- **429**: Rate limit exceeded (5000 requests per 5 minutes)
