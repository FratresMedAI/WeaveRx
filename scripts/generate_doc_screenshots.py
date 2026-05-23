#!/usr/bin/env python3
"""Generate README terminal screenshots (doc tooling only)."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from rich.console import Console
from rich.terminal_theme import MONOKAI

from weaverx.cli import render_triage_result
from weaverx.safeguards import run_safeguards
from weaverx.triage import TriageOptions, TriageOrchestrator

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "docs" / "screenshots"


def _build_clean_result():
    orchestrator = TriageOrchestrator(github_token=None, mock=True)
    return orchestrator.triage_one(
        TriageOptions(
            repo="Project-MONAI/MONAI",
            issue_number=42,
            mock=True,
            dry_run=True,
        )
    )


def _build_safeguard_result():
    result = _build_clean_result()
    bad_draft = (
        "Hi @researcher-dev - please set api_key=abcd1234efgh5678 in your environment.\n\n"
        + ("Thanks for reporting this reproduction issue. " * 35)
    )
    safeguard = run_safeguards(
        bad_draft,
        issue_title=result.issue.title,
        issue_body=result.issue.body,
    )
    return replace(result, draft_response=bad_draft, safeguard=safeguard)


def _svg_to_png(svg_path: Path, png_path: Path) -> None:
    try:
        import cairosvg

        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(png_path),
            output_width=1200,
        )
        return
    except (ImportError, OSError):
        pass

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit(
            "PNG export needs cairosvg (Linux/macOS) or playwright (Windows). "
            "Try: pip install playwright && playwright install chromium"
        ) from exc

    svg_content = svg_path.read_text(encoding="utf-8")
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;background:#0c0c0c;padding:8px'>"
        f"{svg_content}</body></html>"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1240, "height": 900})
        page.set_content(html, wait_until="load")
        page.locator("svg").screenshot(path=str(png_path), timeout=60_000)
        browser.close()


def _export_png(result, png_path: Path, *, verbose: bool = False) -> None:
    console = Console(
        record=True,
        width=100,
        force_terminal=True,
        color_system="truecolor",
    )
    render_triage_result(result, verbose=verbose, output_console=console)
    svg_path = png_path.with_suffix(".svg")
    console.save_svg(str(svg_path), title="WeaveRx", theme=MONOKAI)
    _svg_to_png(svg_path, png_path)
    svg_path.unlink(missing_ok=True)


def _export_text(result, txt_path: Path, *, verbose: bool = False) -> None:
    console = Console(record=True, width=100, force_terminal=True, color_system="truecolor")
    render_triage_result(result, verbose=verbose, output_console=console)
    txt_path.write_text(console.export_text(clear=False), encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    captures_dir = REPO_ROOT / "examples" / "captures"
    captures_dir.mkdir(parents=True, exist_ok=True)

    clean_path = OUTPUT_DIR / "triage-clean.png"
    warning_path = OUTPUT_DIR / "safeguard-warning.png"

    clean_result = _build_clean_result()
    warning_result = _build_safeguard_result()

    print(f"Writing {clean_path}")
    _export_png(clean_result, clean_path)
    _export_text(clean_result, captures_dir / "triage-clean.txt")

    print(f"Writing {warning_path}")
    _export_png(warning_result, warning_path)
    _export_text(warning_result, captures_dir / "safeguard-warning.txt")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
