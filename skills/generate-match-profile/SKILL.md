---
name: generate-match-profile
description: Derive a compact Work Experience/match-profile.md (~1 page) and Job Applications/scout-searches.json from the user's experience notes for job-scout filtering. Trigger when setting up discovery, after Work Experience notes change materially, or when the user asks to refresh their match profile or saved OpenPostings searches.
---

# Generate Match Profile

Produce the discovery-side mirror of a signal report: a short, cheap-to-score profile that `job-scout` uses instead of dumping the full `Work Experience/` notes into every filter call. Also seed/refresh the saved-search config the scout runs against OpenPostings.

## When to use

- First-time OpenPostings discovery setup
- User says experience notes changed and wants the profile / searches refreshed
- `job-scout` finds `match-profile.md` missing or clearly stale vs. recent roles

## Inputs

- **Required:** `Work Experience/` directory (experience notes, `skills - technical.md`, `work history.md`, optional `interests.md`)
- **Optional:** `Job Targets/` notes (preferred titles, location/remote preferences, environment fit) — use when present to set dealbreakers and target titles more accurately
- **Optional:** Existing `Work Experience/match-profile.md` and `Job Applications/scout-searches.json` (preserve user-tuned search queries unless regenerating searches explicitly)

## Process

1. **Read** work history dates/titles, technical skills with approximate tenure, and any stated preferences from `Job Targets/` / personal notes.
2. **Write** `Work Experience/match-profile.md` using the format below. Cap at ~1 page. Be concrete; no fluff.
3. **Write or refresh** `Job Applications/scout-searches.json`:
   - One narrow search per target-title / skill cluster (typically 3–6 searches).
   - Map fields to `openpostings search` flags (`search`, `remote`, `pay_min`, `countries`, `states`, `limit` suggestion).
   - Keep searches **narrow** (title + skill keywords). Broad queries flood the scout; OpenPostings matches company/title/location substrings only — never description text.
   - Preserve `last_run` if the file already exists and you are only editing search definitions.
   - If the user has hand-tuned queries, ask before overwriting them — or only refresh `match-profile.md`.

## Output: `Work Experience/match-profile.md`

```markdown
# Match Profile

## Target titles
- <exact title strings to prefer in search / skim>

## Seniority band
<e.g. Senior IC / Staff; years overall>

## Hard skills (with approx. years)
- <skill>: ~<N> years — <where / note>
- ...

## Strong domains
- <cloud infra, applied AI/RAG, etc.>

## Dealbreakers
- Location / remote: <constraint>
- Salary floor: <if known, else "unspecified">
- Visa / clearance: <e.g. no sponsorship needed / no clearance>
- Other: <must-not roles, title traps>

## Soft preferences (not knockouts)
- <hybrid vs remote, company stage, etc.>

## Notes for scoring
- <gaps to watch, e.g. named-web-framework tenure>
```

## Output: `Job Applications/scout-searches.json`

```json
{
  "version": 1,
  "last_run": null,
  "searches": [
    {
      "id": "senior-ai-engineer",
      "description": "Senior / Staff applied AI roles",
      "search": "Senior AI Engineer",
      "remote": "all",
      "pay_min": null,
      "countries": [],
      "states": [],
      "limit": 2000
    }
  ]
}
```

Field notes:

| Field | Maps to CLI |
|-------|-------------|
| `search` | `--search` (space-separated; matches company/title/location only) |
| `remote` | `--remote` (`all` \| `remote` \| `hybrid` \| `non_remote`) |
| `pay_min` | `--pay-min` (omit / null if unused) |
| `countries` / `states` | `--countries` / `--states` CSV |
| `limit` | `--limit` — **always ≥ 2000 when using `--new-since`** (client-side filter runs after the server limit) |

`job-scout` maintains `last_run` (ISO date) after each successful run.

## Rules

- Never pass the full experience dump into scout scoring — the profile is the contract.
- Prefer fewer, sharper searches over many overlapping ones (each search is ~15–20s against the full DB).
- Do not invent skills or years not supported by the notes.
- Regenerate on demand; do not silently overwrite hand-tuned `scout-searches.json` without confirming.

## What NOT to do

- Do not run OpenPostings searches from this skill — that is `job-scout`.
- Do not create per-job folders or tracker rows.
- Do not duplicate CLI flag documentation; see `openpostings-search`.
