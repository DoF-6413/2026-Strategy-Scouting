# External Key Mappings Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the scouting script year-agnostic by externalizing QR key mappings to `mappings.json`, and fix `RandomData2026_v2.py` to emit the `"mo":"s"` routing key.

**Architecture:** A new `Scouting-Scripts/mappings.json` holds all compact→full key mappings keyed by `{year}s` / `{year}d`. A new `scouting_all_v2.py` loads this file at startup, validates that both year mappings exist when the event code is entered, and passes the mapping as parameters to the inflate functions. Adding support for a new game year requires only editing `mappings.json` — no script changes.

**Tech Stack:** Python 3.11+, JSON stdlib (`json`), uv workspace monorepo

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Create | `Scouting-Scripts/mappings.json` | All compact→full key mappings, keyed by year+mode |
| Create | `Scouting-Scripts/scouting_all_v2.py` | Year-agnostic scouting script |
| Keep   | `Scouting-Scripts/scouting_all_2026.py` | Retained as reference; not modified |
| Modify | `Tools/RandomData2026_v2.py` | Add `"mo":"s"` to generated QR payload |
| Modify | `ScoutingMatchScan.bat` | Point to `scouting_all_v2.py` |
| Modify | `UV_SCRIPTS.md` | Update command reference |
| Modify | `README.md` | Update `uv run` example |

---

## mappings.json Structure

`Scouting-Scripts/mappings.json` — one top-level JSON object. Match entries have `key_mapping` and `total_game_pieces_fields`; defense entries have only `key_mapping`.

```json
{
  "2026s": {
    "key_mapping": {
      "cl": "compLevel",
      "mn": "matchNumber",
      "i": "scouter",
      "a1": "autoHub",
      "a2": "autoHubMiss",
      "t1": "teleHub",
      "t2": "teleHubMiss",
      "ns": "noShow",
      "r": "relayed",
      "h": "herded",
      "d": "died",
      "co": "comments"
    },
    "total_game_pieces_fields": ["autoHub", "teleHub"]
  },
  "2026d": {
    "key_mapping": {
      "cl": "compLevel",
      "mn": "matchNumber",
      "i": "scouter",
      "r1": "r1defense",
      "r2": "r2defense",
      "r3": "r3defense",
      "r4": "r1teamNum",
      "r5": "r2teamNum",
      "r6": "r3teamNum",
      "b1": "b1defense",
      "b2": "b2defense",
      "b3": "b3defense",
      "b4": "b1teamNum",
      "b5": "b2teamNum",
      "b6": "b3teamNum"
    }
  }
}
```

To add 2027 support, add `"2027s"` and `"2027d"` entries — no script edits needed.

---

## scouting_all_v2.py Changes from scouting_all_2026.py

`scouting_all_v2.py` is a copy of `scouting_all_2026.py` with five targeted changes. Everything else (logging, `validate_configuration`, `get_database`, MongoDB save loop, replay file, colorama init) is identical.

### Change 1 — Load mappings at startup

In `main()`, immediately after `validate_configuration()`, load `mappings.json` using a `__file__`-relative path (same technique already used for the log file):

```python
script_dir = os.path.dirname(os.path.abspath(__file__))
mappings_path = os.path.join(script_dir, "mappings.json")
try:
    with open(mappings_path, encoding="utf-8") as f:
        all_mappings = json.load(f)
except FileNotFoundError:
    err_msg = f"ERROR: mappings.json not found at {mappings_path}"
    get_logger().error(err_msg)
    print(f"{Fore.RED}{err_msg}")
    sys.exit(2)
except json.JSONDecodeError as e:
    err_msg = f"ERROR: mappings.json contains invalid JSON: {e}"
    get_logger().error(err_msg)
    print(f"{Fore.RED}{err_msg}")
    sys.exit(2)
```

### Change 2 — Validate year mapping after event code entry

In the event code loop, after accepting a code that starts with `'2'`, check both year entries exist before breaking:

