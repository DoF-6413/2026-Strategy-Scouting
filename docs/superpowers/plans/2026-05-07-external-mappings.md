# External Key Mappings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `RandomData2026_v2.py` to emit the `"mo":"s"` routing key, then create `mappings.json` and `scouting_all_v2.py` so the scouting script is year-agnostic and requires no code edits when the FRC game changes.

**Architecture:** QR compact-to-full key mappings move from hardcoded dicts inside the inflate functions into `Scouting-Scripts/mappings.json`, keyed by `{year}s` / `{year}d`. `scouting_all_v2.py` loads the file once at startup, validates that both year entries exist after the event code is entered, then passes the mapping as parameters to the inflate functions.

**Tech Stack:** Python 3.11+, JSON stdlib, uv workspace monorepo, ruff

---

## File Map

| Action | Path |
|--------|------|
| Modify | `Tools/RandomData2026_v2.py` |
| Create | `Scouting-Scripts/mappings.json` |
| Create | `Scouting-Scripts/scouting_all_v2.py` |
| Keep   | `Scouting-Scripts/scouting_all_2026.py` (not touched) |
| Modify | `ScoutingMatchScan.bat` |
| Modify | `UV_SCRIPTS.md` |
| Modify | `README.md` |

---

## Context for the implementer

This repo is an FRC robotics scouting system (Team 6413). Scripts are run from the repo root via `uv run --package <pkg> python <path>`. There is no pytest suite; verification is done with manual smoke tests using piped stdin. All Python changes must pass `uv run ruff check` with zero output.

`scouting_all_2026.py` is the combined match + defense scouting script from the previous implementation. `scouting_all_v2.py` is a copy of it with five targeted changes — every other function, the logging setup, MongoDB save loop, and replay file logic are **identical** and must not be changed.

Run all commands from the repo root (`D:\Shred\2026-Strategy-Scouting` or wherever the repo lives).

---

## Task 1: Fix RandomData2026_v2.py

**Files:**
- Modify: `Tools/RandomData2026_v2.py` (line ~228)

The script generates fake match scouting data. It currently omits the `"mo":"s"` routing key that `scouting_all_v2.py` (and `scouting_all_2026.py`) require. Without it, piping random data into the scanner script produces `"ERROR: QR code is missing the 'mo' mode key"` for every record.

- [ ] **Step 1: Edit the matchResults f-string**

In `Tools/RandomData2026_v2.py`, find the `matchResults` assignment (around line 228). It currently starts:

```python
        matchResults = (
            f'"key":{a_Teams[team][TEAMNUM]},"mn":{matchNum},"cl":"qm","i":"Python",'
```

Replace just the first line of the f-string to prepend `"mo":"s"`:

```python
        matchResults = (
            f'"mo":"s","key":{a_Teams[team][TEAMNUM]},"mn":{matchNum},"cl":"qm","i":"Python",'
```

The remaining three lines of the f-string are unchanged:

```python
            f'"a1":{autoHub},"a2":{autoHubMiss},'
            f'"t1":{a_Teams[team][HUB]},"t2":{a_Teams[team][HUBMISS]},'
            f'"ns":0,"d":0,"r":{teleRelay},"h":{teleHerd},'
            f'"co":"{comments}"'
            )
```

- [ ] **Step 2: Verify output starts with `"mo":"s"`**

```bash
uv run --package frc-6413-scouting-tools python Tools/RandomData2026_v2.py | head -1
```

Expected output (values will vary):
```
{"mo":"s","key":60,"mn":1,"cl":"qm","i":"Python","a1":3,...}
```

- [ ] **Step 3: Run ruff**

```bash
uv run ruff check Tools/RandomData2026_v2.py
```

Expected: no output (zero issues).

- [ ] **Step 4: Commit**

```bash
git add Tools/RandomData2026_v2.py
git commit -m "Add mo:s routing key to RandomData2026_v2.py output"
```

---

## Task 2: Create mappings.json

**Files:**
- Create: `Scouting-Scripts/mappings.json`

This file holds all compact→full QR key mappings keyed by `{year}s` (match) and `{year}d` (defense). Match entries include `total_game_pieces_fields` (a list of inflated field names to sum). Defense entries have only `key_mapping`.

- [ ] **Step 1: Create the file**

Create `Scouting-Scripts/mappings.json` with this exact content:

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

- [ ] **Step 2: Validate the JSON is well-formed**

```bash
python -c "import json; json.load(open('Scouting-Scripts/mappings.json')); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add Scouting-Scripts/mappings.json
git commit -m "Add mappings.json with 2026 match and defense key mappings"
```

---

## Task 3: Create scouting_all_v2.py

