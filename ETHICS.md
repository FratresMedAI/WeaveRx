# Ethics and responsible use

WeaveRx is built for **open-source maintainers** of medical AI projects (MONAI, nnU-Net, and related ecosystems). It is not a clinical product.

## What WeaveRx is

- Maintainer support tooling for GitHub issue triage
- A draft assistant with **human review required** before any post
- A local safeguard layer that **warns** about risky drafts — it does not auto-block posting

## What WeaveRx is not

- **Not for clinical use** — do not use triage output for diagnosis, treatment, or patient care decisions
- **Not medical advice** — drafts are suggestions for issue threads, not clinical guidance
- **Not legal or compliance advice** — privacy flags and safeguard heuristics are incomplete; they do not replace IRB, legal, or HIPAA/GDPR review
- **Not a PHI-safe channel** — GitHub issues are public or semi-public; never paste patient identifiers or protected health information

## Human-in-the-loop

Every draft comment must be reviewed by a maintainer before posting. WeaveRx defaults to dry-run mode and requires explicit `--confirm` for writes.

Safeguard scores are **advisory**. A `clean` score does not guarantee a draft is safe to post.

## Privacy

- Use `--privacy-insight` (default on) to flag possible PHI/DICOM concerns in issue text
- Heuristic scanning can miss sensitive content and may false-positive on technical terms
- For deeper audit workflows, see related tooling such as [Safire](https://github.com/FratresMedAI/Safire)

## Research and citations

If you use WeaveRx in academic work, see [CITATION.cff](CITATION.cff) and the README **Citing WeaveRx** section.

## Reporting concerns

- Security vulnerabilities: [SECURITY.md](SECURITY.md)
- Community behavior: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Product feedback: GitHub issues with redacted data only