```python
year = eventCode[:4]
match_key = f"{year}s"
defense_key = f"{year}d"

if match_key not in all_mappings or defense_key not in all_mappings:
    missing = [k for k in (match_key, defense_key) if k not in all_mappings]
    err_msg = (
        f"ERROR: No mapping found for {', '.join(missing)} in mappings.json. "
        f"Add the missing entries and restart the script."
    )
    get_logger().error(err_msg)
    print(f"{Fore.RED}{err_msg}")
    continue  # loop back to event code prompt

break
```

### Change 3 — inflate_match_data accepts mapping as parameters

Replace the hardcoded `key_mapping` dict inside `inflate_match_data` with parameters:

```python
def inflate_match_data(
    matchData: Dict,
    key_mapping: Dict[str, str],
    total_game_pieces_fields: List[str],
) -> Optional[Dict]:
```

Replace `matchData["totalGamePieces"] = matchData["autoHub"] + matchData["teleHub"]` with:

```python
matchData["totalGamePieces"] = sum(matchData[f] for f in total_game_pieces_fields)
```

### Change 4 — inflate_defense_data accepts mapping as parameter

Replace the hardcoded `key_mapping` dict inside `inflate_defense_data` with a parameter:

```python
def inflate_defense_data(
    matchData: Dict,
    key_mapping: Dict[str, str],
) -> Optional[Dict]:
```

### Change 5 — Call sites pass mapping from loaded data

Before the scan loop (after the event code is accepted), extract the year-specific mappings:

```python
match_mapping = all_mappings[match_key]
defense_mapping = all_mappings[defense_key]
```

At the dispatch points inside the scan loop:

```python
# mo == "s"
inflated = inflate_match_data(
    matchData,
    match_mapping["key_mapping"],
    match_mapping["total_game_pieces_fields"],
)

# mo == "d"
inflated = inflate_defense_data(matchData, defense_mapping["key_mapping"])
```

---

## RandomData2026_v2.py Fix

Single change to the `matchResults` f-string (line ~228): add `"mo":"s"` as the first key.

```python
# Before
matchResults = (
    f'"key":{a_Teams[team][TEAMNUM]},"mn":{matchNum},"cl":"qm","i":"Python",'
    ...
)

# After
matchResults = (
    f'"mo":"s","key":{a_Teams[team][TEAMNUM]},"mn":{matchNum},"cl":"qm","i":"Python",'
    ...
)
```

Output becomes: `{"mo":"s","key":6413,"mn":1,"cl":"qm",...}`

---

## Supporting File Updates

### ScoutingMatchScan.bat

Change the `python` argument from `scouting_all_2026.py` to `scouting_all_v2.py`:

```bat
@echo off
cd /d "%~dp0"
echo Scanning scouting data...
uv run --package frc-6413-scouting-scripts python Scouting-Scripts\scouting_all_v2.py
```

### UV_SCRIPTS.md

In the Scouting-Scripts table, update the "Match & Defense Scouting" command:

```
| Match & Defense Scouting | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_all_v2.py` |
```

### README.md

Update the `uv run` example that references `scouting_all_2026.py` to `scouting_all_v2.py`.

---

## Error Handling Summary

| Scenario | Behavior |
|----------|----------|
| `mappings.json` not found | Print error, `sys.exit(2)` |
| `mappings.json` invalid JSON | Print error, `sys.exit(2)` |
| Year mapping missing (e.g., `2027s`) | Print which keys are missing, loop back to event code prompt |
| Missing QR key during inflation | Unchanged from `scouting_all_2026.py` — print error, return `None`, skip record |

---

## What Does NOT Change

- `scouting_all_2026.py` — kept as-is, not modified
- MongoDB save logic, upsert pattern, replay file, secondary DB handling
- `validate_configuration()`, `get_database()`, logging setup
- All behavior for unknown `mo` values, JSON parse errors, MongoDB failures
