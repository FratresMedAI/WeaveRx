# Draft safeguards

After generating a draft, WeaveRx runs **fast, local-only** checks — **no LLM calls** on the safeguard path. Flags are **advisory**; they never auto-block posting.

| Check | Threshold (default) | What it detects |
| --- | --- | --- |
| **Entropy** | Shannon > 5.5 bits/char | Possible encoded or obfuscated content |
| **Length** | > 6000 characters | Suspiciously long drafts |
| **Repetition** | ratio > 0.35 or repeated 4-grams | Heavy copy-paste or looped text |
| **Patterns** | regex heuristics | Credential-like strings, base64 blobs, private key markers, excessive markdown links (>15) |
| **Relevance** | keyword overlap < 0.08 | Draft may be off-topic vs issue |

| Score | Status | Meaning |
| --- | --- | --- |
| 0.0 – 2.9 | `clean` | No meaningful red flags |
| 3.0 – 6.9 | `review_recommended` | Skim draft before posting |
| 7.0 – 10.0 | `high_risk` | Multiple or severe heuristics fired |

Disable: `--no-safeguards` or `WEAVERX_SAFEGUARDS=0`. Tune: `WEAVERX_SAFEGUARD_ENTROPY_MAX`, `WEAVERX_SAFEGUARD_MAX_CHARS`.

See the [safeguard warning screenshot](../screenshots/safeguard-warning.png) and [sample_safeguard_warning.json](https://github.com/FratresMedAI/WeaveRx/blob/master/examples/sample_safeguard_warning.json).

Complements privacy keyword scanning. [Safire](https://github.com/FratresMedAI/Safire) is a separate path for deeper audit tooling.
