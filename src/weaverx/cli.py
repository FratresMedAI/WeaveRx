"""WeaveRx CLI — medical AI GitHub triage from the terminal."""

from __future__ import annotations

import json
from typing import Annotated, Any

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from weaverx import __version__
from weaverx.categories import CATEGORY_BY_SLUG, Priority
from weaverx.triage import TriageOptions, TriageResult, build_orchestrator
from weaverx.utils import setup_logging

app = typer.Typer(
    name="weaverx",
    help="WeaveRx — supportive AI triage for medical AI GitHub issues.",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)

PRIORITY_STYLE = {
    Priority.LOW.value: "dim",
    Priority.MEDIUM.value: "cyan",
    Priority.HIGH.value: "yellow",
    Priority.CRITICAL.value: "bold red",
}

SAFEGUARD_STATUS_STYLE = {
    "clean": "green",
    "review_recommended": "yellow",
    "high_risk": "bold red",
}

SAFEGUARD_STATUS_ABBR = {
    "clean": "OK",
    "review_recommended": "REV",
    "high_risk": "RISK",
}


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"weaverx {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = None,
) -> None:
    """WeaveRx entrypoint."""


def _render_duplicate_bar(score: float) -> Text:
    filled = int(score * 10)
    bar = "#" * filled + "-" * (10 - filled)
    style = "green" if score < 0.4 else "yellow" if score < 0.7 else "red"
    return Text(f"[{bar}] {score:.0%}", style=style)


