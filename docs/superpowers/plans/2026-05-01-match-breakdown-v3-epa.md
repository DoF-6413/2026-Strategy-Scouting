# Match Breakdown v3 — Statbotics EPA Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `Tools/get_match_breakdown_2026_v3.py` which shows each team's Statbotics `norm_epa['current']` value (e.g. `6413 (EPA: 1847.3)`) next to their number in the match breakdown output.

**Architecture:** Add `statbotics` as a Tools dependency, add a `get_epa()` fetcher and `epa_suffix()` formatter, build an `epa_map` dict in `main()` mirroring the existing `prescout_map` pattern, then pass it into both print functions. If a fetch fails for any reason, `(EPA: N/A)` is shown.

**Tech Stack:** Python 3.11+, statbotics, colorama, pymongo, uv (package manager)

---

## File Map

| File | Change |
|------|--------|
| `Tools/pyproject.toml` | Add `statbotics` dependency |
| `Tools/get_match_breakdown_2026_v3.py` | New file — copy of v2 plus all EPA additions |
| `UV_SCRIPTS.md` | Add v3 row to the Tools table |

---

### Task 1: Add statbotics dependency

**Files:**
- Modify: `Tools/pyproject.toml`

- [ ] **Step 1: Add the dependency via uv**

Run from the repo root:

```bash
uv add --package frc-6413-scouting-tools statbotics
```

Expected output: lines showing `Resolved`, `Prepared`, and `Installed statbotics-...`. This automatically edits `Tools/pyproject.toml` and `uv.lock`.

- [ ] **Step 2: Re-sync on Windows**

```bash
uv sync --link-mode=copy
```

Expected: no errors; statbotics appears in the installed packages list.

- [ ] **Step 3: Verify import works**

```bash
uv run --package frc-6413-scouting-tools python -c "import statbotics; print('ok')"
```

Expected output:
```
ok
```

- [ ] **Step 4: Commit**

```bash
git add Tools/pyproject.toml uv.lock
git commit -m "feat: add statbotics dependency to Tools package"
```

---

### Task 2: Create v3 file with get_epa() and epa_suffix()

**Files:**
- Create: `Tools/get_match_breakdown_2026_v3.py`

- [ ] **Step 1: Copy v2 to v3**

```bash
cp Tools/get_match_breakdown_2026_v2.py Tools/get_match_breakdown_2026_v3.py
```

- [ ] **Step 2: Update the header comment**

Replace the first comment block at the top of `Tools/get_match_breakdown_2026_v3.py`:

Old:
```python
# A Python script that retrieves alliance and opponent pre-scouting notes
# from MongoDB for a specific match, giving the strategy team a quick
# breakdown before a match. Defaults team to frc6413 when not specified.
#
# Usage:
#   uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v2.py
#   uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v2.py \
#       -e 2026nvlv -m qm5
```

New:
```python
# A Python script that retrieves alliance and opponent pre-scouting notes
# from MongoDB for a specific match, giving the strategy team a quick
# breakdown before a match. Defaults team to frc6413 when not specified.
# Shows each team's Statbotics norm_epa['current'] value next to their number.
#
# Usage:
#   uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v3.py
#   uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v3.py \
#       -e 2026nvlv -m qm5
```

- [ ] **Step 3: Add statbotics import**

In `Tools/get_match_breakdown_2026_v3.py`, find the imports block:

```python
import argparse
import logging
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple
```

Replace with:

```python
import argparse
import logging
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import statbotics
```

- [ ] **Step 4: Add get_epa() and epa_suffix() functions**

Insert the two new functions after the `get_logger()` function (after line ~58) and before `check_config_params()`. Add the separator block and both functions:

```python
###############################################################################
###############################################################################
def get_epa(team_number: int) -> Optional[float]:
    """
    Fetch the current norm_epa value for a team from Statbotics.
    Returns None on any failure (API down, team not found, missing field).
    """
    logger: logging.Logger = get_logger()
    try:
        sb = statbotics.Statbotics()
        team_data = sb.get_team(team_number)
        return float(team_data["norm_epa"]["current"])
    except Exception as e:
        logger.warning(f"Could not fetch EPA for team {team_number}: {e}")
        return None


###############################################################################
###############################################################################
def epa_suffix(epa: Optional[float]) -> str:
    """
    Format an EPA value as ' (EPA: 1847.3)' or ' (EPA: N/A)' when None.
    """
    if epa is None:
        return " (EPA: N/A)"
    return f" (EPA: {epa:.1f})"


```

- [ ] **Step 5: Manually verify get_epa() works**

