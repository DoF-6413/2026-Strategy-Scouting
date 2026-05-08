# Running Python Scripts with uv

This project uses uv for fast Python package management and script execution.

## Initial Setup (one-time)

It is **strongly** recommended that you install the uv tool following the standalone steps outlined in the official docs [here](https://docs.astral.sh/uv/getting-started/installation/).  This works best if you are not sure if you have Python already installed or it is an older Python version.

If you want to install uv using an existing Python installation then you can follow these steps:

```bash
# Install uv if not already installed
pip install uv

# Sync dependencies (from repo root)
# Windows (required - linking doesn't work on Windows)
uv sync --link-mode=copy

# Mac/Linux (can use default linking)
uv sync
```

## Setting up credentials (one-time, per machine)

The shared package needs your TBA API key and MongoDB connection string before any script can run. Copy the committed example file and edit your local copy:

```bash
cp Common/credentials.py.example Common/frc_6413_common/credentials.py
```

Then open `Common/frc_6413_common/credentials.py` and fill in:

- `TBA_AUTH_KEY` — your The Blue Alliance API key from <https://www.thebluealliance.com/account>
- `PRIMARY_CONNECTION_STRING` — `"mongodb://localhost:27017/"` for a local MongoDB, or your Atlas connection string

`Common/frc_6413_common/credentials.py` is gitignored and will **never** be committed.

## Quick Reference

- Always run any script from **repo root**
- Use `uv run --package <package-name>` to activate the correct environment
- After the first `uv sync`, scripts start immediately (no activation needed)
- Common dependencies are deduplicated across packages automatically

## Running Scripts

### Scouting-Scripts

All scripts are run from the **repo root** using `uv run --package <package-name> <script>`

| Script | Command |
|--------|---------|
| Match & Defense Scouting | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_all_2026.py` |
| Training Check | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/training_checking_2026_v2.py` |
| Training Collection | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/training_collection_2026_v2.py` |
| Pre-scouting Template | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/prescouting_make_template.py` |
| Pre-scouting Upload | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/prescouting_upload.py` |
| File to MongoDB | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/file_to_MongoDB_v1.py` |
| Find Missing Data | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/find_missing_data.py` |

**Or use the batch file (Windows):**
- `ScoutingMatchScan.bat` - Match and defense scouting

**NOTE:** Drag and drop the BATch files to your Desktop to easily launch the scripts without needing to open a command prompt first.  You can rename the BATch files to have spaces if you put them on your Desktop so they are more readable when sitting side by side.  Bonus points if you change the Desktop icons to make them different and visually distinct.

### Strategy-Dashboard

| Action | Command |
|--------|---------|
| Run Dashboard | `uv run --package frc-6413-strategy-dashboard streamlit run Strategy-Dashboard/main.py` |

**Or use the batch file (Windows):**
- `Strategy Dashboard.bat` - Opens the dashboard

### Tools

All Tools scripts are run from the **repo root**:

| Script | Command |
|--------|---------|
| Random Data Generator | `uv run --package frc-6413-scouting-tools python Tools/RandomData2026_v2.py` |
| MongoDB to MongoDB | `uv run --package frc-6413-scouting-tools python Tools/MongoDB_to_MongoDB_v1.py` |
| Get Event Matches (2026) | `uv run --package frc-6413-scouting-tools python Tools/get_event_matches_2026_v3.py` |
| Get Event List of Teams | `uv run --package frc-6413-scouting-tools python Tools/get_event_list_of_teams_2025_v1.py` |
| Get Event Teams Simple | `uv run --package frc-6413-scouting-tools python Tools/get_event_teams_simple_2025_v1.py` |
| Get Event Schedule from MongoDB | `uv run --package frc-6413-scouting-tools python Tools/get_event_schedule_from_mongodb_2026_v2.py` |
| Get Match Breakdown | `uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v2.py` |
| Get Match Breakdown (with EPA) | `uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v3.py` |

## Code Quality (Ruff)

Run from the **repo root**:

| Action | Command |
|--------|---------|
| Lint (check for issues) | `uv run ruff check .` |
| Format (auto-format code) | `uv run ruff format .` |
| Lint + auto-fix | `uv run ruff check --fix .` |
| Format dry-run | `uv run ruff format --check .` |

Scope to a single file:
```bash
uv run ruff check Scouting-Scripts/scouting_2026_v2.py
uv run ruff format Scouting-Scripts/scouting_2026_v2.py
```

## Adding Dependencies

To add a new dependency to a package:

```bash
# Add to Scouting-Scripts
uv add --package frc-6413-scouting-scripts <package-name>

# Add to Strategy-Dashboard
uv add --package frc-6413-strategy-dashboard <package-name>

# Add to Tools
uv add --package frc-6413-scouting-tools <package-name>
```

### Shared configuration constants

V5 schema constants (`DB_NAME`, `V5_COL_*`, `DT_*`, etc.) and credentials live in the `frc-6413-common` package and are imported as:

```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

To edit shared schema constants, edit `Common/frc_6413_common/config.py`. Dashboard-specific UI configuration (colors, stat mappings, page configs) lives in `Strategy-Dashboard/config.py` instead.