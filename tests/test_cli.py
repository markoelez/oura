from unittest.mock import patch

from click.testing import CliRunner

from oura.cli import cli


def test_help():
  runner = CliRunner()
  result = runner.invoke(cli, ["--help"])
  assert result.exit_code == 0
  assert "Oura Ring API" in result.output


def test_sleep_no_auth():
  runner = CliRunner()
  with patch("oura.client.get_access_token", return_value=None):
    result = runner.invoke(cli, ["sleep"])
  assert result.exit_code == 1
  assert "Not authenticated" in result.output
