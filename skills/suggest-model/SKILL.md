---
name: suggest-model
description: Recommend which model tier (haiku/sonnet/opus) a role should be pinned to, based on a short quiz about the task it handles.
---

# Suggest a model for a role

Ask about the role being defined, one question at a time, waiting for an
answer before asking the next:

1. **Cost of being wrong** — if this role gets something wrong, how costly
   is that: low, medium, or high?
2. **Judgment or pattern-following** — does this role mainly make
   judgment/design calls, or mostly follow an established pattern?
3. **Context needed** — how much surrounding context does it typically
   need to hold at once: just the immediate file(s), the whole module or
   feature, or the whole repo and its history?

## Scoring

| Answer | Points |
|---|---|
| Cost: low | 0 |
| Cost: medium | 1 |
| Cost: high | 2 |
| Style: pattern-following | 0 |
| Style: judgment | 2 |
| Context: single file(s) | 0 |
| Context: module/feature | 1 |
| Context: whole repo/history | 2 |

Sum the three answers' points. Recommend:

- 0–1 → `haiku`
- 2–3 → `sonnet`
- 4–6 → `opus`

This is a deterministic lookup, not a closer judgment call each time —
apply the table exactly as written, including right at the 1/2 and 3/4
boundaries.

## Output

State the recommended tier and the exact line to paste:

```
model: <tier>
```

Say which answers drove the score in one line (e.g. "high cost + judgment
+ whole-repo context → opus"), so the person can sanity-check the
recommendation rather than take it on faith.
