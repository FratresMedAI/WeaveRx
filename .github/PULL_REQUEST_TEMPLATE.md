## Summary

<!-- What changed and why? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactor / tooling
- [ ] Other (describe below)

## Testing

- [ ] `ruff check .`
- [ ] `mypy src/weaverx`
- [ ] `pytest` (offline tests pass)
- [ ] Added or updated tests for behavior changes

## Safety checklist

WeaveRx is human-in-the-loop tooling. Confirm:

- [ ] No weakening of dry-run / `--confirm` gates
- [ ] Safeguards remain advisory (warn-only)
- [ ] No features that encourage posting PHI or patient identifiers
- [ ] CLI or docs disclaimers updated if user-facing safety text changed

## Related issues

<!-- Fixes #123 or links to discussion -->
