# Match Breakdown Script Design

**Date:** 2026-04-29
**Script:** `Tools/get_match_breakdown_2026_v1.py`

## Purpose

A command-line tool that retrieves alliance and opponent pre-scouting notes from MongoDB
for a specific match, giving the strategy team a quick breakdown before a match: what
strengths your alliance brings and what weaknesses/observations exist for your opponents.

## Inputs

Three inputs, all optional as CLI arguments (prompted interactively if omitted):

| Flag | Long form | Example | Description |
|------|-----------|---------|-------------|
| `-e` | `--event` | `2026nvlv` | TBA event code |
| `-t` | `--team` | `frc6413` | Full TBA team key |
| `-m` | `--match` | `qm5` | Match number in TBA format |

If any argument is missing from the command line, the user is prompted with the same
`input(...).strip()` style used by existing Tools scripts. Entering `quit` at any
prompt exits cleanly.

## Match Key Parsing

A regex splits the TBA match format into MongoDB query fields:

| Input | `comp_level` | `set_number` | `match_number` |
|-------|-------------|-------------|----------------|
| `qm5` | `qm` | `1` | `5` |
| `sf2m1` | `sf` | `2` | `1` |
| `f1m2` | `f` | `1` | `2` |
| `qf1m1` | `qf` | `1` | `1` |

An invalid format (fails regex) prints a red error and exits.

## Data Retrieval

Primary MongoDB only (no secondary). Two queries per run:

**Match lookup** — `matches` collection:
```
{
  "event_key": eventCode,
  "comp_level": compLevel,
  "set_number": setNumber,
  "match_number": matchNumber
}
```
Determines which alliance (blue or red) contains the input team. Partners are the
other two teams on the same alliance; opponents are all three teams on the other
alliance. If no match document is found, print a red error and exit.

**Prescout lookup** — `scouting` collection, one query per team (6 total):
```
{
  "docType": "prescout",
  "eventCode": eventCode,
  "team": "<number>"        # frc prefix stripped, e.g. "6413"
}
```
The `frc` prefix is stripped because `prescouting_upload.py` stores `team` as a
bare number string (e.g. `"6413"`). If no document is found, `notes` is treated
as `None` and "No data" is displayed.

## Output Format

Two blocks printed to the terminal using colorama colors:

### Alliance Block (blue header)
```
=== YOUR ALLIANCE ===

[6413] (YOUR TEAM)
  Strengths:
    <text, or "No data" in yellow>

[1234]
  Strengths:
    <text, or "No data" in yellow>

[5678]
  Strengths:
    <text, or "No data" in yellow>
```

### Opponent Block (red header)
```
=== OPPOSING ALLIANCE ===

[254]
  Weaknesses:
    <text, or "No data" in yellow>
  Observations:
    <text, or "No data" in yellow>

[1114]
  ...

[2056]
  ...
```

- All team numbers are displayed without the `frc` prefix.
- Team headers for alliance teams are printed in blue; opponent team headers in red.
- "No data" is printed in yellow.
- The "YOUR TEAM" label distinguishes the queried team from its alliance partners.
- If the match is not found in MongoDB, a red error message is printed and the script exits.

## Code Structure

Follows the pattern of `get_event_schedule_from_mongodb_2026_v1.py` exactly:

- Module-level `_logger` with `setup_logger()` / `get_logger()` functions
- `validate_configuration()` checking credentials and V5 schema constants
- `get_database()` returning a `Database` or `None`
- `parse_match_key(match_key: str)` — regex parser, returns `(comp_level, set_number, match_number)` or raises `ValueError`
- `get_match(db, event_code, comp_level, set_number, match_number)` — returns match dict or `None`
- `get_prescout(db, event_code, team_key)` — strips `frc` prefix, returns notes dict or `None`
- `print_alliance_block(team_key, partners, prescout_map)` — prints alliance strengths
- `print_opponent_block(opponents, prescout_map)` — prints opponent weaknesses + observations
- `main()` — argparse setup, input prompting, orchestration

## Dependencies

No new dependencies. Uses the same packages already in the Tools workspace:
`colorama`, `pymongo`, `frc_6413_common` (config + credentials).
No TBA API calls — all data comes from MongoDB.
