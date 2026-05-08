# Combined Scouting Script and HTML Mode Key

**Date:** 2026-05-07
**Branch:** `one_scouting_script`
**Status:** Approved design, pending implementation plan

## Problem

Two separate scripts (`scouting_2026_v2.py` and `defense_scouting_2026_v2.py`) and two separate HTML pages (`index.html` and `index-defense.html`) handle match and defense scouting respectively. Operators must launch the correct script for the correct scouting type. There is no mechanism in the QR code data itself to identify which type of scan it represents, so a misdirected scan would silently corrupt the database.

## Goal

1. Produce a single Python script (`scouting_all_2026.py`) that handles both match and defense scouting based on a new `mo` routing key embedded in every QR code.
2. Update `index.html` to emit `"mo":"s"` in every QR payload.
3. Update `index-defense.html` to emit `"mo":"d"` in every QR payload.
4. QR codes that contain no `mo` key are treated as invalid and are never saved.

The two existing `v2` scripts are left in place as reference; they are not deleted.

## Decisions

1. **Script location:** `Scouting-Scripts/scouting_all_2026.py`
2. **Routing key:** `mo` — value `"s"` for match scouting, `"d"` for defense scouting. Any other value or an absent key is rejected.
3. **`mo` in saved data:** Stripped before inflation. It is a routing key only and does not appear in MongoDB documents.
4. **Replay file:** Single combined file `ScoutingAll_YYYYMMDD_HHMMSS.data`. Only valid, successfully-inflated records are written.
5. **Logging:** File-based logger from `defense_scouting_2026_v2.py` (`setup_logger()` / `get_logger()` pattern). Every function that logs calls `logger = get_logger()` near its start.
6. **Credentials import:** `from frc_6413_common import credentials as creds` at module level (not inside functions — fixes the pattern from `defense_scouting_2026_v2.py`).
7. **Inflate structure:** Two separate functions (`inflate_match_data` and `inflate_defense_data`); the scan loop dispatches based on `mo`.
8. **`eventCode` global:** Retained as a module-level global so `inflate_match_data` can use it for `_id` generation (same as `scouting_2026_v2.py`).

## Architecture

### Files changed

| File | Change |
|---|---|
| `Scouting-Scripts/scouting_all_2026.py` | New file |
| `Scouting-App/index.html` | Add `"mo":"s"` as first field in QR data string |
| `Scouting-App/index-defense.html` | Add `"mo":"d"` as first field in QR data string |

### Files NOT changed

- `Scouting-Scripts/scouting_2026_v2.py` — kept as reference
- `Scouting-Scripts/defense_scouting_2026_v2.py` — kept as reference
- All other scripts, dashboard, config, BAT files

## `scouting_all_2026.py` detailed design

### Imports

```python
import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from colorama import Fore, init
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
from pymongo.collection import Collection
from pymongo.database import Database
from tqdm import tqdm
```

### Logging

```python
_logger: Optional[logging.Logger] = None

def setup_logger() -> logging.Logger: ...   # file-based, WARNING+, ScriptLog_YYYYMMDD_HHMMSS.log
def get_logger() -> logging.Logger: ...     # returns _logger, calls setup_logger() if needed
```

Every function that logs opens with `logger = get_logger()`.

### Configuration helpers (unchanged from originals)

- `check_config_params(cfg, params)` — returns `True` if any param is missing/empty
- `is_V5_configuration_bad()` — checks all V5 schema constants
- `validate_configuration()` — checks credentials + V5 schema, calls `sys.exit(2)` on failure
- `get_database(databaseURI, databaseName)` — connects with 15 s timeout, pings, returns `Database` or `None`

### `inflate_match_data(matchData: dict) -> Optional[dict]`

Receives an already-parsed dict with `mo` already popped.

Key mapping:

| Short | Long |
|---|---|
| cl | compLevel |
| mn | matchNumber |
| i | scouter |
| a1 | autoHub |
| a2 | autoHubMiss |
| t1 | teleHub |
| t2 | teleHubMiss |
| ns | noShow |
| r | relayed |
| h | herded |
| d | died |
| co | comments |

Post-inflation steps:
1. Clean `comments` (collapse whitespace, strip leading/trailing).
2. Set `docType = cfg.DT_SCOUTING_MATCH`.
3. Add `team = str(matchData["key"])`.
4. Calculate `totalGamePieces = autoHub + teleHub`.
5. Generate `_id = f"{eventCode}_{compLevel}{matchNumber}_frc{team}"`.

Returns inflated dict, or `None` if any expected key is missing (logs error per missing key).

### `inflate_defense_data(matchData: dict) -> Optional[dict]`

Receives an already-parsed dict with `mo` already popped.

Key mapping:

