<p align="center">
  <img src="docs/weaverx-hero.png" alt="WeaveRx — medical AI GitHub issue triage" width="900" />
</p>

# WeaveRx

**Medical AI GitHub issue triage with auditable drafts, local safeguards, and human-in-the-loop defaults.**

WeaveRx helps maintainers of MONAI, nnU-Net, and related projects triage issues faster — classifying reproducibility blockers, dataset access friction, subgroup performance questions, privacy/DICOM concerns, and clinical validation requests. It produces a **review-ready draft comment** with **sources** (issue excerpts that grounded the decision) and **safeguard scores** (local heuristics, no extra LLM calls).

Built for medical AI maintainers, research groups, and hospital OSS teams who need practical tooling — not a gatekeeper bot.

---

## Example output

A typical `--json` result (abbreviated draft text):

```json
{
  "repo": "Project-MONAI/MONAI",
  "status": "ready_for_review",
  "issue": {
    "number": 42,
    "title": "Unable to reproduce nnU-Net training results on BraTS subset",
    "url": "https://github.com/Project-MONAI/MONAI/issues/42",
    "author": "researcher-dev",
    "labels": ["question"]
  },
  "analysis": {
    "category": "reproducibility-environment",
    "priority": "high",
    "impact_summary": "Benchmark reproduction gap may affect trust in reported BraTS metrics.",
    "duplicate_likelihood": 0.15,
    "suggested_labels": ["reproducibility", "nnunet", "question"],
    "privacy_flags": [],
    "reasoning": "Issue cites nnU-Net v2.1 and MONAI transforms on BraTS."
  },
  "sources": [
    {
      "type": "issue_body",
      "snippet": "I'm trying to reproduce the BraTS segmentation benchmark using nnU-Net v2...",
      "reason": "Identified reproducibility concern with version-specific stack."
    },
    {
      "type": "issue_title",
      "snippet": "Unable to reproduce nnU-Net training results on BraTS subset",
      "reason": "Confirmed triage category: reproducibility-environment."
    }
  ],
  "draft_response": "Hi @researcher-dev — thank you for documenting this carefully...",
  "safeguard": {
    "score": 0.0,
    "status": "clean",
    "triggered": [],
    "metrics": { "entropy": 4.69, "char_count": 608, "relevance_ratio": 0.27 }
  },
  "llm": { "provider": "grok", "model": "xai/grok-2-latest" },
  "dry_run": true
}
```

When safeguards flag a draft (advisory only — you still decide whether to post):

```json
"safeguard": {
  "score": 6.5,
  "status": "review_recommended",
  "triggered": [
    {
      "id": "credential_like_pattern",
      "severity": "high",
      "message": "Draft contains a credential-like token pattern (e.g. API key shape)."
    }
  ]
}
```

Full examples: [`examples/sample_triage_output.json`](examples/sample_triage_output.json), [`examples/sample_safeguard_warning.json`](examples/sample_safeguard_warning.json).

<!-- screenshot: CLI table output — see examples/sample_triage_cli.txt -->
<!-- screenshot: batch summary with Safeguard OK/REV/RISK column -->

---

## Why WeaveRx?

