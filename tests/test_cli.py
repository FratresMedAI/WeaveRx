"""CLI smoke tests."""

from typer.testing import CliRunner

from weaverx.cli import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "WeaveRx" in result.stdout
    assert "triage" in result.stdout


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "weaverx" in result.stdout


def test_triage_mock_json() -> None:
    result = runner.invoke(
        app,
        ["triage", "--repo", "Project-MONAI/MONAI", "--issue", "42", "--mock", "--json"],
    )
    assert result.exit_code == 0
    assert "reproducibility-environment" in result.stdout
    assert "draft_response" in result.stdout
    assert "safeguard" in result.stdout
    assert "ready_for_review" in result.stdout
    assert "sources" in result.stdout


def test_triage_requires_issue_or_recent() -> None:
    result = runner.invoke(app, ["triage", "--repo", "Project-MONAI/MONAI"])
    assert result.exit_code == 1
