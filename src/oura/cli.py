import json

import click
import httpx

from .auth import authorize, set_token
from .client import OuraClient


def _print_json(data):
  click.echo(json.dumps(data, indent=2))


def _handle_errors(fn):
  """Decorator to catch common errors and display clean messages."""
  import functools

  @functools.wraps(fn)
  def wrapper(*args, **kwargs):
    try:
      return fn(*args, **kwargs)
    except RuntimeError as e:
      raise click.ClickException(str(e))
    except httpx.HTTPStatusError as e:
      msg = f"{e.response.status_code}"
      try:
        body = e.response.json()
        detail = body.get("detail", body.get("message", ""))
        if detail:
          msg += f": {detail}"
      except Exception:
        msg += f": {e.response.text}"
      raise click.ClickException(msg)

  return wrapper


@click.group()
def cli():
  """Oura Ring API command-line interface."""


@cli.command()
@click.option("--token", "-t", help="Set a Personal Access Token directly")
@_handle_errors
def auth(token):
  """Authenticate with the Oura API.

  Without --token: runs the OAuth2 browser flow.
  With --token: saves the given Personal Access Token.
  """
  if token:
    set_token(token)
    click.echo("Token saved.")
  else:
    authorize()


@cli.command("personal-info")
@_handle_errors
def personal_info():
  """Get personal info (age, weight, height, email)."""
  client = OuraClient()
  _print_json(client.get_personal_info())


@cli.command()
@click.option("--start", "-s", help="Start datetime (ISO 8601, e.g. 2024-01-01T00:00:00-08:00)")
@click.option("--end", "-e", help="End datetime (ISO 8601)")
@click.option("--next-token", help="Pagination token")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
@_handle_errors
def heartrate(start, end, next_token, fetch_all):
  """Get heart rate time-series data."""
  client = OuraClient()
  if fetch_all:
    _print_json(client.get_all_heartrate(start_datetime=start, end_datetime=end))
  else:
    _print_json(client.get_heartrate(start_datetime=start, end_datetime=end, next_token=next_token))


# --- Data commands (all follow the same pattern) ---

DATA_TYPES = [
  ("sleep", "sleep", "Get sleep period data"),
  ("daily-sleep", "daily_sleep", "Get daily sleep summary"),
  ("activity", "daily_activity", "Get daily activity data"),
  ("readiness", "daily_readiness", "Get daily readiness scores"),
  ("stress", "daily_stress", "Get daily stress data"),
  ("resilience", "daily_resilience", "Get daily resilience data"),
  ("spo2", "daily_spo2", "Get daily SpO2 data"),
  ("cardiovascular-age", "daily_cardiovascular_age", "Get daily cardiovascular age"),
  ("vo2-max", "vO2_max", "Get VO2 max data"),
  ("workout", "workout", "Get workout data"),
  ("session", "session", "Get session data"),
  ("tag", "tag", "Get tag data"),
  ("enhanced-tag", "enhanced_tag", "Get enhanced tag data"),
  ("sleep-time", "sleep_time", "Get sleep time recommendations"),
  ("rest-mode", "rest_mode_period", "Get rest mode periods"),
  ("ring", "ring_configuration", "Get ring configuration"),
]


def _make_data_command(cmd_name: str, api_path: str, help_text: str):
  @click.command(name=cmd_name, help=help_text)
  @click.option("--start", "-s", help="Start date (YYYY-MM-DD)")
  @click.option("--end", "-e", help="End date (YYYY-MM-DD)")
  @click.option("--id", "doc_id", help="Fetch a single document by ID")
  @click.option("--next-token", help="Pagination token")
  @click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages")
  @_handle_errors
  def cmd(start, end, doc_id, next_token, fetch_all):
    client = OuraClient()
    if doc_id:
      _print_json(client.get_document(api_path, doc_id))
    elif fetch_all:
      _print_json(client.get_all_data(api_path, start_date=start, end_date=end))
    else:
      _print_json(client.get_data(api_path, start_date=start, end_date=end, next_token=next_token))

  cli.add_command(cmd)


for _name, _path, _help in DATA_TYPES:
  _make_data_command(_name, _path, _help)


# --- Webhook commands ---


@cli.group()
def webhook():
  """Manage webhook subscriptions (uses client credentials)."""


@webhook.command("list")
@_handle_errors
def webhook_list():
  """List all webhook subscriptions."""
  client = OuraClient()
  _print_json(client.list_webhooks())


@webhook.command("create")
@click.option("--url", required=True, help="Callback URL")
@click.option("--token", required=True, help="Verification token")
@click.option(
  "--event",
  required=True,
  type=click.Choice(["create", "update", "delete"]),
  help="Event type",
)
@click.option(
  "--data-type",
  required=True,
  type=click.Choice(
    [
      "tag",
      "enhanced_tag",
      "workout",
      "session",
      "sleep",
      "daily_sleep",
      "daily_readiness",
      "daily_activity",
      "daily_spo2",
      "sleep_time",
      "rest_mode_period",
      "ring_configuration",
      "daily_stress",
      "daily_cardiovascular_age",
      "daily_resilience",
      "vo2_max",
    ]
  ),
  help="Data type to subscribe to",
)
@_handle_errors
def webhook_create(url, token, event, data_type):
  """Create a webhook subscription."""
  client = OuraClient()
  _print_json(client.create_webhook(url, token, event, data_type))


@webhook.command("get")
@click.argument("id")
@_handle_errors
def webhook_get(id):
  """Get a webhook subscription by ID."""
  client = OuraClient()
  _print_json(client.get_webhook(id))


@webhook.command("delete")
@click.argument("id")
@_handle_errors
def webhook_delete(id):
  """Delete a webhook subscription."""
  client = OuraClient()
  client.delete_webhook(id)
  click.echo("Webhook deleted.")


@webhook.command("renew")
@click.argument("id")
@_handle_errors
def webhook_renew(id):
  """Renew a webhook subscription."""
  client = OuraClient()
  _print_json(client.renew_webhook(id))