**Files:**
- Create: `Scouting-Scripts/scouting_all_v2.py` (copied from `scouting_all_2026.py`, then modified)

Five targeted changes from the original. Everything else is identical — do not touch `setup_logger`, `get_logger`, `check_config_params`, `is_V5_configuration_bad`, `validate_configuration`, `get_database`, or the MongoDB save / replay file logic.

- [ ] **Step 1: Copy the source file**

```bash
cp Scouting-Scripts/scouting_all_2026.py Scouting-Scripts/scouting_all_v2.py
```

- [ ] **Step 2: Update the header comment**

In `Scouting-Scripts/scouting_all_v2.py`, replace the existing header comment (lines 1–14) with:

```python
# This Python script will take scouting data from scanned QR codes (as JSON)
# and then do any touch up and data checking before putting it into a MongoDB
# database or two.
#
# This script combines match and defense scouting into a single entry point.
# A "mo" key in the QR code JSON determines which inflate path to use:
#
#   mo = "s"  ->  match scouting
#   mo = "d"  ->  defense scouting
#   mo absent ->  invalid; data is rejected and not saved
#
# Key mappings are loaded from mappings.json (same directory as this script),
# keyed by {year}s and {year}d (e.g., "2026s", "2026d").  To support a new
# game year, add the new entries to mappings.json — no script edits needed.
#
# The "mo" key is stripped from the data before inflation and is never written
# to MongoDB.
```

- [ ] **Step 3: Apply Change 1 — load mappings.json at startup**

In `main()`, locate this line:

```python
    validate_configuration()
```

After it (before the `replayFile =` line), insert:

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

- [ ] **Step 4: Apply Change 2 — replace the event code loop**

In `main()`, find and replace the entire existing event code `while True` loop:

**Old (the entire loop):**
```python
    while True:
        eventCode = input(
            "Enter the event code for the event you are scouting (or 'quit' to exit): "
        ).strip()

        if eventCode.lower() == "quit":
            get_logger().info("The session was aborted at the event code prompt")
            sys.exit(0)

        # Make sure we get an event code that begins with a '2'
        if eventCode.startswith("2"):
            break

        print("\n\nHEY!  That is not a valid event code!  Try again...\n")
```

**New:**
```python
    while True:
        eventCode = input(
            "Enter the event code for the event you are scouting (or 'quit' to exit): "
        ).strip()

        if eventCode.lower() == "quit":
            get_logger().info("The session was aborted at the event code prompt")
            sys.exit(0)

        if not eventCode.startswith("2"):
            print("\n\nHEY!  That is not a valid event code!  Try again...\n")
            continue

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
            continue

        break
```

- [ ] **Step 5: Apply Change 2 continued — add mapping extraction after the loop**

Find this line (right after the event code loop):

```python
    get_logger().info(f"The event code for this session is {eventCode}")
```

After it, insert:

```python
    match_mapping = all_mappings[match_key]
    defense_mapping = all_mappings[defense_key]
```

- [ ] **Step 6: Apply Change 3 — replace inflate_match_data**

Find the entire `inflate_match_data` function and replace it with:

```python
###############################################################################
###############################################################################
def inflate_match_data(
    matchData: Dict,
    key_mapping: Dict[str, str],
    total_game_pieces_fields: List[str],
) -> Optional[Dict]:
    """
    "Inflate" the compact match scouting JSON keys to their full names and
    compute derived fields.

    Parameters:
        matchData: Already-parsed dict with "mo" already popped off.
        key_mapping: Compact-to-full key name mapping for this game year.
        total_game_pieces_fields: Field names to sum for totalGamePieces.

    Returns:
        The inflated dict, or None if any expected key was missing.
    """
    logger = get_logger()

    for short_key, long_key in key_mapping.items():
        if short_key in matchData:
            matchData[long_key] = matchData.pop(short_key)
        else:
            err_msg: str = f"QR code key {short_key} was NOT found!"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            return None

    comments = matchData["comments"]
    matchData["comments"] = re.sub(r"\s+", " ", comments.replace("\n", " ")).strip()

    matchData["docType"] = cfg.DT_SCOUTING_MATCH
    matchData["team"] = str(matchData["key"])
    matchData["totalGamePieces"] = sum(matchData[f] for f in total_game_pieces_fields)

    id_to_use = (
        f"{eventCode}_{matchData['compLevel']}{matchData['matchNumber']}_frc{matchData['team']}"
    )
    matchData["_id"] = id_to_use

    return matchData
```

- [ ] **Step 7: Apply Change 4 — replace inflate_defense_data**

Find the entire `inflate_defense_data` function and replace it with:

