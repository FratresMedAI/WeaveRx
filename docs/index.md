# WeaveRx

**Medical AI GitHub issue triage with auditable drafts, local safeguards, and human-in-the-loop defaults.**

WeaveRx classifies MONAI, nnU-Net, and related project issues — reproducibility blockers, dataset access, subgroup performance, privacy/DICOM, and clinical validation requests — and produces a **review-ready draft** with **sources** and **safeguard scores** (local heuristics, no extra LLM calls).

## Quick links

- [README on GitHub](https://github.com/FratresMedAI/WeaveRx/blob/master/README.md) — install, screenshots, quickstart
- [Configuration](configuration.md) — environment variables
- [Examples](https://github.com/FratresMedAI/WeaveRx/tree/master/examples) — JSON samples and CLI captures
- [Ethics](https://github.com/FratresMedAI/WeaveRx/blob/master/ETHICS.md) — not for clinical use; human review required

Install: `pip install weaverx`

## See it in action

![Clean triage screenshot](screenshots/triage-clean.png)

Command: `weaverx triage --repo Project-MONAI/MONAI --issue 42 --mock`

![Safeguard warning screenshot](screenshots/safeguard-warning.png)

Safeguard checks are advisory — they flag drafts for review; they never auto-block posting.

Text fallbacks: [examples/captures/](https://github.com/FratresMedAI/WeaveRx/tree/master/examples/captures)

## GitHub Action

Dry-run triage on new issues via [action.yml](https://github.com/FratresMedAI/WeaveRx/blob/master/action.yml):

```yaml
- uses: FratresMedAI/WeaveRx@v0.1.1
  with:
    repo: ${{ github.repository }}
    issue_number: ${{ github.event.issue.number }}
    dry_run: "true"
  env:
    XAI_API_KEY: ${{ secrets.XAI_API_KEY }}
```

![GitHub Action dry-run log](screenshots/github-action-dry-run.png)

## Documentation map

| Topic | Page |
| --- | --- |
| Medical AI categories | [reference/categories.md](reference/categories.md) |
| Draft safeguards | [reference/safeguards.md](reference/safeguards.md) |
| CLI flags and JSON | [reference/cli.md](reference/cli.md) |
| LLM providers | [reference/llm-providers.md](reference/llm-providers.md) |
| Releasing | [releasing.md](releasing.md) |

Local preview: `pip install -e ".[docs]" && mkdocs serve` — see [Documentation setup](setup.md).
