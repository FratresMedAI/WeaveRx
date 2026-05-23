"""Shared utilities: env, logging, confirmation gates."""

from __future__ import annotations

import logging
import os
import sys
from typing import Literal

ExitCode = Literal[0, 1, 2]

LOG = logging.getLogger("weaverx")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )


def get_env(name: str, *, required: bool = False, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    if required and not value:
        raise ValueError(
            f"Missing required environment variable: {name}. "
            f"Set {name} or use --mock for offline testing."
        )
    return value


def is_mock_mode(cli_mock: bool = False) -> bool:
    return cli_mock or os.environ.get("WEAVERX_MOCK", "").lower() in {"1", "true", "yes"}


def require_confirmation(
    *,
    confirm: bool,
    dry_run: bool,
    action_description: str,
) -> bool:
    """Return True if the action may proceed."""
    if dry_run:
        LOG.info("Dry-run: skipping %s", action_description)
        return False
    if confirm:
        return True
    LOG.warning(
        "Skipped %s (pass --confirm to apply changes).",
        action_description,
    )
    return False


def parse_repo(repo: str) -> tuple[str, str]:
    parts = repo.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError(
            f"Invalid repo format: {repo!r}. Expected 'owner/name' (e.g. 'Project-MONAI/MONAI')."
        )
    return parts[0], parts[1]