```bash
uv run --package frc-6413-scouting-tools python -c "
import statbotics
sb = statbotics.Statbotics()
d = sb.get_team(254)
print(d['norm_epa']['current'])
"
```

Expected: a float number printed (e.g. `2015.0`). Any number confirms the API and field path are correct.

- [ ] **Step 6: Commit**

```bash
git add Tools/get_match_breakdown_2026_v3.py
git commit -m "feat: add get_epa and epa_suffix to match breakdown v3"
```

---

### Task 3: Update print_alliance_block() and print_opponent_block()

**Files:**
- Modify: `Tools/get_match_breakdown_2026_v3.py`

- [ ] **Step 1: Replace print_alliance_block()**

Find and replace the entire `print_alliance_block` function:

Old:
```python
def print_alliance_block(
    team_key: str,
    partners: List[str],
    prescout_map: Dict[str, Optional[Dict[str, str]]],
) -> None:
    """
    Print Strengths for the queried team and its partners.
    Shows "No data" in yellow if the team has no prescout document or
    if the Strengths field is empty.
    """
    print(f"{Fore.BLUE}Our alliance:{Style.RESET_ALL}\n")

    for tk in [team_key] + partners:
        display_num: str = tk[3:]  # strip 'frc'
        print(f"{Fore.BLUE}{display_num}{Style.RESET_ALL}")

        notes = prescout_map.get(tk)
        if notes is None:
            print(f"  {Fore.YELLOW}No data{Style.RESET_ALL}")
        else:
            strengths: str = notes.get("Strengths", "").strip()
            if strengths:
                print(f"  {strengths}")
            else:
                print(f"  {Fore.YELLOW}No data{Style.RESET_ALL}")
        print()
```

New:
```python
def print_alliance_block(
    team_key: str,
    partners: List[str],
    prescout_map: Dict[str, Optional[Dict[str, str]]],
    epa_map: Dict[str, Optional[float]],
) -> None:
    """
    Print Strengths for the queried team and its partners.
    Shows "No data" in yellow if the team has no prescout document or
    if the Strengths field is empty.
    """
    print(f"{Fore.BLUE}Our alliance:{Style.RESET_ALL}\n")

    for tk in [team_key] + partners:
        display_num: str = tk[3:]  # strip 'frc'
        print(f"{Fore.BLUE}{display_num}{epa_suffix(epa_map.get(tk))}{Style.RESET_ALL}")

        notes = prescout_map.get(tk)
        if notes is None:
            print(f"  {Fore.YELLOW}No data{Style.RESET_ALL}")
        else:
            strengths: str = notes.get("Strengths", "").strip()
            if strengths:
                print(f"  {strengths}")
            else:
                print(f"  {Fore.YELLOW}No data{Style.RESET_ALL}")
        print()
```

- [ ] **Step 2: Replace print_opponent_block()**

Find and replace the entire `print_opponent_block` function:

Old:
```python
def print_opponent_block(
    opponents: List[str],
    prescout_map: Dict[str, Optional[Dict[str, str]]],
) -> None:
    """
    Print Weaknesses and Observations for each opponent.
    Fields with no text are silently skipped — no label, no placeholder.
    "No data" is only shown when the team has no prescout document at all,
    or when both Weaknesses and Observations are absent or empty.
    """
    print(f"{Fore.RED}Opponents:{Style.RESET_ALL}\n")

    for tk in opponents:
        display_num: str = tk[3:]  # strip 'frc'
        print(f"{Fore.RED}{display_num}{Style.RESET_ALL}")

        notes = prescout_map.get(tk)
        if notes is None:
            print(f"  {Fore.YELLOW}No data{Style.RESET_ALL}")
        else:
            weaknesses: str = notes.get("Weaknesses", "").strip()
            observations: str = notes.get("Observations", "").strip()

            if not weaknesses and not observations:
                print(f"  {Fore.YELLOW}No data{Style.RESET_ALL}")
            else:
                if weaknesses:
                    print(f"  {weaknesses}")
                if weaknesses and observations:
                    print()
                if observations:
                    print(f"  {observations}")
        print()
```

