# Configuration

WeaveRx reads settings from environment variables and CLI flags. CLI flags take precedence where both apply.

## GitHub

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `GITHUB_TOKEN` | For writes | Personal access token or `GITHUB_TOKEN` in Actions. Needed to post comments or apply labels. Optional for read-only triage on public repos. |

## LLM providers

WeaveRx uses [LiteLLM](https://github.com/BerriAI/litellm). Set **one** provider's API key.

| Variable | Provider | Description |
| -------- | -------- | ----------- |
| `XAI_API_KEY` | Grok (default) | xAI API key |
| `ANTHROPIC_API_KEY` | Anthropic | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI-compatible | OpenAI, Azure OpenAI, vLLM, or other OpenAI-compatible gateways |
| `OPENAI_API_BASE` | OpenAI-compatible | Custom API base URL (optional; omit for `api.openai.com`) |
| `WEAVERX_LLM_PROVIDER` | All | Override default provider: `grok`, `anthropic`, or `openai` |
| `WEAVERX_LLM_MODEL` | All | Override model id (e.g. `anthropic/claude-3-5-haiku-20241022`) |

CLI equivalent: `--llm-provider grok|anthropic|openai`

## Offline and mock modes

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `WEAVERX_MOCK` | off | Set to `1`, `true`, or `yes` for fully offline mock GitHub + mock LLM |

CLI equivalents: `--mock` (offline GitHub + mock LLM), `--mock-llm` (real GitHub, mock LLM)

## Safeguards

Local heuristic checks on generated drafts. No LLM calls on this path.

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `WEAVERX_SAFEGUARDS` | `1` | Set to `0`, `false`, or `no` to disable |
| `WEAVERX_SAFEGUARD_ENTROPY_MAX` | `5.5` | Shannon entropy threshold (bits per character) |
| `WEAVERX_SAFEGUARD_MAX_CHARS` | `6000` | Maximum draft length before flagging |

CLI equivalents: `--safeguards` / `--no-safeguards`

## GitHub Action

The composite action passes inputs as environment variables. See [action.yml](https://github.com/FratresMedAI/WeaveRx/blob/master/action.yml) and [GitHub Action](index.md#github-action) in this site.

## Quick reference

```bash
# Offline demo — no env vars
weaverx triage --repo Project-MONAI/MONAI --issue 42 --mock

# Real LLM, dry-run
export XAI_API_KEY=xai-...
weaverx triage --repo owner/repo --issue 1234 --dry-run

# Post comment (requires token + explicit confirm flags)
export GITHUB_TOKEN=ghp_...
weaverx triage --repo owner/repo --issue 1234 --post-comment --confirm
```

More examples: [llm_provider_examples.md](https://github.com/FratresMedAI/WeaveRx/blob/master/examples/llm_provider_examples.md).