- **Domain-tuned** — eight medical AI categories (reproducibility, DICOM/privacy, clinical validation, subgroup performance, and more), not generic bug/feat labels alone.
- **Safety by default** — dry-run unless you explicitly post; `--confirm` required for GitHub writes; local safeguard heuristics on every draft.
- **Auditable** — `sources` cite issue excerpts that informed the triage; `safeguard` scores are computed locally with no LLM on that path.
- **Your LLM stack** — Grok, Anthropic, or OpenAI-compatible endpoints via [LiteLLM](https://github.com/BerriAI/litellm); mock mode for offline CI and demos.

---

## Quickstart

**Requirements:** Python 3.11+

```bash
git clone https://github.com/FratresMedAI/WeaveRx.git
cd WeaveRx
pip install -e ".[dev]"
```

### 1. Mock (zero API keys)

```bash
weaverx triage --repo Project-MONAI/MONAI --issue 42 --mock
```

### 2. Dry-run (real GitHub, offline LLM)

```bash
weaverx triage --repo Project-MONAI/MONAI --issue 1234 --mock-llm --dry-run
```

### 3. Real LLM analysis

**Grok (default):**

```bash
export XAI_API_KEY=xai-...
weaverx triage --repo Project-MONAI/MONAI --issue 1234 --dry-run
```

**Anthropic:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
weaverx triage --repo Project-MONAI/MONAI --issue 1234 --llm-provider anthropic --dry-run
```

**OpenAI-compatible** (OpenAI, Azure, local vLLM, etc.):

```bash
export OPENAI_API_KEY=sk-...
# optional for non-OpenAI hosts:
export OPENAI_API_BASE=https://your-host/v1
export WEAVERX_LLM_MODEL=openai/your-model-name

weaverx triage --repo Project-MONAI/MONAI --issue 1234 --llm-provider openai --dry-run
```

`GITHUB_TOKEN` is optional for public repos (recommended for rate limits). Add `issues:write` only if posting comments or labels.

### 4. JSON for automation

```bash
weaverx triage --repo Project-MONAI/MONAI --issue 42 --mock --json
```

### 5. Batch recent issues

```bash
weaverx triage --repo Project-MONAI/MONAI --recent 5 --mock
```

---

## What a real triage looks like

**Repo:** [Project-MONAI/MONAI](https://github.com/Project-MONAI/MONAI)  
**Issue:** reproducibility question about nnU-Net on BraTS (mock issue #42)

| Field | Typical result |
|---|---|
| Category | Reproducibility & Environment |
| Priority | high |
| Status | `ready_for_review` (dry-run) |
| Sources | Issue title + body excerpts citing nnU-Net / CUDA / MONAI versions |
| Safeguard | `clean` (score 0–2.9) for normal prose drafts |
| Draft | Warm, concrete checklist (environment snapshot, preprocessing, seed/fold) |

CLI layout (see [`examples/sample_triage_cli.txt`](examples/sample_triage_cli.txt)):

```
Category             Reproducibility & Environment
Priority             HIGH
Status               ready for review
Sources              2 excerpt(s) (use --verbose)
Safeguard status     CLEAN
```

Run it yourself: `weaverx triage --repo Project-MONAI/MONAI --issue 42 --mock -v`

---

## Medical AI categories

| Category | What we look for |
|---|---|
| **Dataset Access & Licensing** | Download links, usage terms, attribution |
| **Model Performance (Pathology/Subgroup)** | Accuracy on specific diseases or patient groups |
| **Reproducibility & Environment** | MONAI/nnU-Net versions, CUDA/PyTorch, can't reproduce results |
| **Clinical Validation Request** | External validation, reader studies, deployment |
| **Privacy/Compliance/DICOM** | PHI, de-identification, HIPAA/GDPR, DICOM metadata |
| **Bug** | Crashes, incorrect outputs |
| **Feature/Integration Request** | New capabilities, framework hooks |
| **Documentation** | Missing or unclear tutorials and API docs |

---

## LLM providers

| Provider | CLI | API key env | Default model |
|---|---|---|---|
| Grok | `--llm-provider grok` | `XAI_API_KEY` | `xai/grok-2-latest` |
| Anthropic | `--llm-provider anthropic` | `ANTHROPIC_API_KEY` | `anthropic/claude-3-5-sonnet-20241022` |
| OpenAI-compatible | `--llm-provider openai` | `OPENAI_API_KEY` | `openai/gpt-4o` |

Override model globally: `WEAVERX_LLM_MODEL=anthropic/claude-3-5-haiku-20241022`  
Override provider default: `WEAVERX_LLM_PROVIDER=anthropic`

All providers return the same structured JSON schema (`TriageAnalysis` + `sources`).

---

## JSON output reference

| Field | Description |
|---|---|
| `status` | `ready_for_review` or `posted` |
| `issue` | GitHub issue metadata |
| `analysis` | Raw LLM triage (category, priority, labels, raw draft, reasoning) |
| `sources` | Issue excerpts that grounded the triage (also inside `analysis.sources`) |
| `draft_response` | **Refined** postable comment (use this for posting) |
| `safeguard` | Local heuristic score, status, triggered flags, metrics |
| `llm` | Provider and model used |
| `duplicate_matches` | Similar recent issues (heuristic, not embeddings yet) |

---

## Draft safeguards

After generating a draft, WeaveRx runs **fast, local-only** checks — **no LLM calls** on the safeguard path. Flags are **advisory**; they never auto-block posting.

| Check | Threshold (default) | What it detects |
|---|---|---|
| **Entropy** | Shannon > 5.5 bits/char | Possible encoded or obfuscated content |
| **Length** | > 6000 characters | Suspiciously long drafts |
| **Repetition** | ratio > 0.35 or repeated 4-grams | Heavy copy-paste or looped text |
| **Patterns** | regex heuristics | Credential-like strings, base64 blobs, private key markers, excessive markdown links (>15) |
| **Relevance** | keyword overlap < 0.08 | Draft may be off-topic vs issue |

| Score | Status | Meaning |
|---|---|---|
| 0.0 – 2.9 | `clean` | No meaningful red flags |
| 3.0 – 6.9 | `review_recommended` | Skim draft before posting |
| 7.0 – 10.0 | `high_risk` | Multiple or severe heuristics fired |

Disable: `--no-safeguards` or `WEAVERX_SAFEGUARDS=0`. Tune: `WEAVERX_SAFEGUARD_ENTROPY_MAX`, `WEAVERX_SAFEGUARD_MAX_CHARS`.

Complements privacy keyword scanning. [Safire](https://github.com/FratresMedAI/Safire) is a separate path for deeper audit tooling.

---

## CLI reference

```
weaverx triage --repo owner/repo [--issue N | --recent N] [options]
```

| Flag | Description |
|---|---|
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

---

## Safety first

WeaveRx is **human-in-the-loop** by design:

1. **Never paste patient data in GitHub issues.** Privacy flags are heuristic, not guaranteed.
2. **Default is read-only.** Writes need `--post-comment`/`--apply-labels` **and** `--confirm`.
3. **Use `--dry-run`** on repos you don't maintain.
4. **Use `--mock`** in CI and local demos without tokens.
5. **Review safeguard warnings** before posting flagged drafts.

### Responsible use & limitations

- WeaveRx is **maintainer support tooling**, not medical advice or a clinical decision system.
- It does **not** replace IRB, legal, or compliance review for PHI handling.
- Draft responses may be wrong or incomplete — a human maintainer must review every post.
- Duplicate detection is keyword/heuristic today; near-duplicate issues may be missed until embedding support lands.

---

## GitHub Action

```yaml
- uses: FratresMedAI/WeaveRx@v0.1.0
  with:
    repo: ${{ github.repository }}
    issue_number: ${{ github.event.issue.number }}
    dry_run: "true"
    llm_provider: "grok"
  env:
    XAI_API_KEY: ${{ secrets.XAI_API_KEY }}
    # ANTHROPIC_API_KEY or OPENAI_API_KEY for other providers
```

See [`action.yml`](action.yml) and [`.github/workflows/triage-on-issue.yml`](.github/workflows/triage-on-issue.yml).

---

## Development & contributing

```bash
pip install -e ".[dev]"
ruff check .
mypy src/weaverx
pytest
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for PR expectations and safety constraints.

---

## Roadmap (near-term)

1. **Embedding-based duplicate detection** — optional `weaverx[embeddings]` extra
2. **PR triage mode** — `--pr` for pull request review drafts
3. **PyPI publish** — `pip install weaverx`

---

## License

MIT — see [`LICENSE`](LICENSE).