```python
###############################################################################
###############################################################################
def inflate_defense_data(
    matchData: Dict,
    key_mapping: Dict[str, str],
) -> Optional[Dict]:
    """
    "Inflate" the compact defense scouting JSON keys to their full names.

    Parameters:
        matchData: Already-parsed dict with "mo" already popped off.
        key_mapping: Compact-to-full key name mapping for this game year.

    Returns:
        The inflated dict, or None if any expected key was missing.
        NOTE: _id is NOT generated here; it is generated per-team in the save loop.
    """
    logger = get_logger()

    for short_key, long_key in key_mapping.items():
        if short_key in matchData:
            matchData[long_key] = matchData.pop(short_key)
        else:
            err_msg: str = f"QR code key {short_key} was NOT found!"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            return None

    matchData["docType"] = cfg.DT_SCOUTING_MATCH

    return matchData
```

- [ ] **Step 8: Apply Change 5 — update inflate dispatch calls in the scan loop**

In `main()`, inside the scan loop, find:

```python
        # Step 3: Dispatch to the correct inflate function
        if mo == "s":
            inflated = inflate_match_data(matchData)
        elif mo == "d":
            inflated = inflate_defense_data(matchData)
```

Replace with:

```python
        # Step 3: Dispatch to the correct inflate function
        if mo == "s":
            inflated = inflate_match_data(
                matchData,
                match_mapping["key_mapping"],
                match_mapping["total_game_pieces_fields"],
            )
        elif mo == "d":
            inflated = inflate_defense_data(matchData, defense_mapping["key_mapping"])
```

- [ ] **Step 9: Run ruff check**

```bash
uv run ruff check Scouting-Scripts/scouting_all_v2.py
```

Expected: no output (zero issues). Fix any issues before continuing.

- [ ] **Step 10: Run ruff format**

```bash
uv run ruff format Scouting-Scripts/scouting_all_v2.py
```

Then re-run check to confirm still clean:

```bash
uv run ruff check Scouting-Scripts/scouting_all_v2.py
```

Expected: no output.

- [ ] **Step 11: Smoke test — missing year mapping**

Pipe two inputs: a valid-format event code for a year with no mapping (`2027test`), then `quit`. This tests the new mapping validation without needing MongoDB.

```bash
printf '2027test\nquit\n' | uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_all_v2.py
```

Expected output (exact wording):
```
The data log for this session is ScoutingAll_<timestamp>.data
Enter the event code for the event you are scouting (or 'quit' to exit): ERROR: No mapping found for 2027s, 2027d in mappings.json. Add the missing entries and restart the script.
Enter the event code for the event you are scouting (or 'quit' to exit): 
```

The script exits cleanly (exit code 0) after `quit`.

- [ ] **Step 12: Commit**

```bash
git add Scouting-Scripts/scouting_all_v2.py
git commit -m "Add scouting_all_v2.py with externalized key mappings"
```

---

## Task 4: Update supporting files

**Files:**
- Modify: `ScoutingMatchScan.bat` (line 4)
- Modify: `UV_SCRIPTS.md` (line 53)
- Modify: `README.md` (line 195)

- [ ] **Step 1: Update ScoutingMatchScan.bat**

In `ScoutingMatchScan.bat`, line 4 currently reads:

```bat
uv run --package frc-6413-scouting-scripts python Scouting-Scripts\scouting_all_2026.py
```

Replace with:

```bat
uv run --package frc-6413-scouting-scripts python Scouting-Scripts\scouting_all_v2.py
```

- [ ] **Step 2: Update UV_SCRIPTS.md**

In `UV_SCRIPTS.md`, line 53 currently reads:

```
| Match & Defense Scouting | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_all_2026.py` |
```

Replace `scouting_all_2026.py` with `scouting_all_v2.py`:

```
| Match & Defense Scouting | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_all_v2.py` |
```

- [ ] **Step 3: Update README.md**

In `README.md`, line 195 currently reads:

```
**uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_all_2026.py**
```

Replace `scouting_all_2026.py` with `scouting_all_v2.py`:

```
**uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_all_v2.py**
```

- [ ] **Step 4: Verify no remaining references to scouting_all_2026 in user-facing docs**

```bash
grep -r "scouting_all_2026" README.md UV_SCRIPTS.md ScoutingMatchScan.bat
```

Expected: no output (all references updated). References remaining in `docs/superpowers/` and the old script file itself are fine — do not change those.

- [ ] **Step 5: Commit**

```bash
git add ScoutingMatchScan.bat UV_SCRIPTS.md README.md
git commit -m "Update docs and BAT file to reference scouting_all_v2.py"
```