New:
```python
def print_opponent_block(
    opponents: List[str],
    prescout_map: Dict[str, Optional[Dict[str, str]]],
    epa_map: Dict[str, Optional[float]],
) -> None:
    """
    Print Weaknesses and Observations for each opponent.
    Fields with no text are silently skipped — no label, no placeholder.
    "No data" is only shown when the team has no prescout document at all,
    or when both Weaknesses and Observations are absent or empty.
    """
    print(f"{Fore.RED}Opponents:{Style.RESET_ALL}\n")

    for tk in opponents:
        display_num: str = tk[3:]  # strip 'frc'
        print(f"{Fore.RED}{display_num}{epa_suffix(epa_map.get(tk))}{Style.RESET_ALL}")

        notes = prescout_map.get(tk)
        if notes is None:
            print(f"  {Fore.YELLOW}No data{Style.RESET_ALL}")
        else:
            weaknesses: str = notes.get("Weaknesses", "").strip()
            observations: str = notes.get("Observations", "").strip()

            if not weaknesses and not observations:
                print(f"  {Fore.YELLOW}No data{Style.RESET_ALL}")
            else:
                if weaknesses:
                    print(f"  {weaknesses}")
                if weaknesses and observations:
                    print()
                if observations:
                    print(f"  {observations}")
        print()
```

- [ ] **Step 3: Commit**

```bash
git add Tools/get_match_breakdown_2026_v3.py
git commit -m "feat: update print functions to display EPA next to team numbers"
```

---

### Task 4: Update main() to build epa_map and pass it through

**Files:**
- Modify: `Tools/get_match_breakdown_2026_v3.py`

- [ ] **Step 1: Build epa_map after prescout_map**

In `main()`, find this block:

```python
    # Fetch prescout notes for all 6 teams (ours + 2 partners + 3 opponents)
    all_teams: List[str] = alliance_teams + opponent_teams
    prescout_map: Dict[str, Optional[Dict[str, str]]] = {
        tk: get_prescout(db, event_code, tk) for tk in all_teams
    }

    print_alliance_block(team_key, partners, prescout_map)
    print_opponent_block(opponent_teams, prescout_map)
```

Replace with:

```python
    # Fetch prescout notes for all 6 teams (ours + 2 partners + 3 opponents)
    all_teams: List[str] = alliance_teams + opponent_teams
    prescout_map: Dict[str, Optional[Dict[str, str]]] = {
        tk: get_prescout(db, event_code, tk) for tk in all_teams
    }

    # Fetch Statbotics EPA for all 6 teams
    epa_map: Dict[str, Optional[float]] = {
        tk: get_epa(int(tk[3:])) for tk in all_teams
    }

    print_alliance_block(team_key, partners, prescout_map, epa_map)
    print_opponent_block(opponent_teams, prescout_map, epa_map)
```

- [ ] **Step 2: Commit**

```bash
git add Tools/get_match_breakdown_2026_v3.py
git commit -m "feat: build epa_map in main and thread through print functions"
```

---

### Task 5: Lint, sanity-check, update UV_SCRIPTS.md, final commit

**Files:**
- Modify: `Tools/get_match_breakdown_2026_v3.py`
- Modify: `UV_SCRIPTS.md`

- [ ] **Step 1: Run ruff check**

```bash
uv run ruff check Tools/get_match_breakdown_2026_v3.py
```

Expected: no output (zero issues). If any issues are reported, fix them.

- [ ] **Step 2: Run ruff format**

```bash
uv run ruff format Tools/get_match_breakdown_2026_v3.py
```

Expected: `1 file left unchanged` (or it reformats — either is fine; just ensure the file is formatted).

- [ ] **Step 3: Sanity-check EPA fetch manually**

```bash
uv run --package frc-6413-scouting-tools python -c "
import sys
sys.path.insert(0, 'Tools')
# Inline the two new functions to verify them without MongoDB
import statbotics
from typing import Optional

def get_epa(team_number: int) -> Optional[float]:
    try:
        sb = statbotics.Statbotics()
        team_data = sb.get_team(team_number)
        return float(team_data['norm_epa']['current'])
    except Exception as e:
        print(f'  warning: {e}')
        return None

def epa_suffix(epa: Optional[float]) -> str:
    if epa is None:
        return ' (EPA: N/A)'
    return f' (EPA: {epa:.1f})'

for team in [254, 6413, 99999]:
    epa = get_epa(team)
    print(f'{team}{epa_suffix(epa)}')
"
```

Expected output (numbers will vary by season; 99999 should show N/A):
```
254 (EPA: 2015.0)
6413 (EPA: 987.6)
99999 (EPA: N/A)
```

- [ ] **Step 4: Update UV_SCRIPTS.md Tools table**

In `UV_SCRIPTS.md`, find the Tools table row for Match Breakdown:

```markdown
| Get Match Breakdown | `uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v1.py` |
```

Replace with:

```markdown
| Get Match Breakdown | `uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v2.py` |
| Get Match Breakdown (with EPA) | `uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v3.py` |
```

- [ ] **Step 5: Final commit**

```bash
git add Tools/get_match_breakdown_2026_v3.py UV_SCRIPTS.md
git commit -m "feat: add UV_SCRIPTS entry and finalize match breakdown v3 with EPA display"
```