def render_triage_result(result: TriageResult, *, verbose: bool = False) -> None:
    analysis = result.analysis
    cat = CATEGORY_BY_SLUG.get(analysis.category)
    category_name = cat.display_name if cat else analysis.category

    title = f"Issue #{result.issue.number} - {result.issue.title[:60]}"
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Category", category_name)
    table.add_row(
        "Priority",
        Text(analysis.priority.upper(), style=PRIORITY_STYLE.get(analysis.priority, "white")),
    )
    table.add_row("Impact", analysis.impact_summary)
    table.add_row("Duplicate likelihood", _render_duplicate_bar(analysis.duplicate_likelihood))
    table.add_row("Suggested labels", ", ".join(analysis.suggested_labels) or "-")

    if analysis.privacy_flags:
        table.add_row("Privacy flags", ", ".join(analysis.privacy_flags))

    if result.duplicate_matches:
        dupes = "; ".join(
            f"#{m.issue_number} ({m.score:.0%})" for m in result.duplicate_matches[:3]
        )
        table.add_row("Similar issues", dupes)

    if result.safeguard is not None:
        sg = result.safeguard
        table.add_row("Safeguard score", f"{sg.score:.1f} / 10")
        table.add_row(
            "Safeguard status",
            Text(
                sg.status.replace("_", " ").upper(),
                style=SAFEGUARD_STATUS_STYLE.get(sg.status, "white"),
            ),
        )
        if sg.triggered:
            flags = ", ".join(finding.id for finding in sg.triggered)
            table.add_row("Safeguard flags", flags)

    console.print(table)

    draft_border = "green"
    if result.safeguard is not None:
        draft_border = SAFEGUARD_STATUS_STYLE.get(result.safeguard.status, "green")

    draft_preview = result.draft_response if verbose else _truncate(result.draft_response, 400)
    console.print(
        Panel(
            draft_preview,
            title="Draft response",
            subtitle="(use --verbose for full text)",
            border_style=draft_border,
        )
    )

    if result.safeguard is not None and result.safeguard.status == "high_risk":
        console.print(
            "[yellow]Safeguard: high risk — review draft carefully before posting.[/yellow]"
        )

    if result.dry_run:
        console.print("[dim]Dry-run mode - no changes were made to GitHub.[/dim]")
    if result.posted_comment:
        console.print("[green]Posted triage comment to GitHub.[/green]")
    if result.applied_labels:
        console.print(f"[green]Applied labels:[/green] {', '.join(result.applied_labels)}")


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def _render_batch_summary(results: list[TriageResult]) -> None:
    table = Table(title=f"Batch triage - {len(results)} issues", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right")
    table.add_column("Title")
    table.add_column("Category")
    table.add_column("Priority")
    table.add_column("Dup")
    table.add_column("Safeguard")

    for r in results:
        cat = CATEGORY_BY_SLUG.get(r.analysis.category)
        sg_abbr = "-"
        if r.safeguard is not None:
            sg_abbr = SAFEGUARD_STATUS_ABBR.get(r.safeguard.status, "?")
        table.add_row(
            str(r.issue.number),
            _truncate(r.issue.title, 40),
            cat.display_name if cat else r.analysis.category,
            r.analysis.priority,
            f"{r.analysis.duplicate_likelihood:.0%}",
            sg_abbr,
        )
    console.print(table)


def _output_json(payload: Any) -> None:
    console.print_json(json.dumps(payload, indent=2))


@app.command("triage")
def triage_command(
    repo: Annotated[str, typer.Option("--repo", help="GitHub repository (owner/name).")],
    issue: Annotated[int | None, typer.Option("--issue", help="Issue number to triage.")] = None,
    recent: Annotated[
        int | None,
        typer.Option("--recent", help="Triage N most recent open issues."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output JSON only.")] = False,
    mock: Annotated[bool, typer.Option("--mock", help="Offline mock mode (no API calls).")] = False,
    mock_llm: Annotated[
        bool,
        typer.Option(
            "--mock-llm",
            help="Fetch real GitHub issues but use offline mock LLM (no XAI_API_KEY needed).",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Analyze only; never write to GitHub."),
    ] = False,
    confirm: Annotated[
        bool,
        typer.Option("--confirm", help="Confirm GitHub write actions."),
    ] = False,
    privacy_insight: Annotated[
        bool,
        typer.Option(
            "--privacy-insight/--no-privacy-insight",
            help="Flag possible PHI/DICOM concerns.",
        ),
    ] = True,
    safeguards: Annotated[
        bool,
        typer.Option(
            "--safeguards/--no-safeguards",
            help="Run local draft safeguard heuristics (default: on).",
        ),
    ] = True,
    post_comment: Annotated[
        bool,
        typer.Option("--post-comment", help="Post draft response (requires --confirm)."),
    ] = False,
    apply_labels: Annotated[
        bool,
        typer.Option("--apply-labels", help="Apply suggested labels (requires --confirm)."),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output.")] = False,
) -> None:
    """Triage one issue or a batch of recent issues."""
    setup_logging(verbose)

    if issue is None and recent is None:
        err_console.print("[red]Provide --issue N or --recent N.[/red]")
        raise typer.Exit(code=1)

    if issue is not None and recent is not None:
        err_console.print("[red]Use either --issue or --recent, not both.[/red]")
        raise typer.Exit(code=1)

    if mock and mock_llm:
        err_console.print("[red]Use either --mock or --mock-llm, not both.[/red]")
        raise typer.Exit(code=1)

    options = TriageOptions(
        repo=repo,
        issue_number=issue,
        recent=recent,
        mock=mock,
        mock_llm=mock_llm,
        dry_run=dry_run or not (post_comment or apply_labels),
        confirm=confirm,
        privacy_insight=privacy_insight,
        safeguards=safeguards,
        post_comment=post_comment,
        apply_labels=apply_labels,
    )

    try:
        orchestrator = build_orchestrator(mock=mock, mock_llm=mock_llm)

        if recent is not None:
            results = orchestrator.triage_recent(options)
            if json_output:
                _output_json([r.to_dict() for r in results])
            else:
                _render_batch_summary(results)
                if verbose:
                    for r in results:
                        render_triage_result(r, verbose=True)
        else:
            result = orchestrator.triage_one(options)
            if json_output:
                _output_json(result.to_dict())
            else:
                render_triage_result(result, verbose=verbose)

    except ValueError as exc:
        err_console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        err_console.print(f"[red]Triage failed:[/red] {exc}")
        if verbose:
            err_console.print_exception()
        raise typer.Exit(code=2) from exc


def run() -> None:
    app()


if __name__ == "__main__":
    run()
