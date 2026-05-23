# CLI reference

```
weaverx triage --repo owner/repo [--issue N | --recent N] [options]
```

| Flag | Description |
| --- | --- |
| `--mock` | Offline mode (sample GitHub + mock LLM) |
| `--mock-llm` | Real GitHub, offline mock LLM |
| `--dry-run` | Analyze only; never write (default unless posting) |
| `--json` | Machine-readable JSON output |
| `--llm-provider` | `grok`, `anthropic`, or `openai` |
| `--confirm` | Required to post comments or apply labels |
| `--post-comment` | Post draft (needs `--confirm`) |
| `--apply-labels` | Apply suggested labels (needs `--confirm`) |
| `--privacy-insight` | Flag possible PHI/DICOM concerns (default: on) |
| `--safeguards / --no-safeguards` | Local draft heuristics (default: on) |
| `-v, --verbose` | Full draft, sources, debug logging |

## JSON output fields

| Field | Description |
| --- | --- |
| `status` | `ready_for_review` or `posted` |
| `issue` | GitHub issue metadata |
| `analysis` | Raw LLM triage (category, priority, labels, raw draft, reasoning) |
| `sources` | Issue excerpts that grounded the triage |
| `draft_response` | **Refined** postable comment (use this for posting) |
| `safeguard` | Local heuristic score, status, triggered flags, metrics |
| `llm` | Provider and model used |
| `duplicate_matches` | Similar recent issues (heuristic, not embeddings yet) |

Full sample: [sample_triage_output.json](https://github.com/FratresMedAI/WeaveRx/blob/master/examples/sample_triage_output.json).