| Short | Long |
|---|---|
| cl | compLevel |
| mn | matchNumber |
| i | scouter |
| r1 | r1defense |
| r2 | r2defense |
| r3 | r3defense |
| r4 | r1teamNum |
| r5 | r2teamNum |
| r6 | r3teamNum |
| b1 | b1defense |
| b2 | b2defense |
| b3 | b3defense |
| b4 | b1teamNum |
| b5 | b2teamNum |
| b6 | b3teamNum |

Post-inflation steps:
1. Set `docType = cfg.DT_SCOUTING_MATCH`.

`_id` is NOT generated here — it is generated per-team in the save loop.

Returns inflated dict, or `None` if any expected key is missing (logs error per missing key).

### Scan loop (inside `main()`)

```
parse JSON
  → JSONDecodeError → log + print error, continue

read mo = matchData.get("mo")
  → absent → log + print "QR code is missing the 'mo' mode key. Data rejected.", continue
  → present → pop mo off matchData

dispatch on mo:
  "s" → inflate_match_data(matchData)
  "d" → inflate_defense_data(matchData)
  other → log + print f"Unknown mode '{mo}'. Data rejected.", continue

inflate returns None → continue (errors already logged inside inflate)

inflate returns dict:
  → append raw tabletData to replay file
  → save to DB (match path or defense path — see below)
```

### Save path — match (`mo="s"`)

```python
matchData["eventCode"] = eventCode
matchID = matchData["_id"]
scoutingCollection.update_one({"_id": matchID}, {"$set": matchData}, upsert=True)
if scoutingCollection2:
    scoutingCollection2.update_one({"_id": matchID}, {"$set": matchData}, upsert=True)
```

### Save path — defense (`mo="d"`)

```python
for team_prefix in tqdm(["r1", "r2", "r3", "b1", "b2", "b3"], desc="Processing Teams"):
    team_num = str(matchData[f"{team_prefix}teamNum"])
    id_to_use = f"{eventCode}_{matchData['compLevel']}{matchData['matchNumber']}_frc{team_num}"
    team_data = {
        "defense": matchData[f"{team_prefix}defense"],
        "defenseScouter": matchData["scouter"],
        "eventCode": eventCode,
        "docType": matchData["docType"],
    }
    scoutingCollection.update_one({"_id": id_to_use}, {"$set": team_data}, upsert=True)
    if scoutingCollection2:
        scoutingCollection2.update_one({"_id": id_to_use}, {"$set": team_data}, upsert=True)
```

### `main()` structure

1. `init(autoreset=True, convert=True)`
2. `validate_configuration()`
3. Construct `replayFile = f"ScoutingAll_{datetime.now().strftime('%Y%m%d_%H%M%S')}.data"`; log its name; print its name.
4. Event code prompt loop — must start with `'2'`; `'quit'` exits.
5. Connect primary DB via `get_database()`; exit with error on failure.
6. Get `scoutingCollection = db[cfg.V5_COL_SCOUTING]`.
7. If `creds.SECONDARY_CONNECTION_STRING`: connect secondary DB; exit on failure; get `scoutingCollection2`.
8. Scan loop as described above with prompt `"Scan a tablet now (or 'quit' to exit): "`.

## HTML changes

### `Scouting-App/index.html` — `updateQR()` data string

Insert `'"mo":"s"'` as the first field (before `"key"`):

```javascript
var data =
"{" +
'"mo":"s"' +
',"key":' + JSON.stringify(Number($("#input_t").val())) +
// ... rest of fields unchanged
```

### `Scouting-App/index-defense.html` — `updateQR()` data string

Insert `'"mo":"d"'` as the first field (before `"cl"`):

```javascript
var data =
"{" +
'"mo":"d"' +
',"cl":' + JSON.stringify(getLevel()) +
// ... rest of fields unchanged
```

## Verification

1. `uv run ruff check Scouting-Scripts/scouting_all_2026.py` — zero warnings.
2. `uv run ruff format Scouting-Scripts/scouting_all_2026.py` — no changes.
3. Smoke-test the script by pasting valid match JSON (with `"mo":"s"`) at the scan prompt and confirming a record appears in MongoDB.
4. Smoke-test with valid defense JSON (with `"mo":"d"`) and confirm six records upserted.
5. Smoke-test with JSON missing `mo` and confirm rejection message and no DB write.
6. Open both HTML pages; click "Get Code"; scan the resulting QR with a phone camera or decoder and confirm `"mo":"s"` / `"mo":"d"` appears in the payload.

## Notes

- The defense script's local `import credentials as creds` (inside functions) is not carried into the new script. The new script uses the shared-package import at module level throughout.
- The existing `v2` scripts are left as-is. They will still work for anyone who needs them until the team is comfortable with the combined script.
