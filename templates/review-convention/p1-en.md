## Code Review Comment Convention

Prefix each review comment with a priority label.
Reviewees should decide their response based on the level.

| Level | Meaning | Action |
|-------|---------|--------|
| **P1** | Must fix (bug, security, spec violation) | Fix before merge |
| **P2** | Strongly recommended (performance, maintainability impact) | Fix unless strong reason not to |
| **P3** | Suggestion (design improvement, readability) | Optional; can defer |
| **P4** | Minor (typo, style, naming preference) | Nits; completely optional |
| **P5** | Informational / reference link (no change needed) | FYI; no action required |

### Examples

```
P1: Auth token is written to logs. Must fix before merge.
P2: This N+1 query will degrade as pagination grows.
P3: This could be refactored with a Strategy pattern (no rush).
P4: `data` → `userList` would better convey intent.
P5: Reference: https://example.com/best-practices
```
