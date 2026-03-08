## Code Review Comment Convention

Prefix each review comment with one of the following labels.

| Label | Meaning | Action |
| --- | --- | --- |
| **must** | Blocking issue (bug, security, spec violation) | Fix before merge |
| **should** | Strongly recommended (quality, maintainability) | Fix unless strong reason |
| **imo** | Subjective suggestion (design, naming preference) | Optional; open to discussion |
| **nits** | Minor style / typo / formatting | Completely optional |
| **fyi** | Informational only, no change needed | No action required |

### Examples

```text
must: Auth token is written to logs. Fix before merge.
should: N+1 query will degrade with larger page sizes.
imo: A Strategy pattern might clean this up nicely.
nits: Missing trailing comma.
fyi: Reference: https://example.com/best-practices
```
