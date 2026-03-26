# Running Python Scripts with uv

This project uses uv for fast Python package management and script execution.

## Initial Setup (one-time)

```bash
# Install uv if not already installed
pip install uv

# Sync dependencies (from repo root)
# Windows (required - linking doesn't work on Windows)
uv sync --link-mode=copy

# Mac/Linux (can use default linking)
uv sync
```

## Running Scripts

### Scouting-Scripts

All scripts are run from the **repo root** using `uv run --package <package-name> <script>`

| Script | Command |
|--------|---------|
| Match Scouting | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_2025.py` |
| Defense Scouting | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/defense_scouting_2025.py` |
| Training Check | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/training_checking_2025.py` |
| Training Collection | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/training_collection_2025.py` |
| Pre-scouting Template | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/prescouting_make_template.py` |
| Pre-scouting Upload | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/prescouting_upload.py` |
| File to MongoDB | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/file_to_MongoDB_v1.py` |
| Find Missing Data | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/find_missing_data.py` |
| Schema Migration | `uv run --package frc-6413-scouting-scripts python Scouting-Scripts/2025_v7_to_v8.py` |

**Or use the batch files (Windows):**
- `Scouting Match v8 Scan.bat` - Match scouting
- `Scouting Defense v3 Scan.bat` - Defense scouting

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
| Get Event Matches (2025) | `uv run --package frc-6413-scouting-tools python Tools/get_event_matches_2025_v2.py` |
| Get Event List of Teams | `uv run --package frc-6413-scouting-tools python Tools/get_event_list_of_teams_2025_v1.py` |
| Get Event Teams Simple | `uv run --package frc-6413-scouting-tools python Tools/get_event_teams_simple_2025_v1.py` |
| Get Event Schedule from MongoDB | `uv run --package frc-6413-scouting-tools python Tools/get_event_schedule_from_mongodb_2025_v1.py` |
| MongoDB to MongoDB | `uv run --package frc-6413-scouting-tools python Tools/MongoDB_to_MongoDB_v1.py` |
| Random Data Generator | `uv run --package frc-6413-scouting-tools python Tools/RandomData2026A.py` |
| Get Event Matches (2022) | `uv run --package frc-6413-scouting-tools python Tools/get_event_matches_2022_v2.py` |

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
uv run ruff check Scouting-Scripts/scouting_2026.py
uv run ruff format Scouting-Scripts/scouting_2026.py
```

## Quick Reference

- Always run from **repo root**
- Use `uv run --package <package-name>` to activate the correct environment
- After the first `uv sync`, scripts start immediately (no activation needed)
- Common dependencies are deduplicated across packages automatically

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