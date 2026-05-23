# WeaveRx

**Supportive AI triage for medical AI GitHub issues and PRs.**

WeaveRx helps researchers, clinicians, and maintainers bring clarity to the steady flow of GitHub issues in medical AI projects. It illuminates questions around datasets, model performance on specific pathologies, reproducibility (MONAI, nnU-Net, and friends), clinical validation, and privacy — then offers warm, practical draft responses you can review before posting.

Built for the community, not as a gatekeeper.

---

## Why WeaveRx?

Medical AI repos face a unique mix of issues: dataset licensing friction, subgroup performance concerns, environment reproducibility, IRB-adjacent privacy questions, and integration with clinical workflows. Generic triage bots miss that nuance.

WeaveRx categories and prompts are tuned for this world — restorative in tone, concrete in guidance.

---

## Quickstart

**Requirements:** Python 3.11+

```bash
cd weaverx
pip install -e ".[dev]"
```

Try it offline immediately (no API keys needed):

```bash
weaverx triage --repo Project-MONAI/MONAI --issue 42 --mock
```

With real GitHub data (read-only, no token needed for public repos):

```bash
weaverx triage --repo Project-MONAI/MONAI --issue 1234 --mock-llm --dry-run
```

With Grok analysis:

```bash
export GITHUB_TOKEN=ghp_...   # optional for public repos; recommended for rate limits
export XAI_API_KEY=xai-...

weaverx triage --repo Project-MONAI/MONAI --issue 1234 --dry-run
```

JSON output for automation:

```bash
weaverx triage --repo MIC-DKFZ/nnUNet --issue 100 --mock --json
```

Batch recent issues:

```bash
weaverx triage --repo Project-MONAI/MONAI --recent 5 --mock
```

---

## Example repositories

These are well-known medical AI projects where WeaveRx shines. Use `--dry-run` on repos you don't maintain:

| Repository | Good for triaging |
|---|---|
| [Project-MONAI/MONAI](https://github.com/Project-MONAI/MONAI) | Transforms, reproducibility, integration |
| [MIC-DKFZ/nnUNet](https://github.com/MIC-DKFZ/nnUNet) | Training configs, benchmark reproduction |
| [DeepLearning/Medical](https://github.com/DeepLearning/Medical) | Tutorials, clinical ML patterns |

---

## Medical AI categories

| Category | What we look for |
|---|---|
| **Dataset Access & Licensing** | Download links, usage terms, attribution, redistribution |
| **Model Performance (Pathology/Subgroup)** | Accuracy on specific diseases, sites, or patient groups |
| **Reproducibility & Environment** | MONAI/nnU-Net versions, CUDA/PyTorch, can't reproduce paper results |
| **Clinical Validation Request** | External validation, reader studies, deployment questions |
| **Privacy/Compliance/DICOM** | PHI, de-identification, HIPAA/GDPR, DICOM metadata |
| **Bug** | Crashes, incorrect outputs |
| **Feature/Integration Request** | New capabilities, framework hooks |
| **Documentation** | Missing or unclear tutorials and API docs |

Each triage returns: **category**, **priority**, **duplicate likelihood**, **suggested labels**, **privacy flags** (optional), a **draft response**, and **safeguard results** (entropy/heuristic checks on the draft).

---

## CLI reference

```
weaverx triage --repo owner/repo [--issue N | --recent N] [options]
```

| Flag | Description |
|---|---|
| `--mock` | Offline mode with sample GitHub data (no API calls) |
| `--mock-llm` | Fetch real GitHub issues but use offline mock LLM |
| `--dry-run` | Analyze only; never write to GitHub (default unless posting) |
| `--json` | Machine-readable JSON output |
| `--confirm` | Required to post comments or apply labels |
| `--post-comment` | Post the draft response (needs `--confirm`) |
| `--apply-labels` | Apply suggested labels (needs `--confirm`) |
| `--privacy-insight` | Flag possible PHI/DICOM concerns (default: on) |
| `--safeguards / --no-safeguards` | Run local draft safeguard heuristics (default: on) |
| `-v, --verbose` | Full draft text and debug logging |

---

## Safety first

WeaveRx is designed for **human-in-the-loop** triage:

1. **Never paste patient data in GitHub issues.** WeaveRx flags possible PHI/DICOM mentions but cannot guarantee detection.
2. **Default is read-only.** Writes require both `--post-comment`/`--apply-labels` **and** `--confirm`.
3. **Use `--dry-run`** when exploring repos you don't maintain.
4. **Use `--mock`** in CI demos and local development without tokens.
5. **Token scopes:** public repos work without `GITHUB_TOKEN` (rate-limited). Set `GITHUB_TOKEN` for higher limits; add `issues:write` only if posting comments/labels.

### Draft safeguards

After generating a draft response, WeaveRx runs **fast, local-only** checks — no LLM calls on the safeguard path. These heuristics are advisory: they **warn and flag**, they do not auto-block posting.

| Check | What it detects |
|---|---|
| **Entropy** | Unusually high Shannon entropy (possible encoded or obfuscated content) |
| **Length / repetition** | Suspiciously long drafts or heavy word/phrase repetition |
| **Patterns** | Credential-like strings, base64 blobs, excessive markdown links, private key markers |
| **Relevance** | Low keyword overlap between the issue and the draft (possible off-topic response) |

**Output:** a score (0–10), status (`clean`, `review_recommended`, `high_risk`), triggered finding IDs, and metrics. Disable with `--no-safeguards` or `WEAVERX_SAFEGUARDS=0`. Optional env overrides: `WEAVERX_SAFEGUARD_ENTROPY_MAX`, `WEAVERX_SAFEGUARD_MAX_CHARS`.

This complements privacy keyword scanning. [Safire](https://github.com/FratresMedAI/Safire) remains a separate path for deeper audit tooling; WeaveRx safeguards are built-in and lightweight by design.

---

## GitHub Action

Drop [`action.yml`](action.yml) into your medical AI repo:

```yaml
- uses: your-org/weaverx@v0.1.0
  with:
    repo: ${{ github.repository }}
    issue_number: ${{ github.event.issue.number }}
    dry_run: "true"
  env:
    XAI_API_KEY: ${{ secrets.XAI_API_KEY }}
```

To post comments (explicit opt-in):

```yaml
    dry_run: "false"
    post_comment: "true"
```

See [`.github/workflows/triage-on-issue.yml`](.github/workflows/triage-on-issue.yml) for a starter workflow.

---

## Development

```bash
pip install -e ".[dev]"
ruff check .
mypy src/weaverx
pytest
```

---

## Roadmap

- PyPI publish (`pip install weaverx`)
- GitHub Marketplace / Actions listing
- Embedding-based duplicate detection (`weaverx[embeddings]`)
- PR triage mode (`--pr`) and CSV batch export
- Maintainer HTML report from JSON output
- Deeper privacy scanner (DICOM tag patterns, de-ID checklist)

---

## License

MIT — built with care for the medical AI open-source community.
