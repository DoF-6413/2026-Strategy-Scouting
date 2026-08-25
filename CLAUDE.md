# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is FRC Team 6413 (Degrees of Freedom) scouting and strategy system for the 2026 season. The system consists of:

1. **Scouting-App**: A web-based HTML/JavaScript app for match scouting at events
2. **Scouting-Scripts**: Python scripts that collect scouting data via QR codes and store in MongoDB
3. **Strategy-Dashboard**: A Streamlit-based Python dashboard for visualizing and analyzing scouting data
4. **Tools**: Utility scripts for data generation and management

## Environment Setup

This project uses **uv** for fast Python package management (uv workspace monorepo):

```bash
# Install uv (once)
pip install uv

# Sync dependencies (from repo root)
# Windows (required - linking doesn't work on Windows)
uv sync --link-mode=copy

# Mac/Linux (can use default linking)
uv sync
```

The workspace contains three Python packages:
- `frc-6413-scouting-scripts` (Scouting-Scripts/)
- `frc-6413-strategy-dashboard` (Strategy-Dashboard/)
- `frc-6413-scouting-tools` (Tools/)

### Running Scripts with uv

All Python scripts are run from the **repo root** using `uv run --package <package-name>`:

```bash
# Match Scouting
uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_2025.py

# Defense Scouting
uv run --package frc-6413-scouting-scripts python Scouting-Scripts/defense_scouting_2025.py

# Strategy Dashboard
uv run --package frc-6413-strategy-dashboard streamlit run Strategy-Dashboard/main.py

# Tools scripts
uv run --package frc-6413-scouting-tools python Tools/get_event_matches_2025_v2.py
```

See `UV_SCRIPTS.md` for a complete list of all script commands.

### Windows Batch Files

Double-click any of these in the repo root:
- `Scouting Match v8 Scan.bat` - Match scouting
- `Scouting Defense v3 Scan.bat` - Defense scouting
- `Strategy Dashboard.bat` - Opens the dashboard

## Common Commands

### Run the Strategy Dashboard

```bash
# Using uv (recommended)
uv run --package frc-6413-strategy-dashboard streamlit run Strategy-Dashboard/main.py
```

Or on Windows, double-click `Strategy Dashboard.bat` in the repo root.

### Collect Scouting Data (QR Code Scanning)

```bash
# Using uv (recommended)
uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_2025.py
```

Or on Windows, double-click `Scouting Match v8 Scan.bat` in the repo root.

### Collect Defense Scouting Data

```bash
# Using uv (recommended)
uv run --package frc-6413-scouting-scripts python Scouting-Scripts/defense_scouting_2025.py
```

Or on Windows, double-click `Scouting Defense v3 Scan.bat` in the repo root.

### Run Tools Scripts

```bash
# Using uv (recommended)
uv run --package frc-6413-scouting-tools python Tools/get_event_matches_2025_v2.py
```

**Important**: All scripts must be run from the **repo root**. See `UV_SCRIPTS.md` for complete command reference.

## Code Quality

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. **Run Ruff on any Python file you modify.**

### Lint (check for issues)
```bash
uv run ruff check .
```

### Format (auto-format code)
```bash
uv run ruff format .
```

### Lint + auto-fix fixable issues
```bash
uv run ruff check --fix .
```

You can also scope to a single file or directory:
```bash
uv run ruff check Scouting-Scripts/scouting_2025.py
uv run ruff format Scouting-Scripts/scouting_2025.py
```

## Architecture

### Data Flow

1. **Scouting App**: Scouts fill out match data on tablet → QR code generated (compact JSON with shortened keys)
2. **QR Code Scanner**: Bluetooth scanner reads QR code → Python script parses JSON
3. **Data Processing**: Python script "inflates" short key names to full names, calculates derived stats
4. **Storage**: Data stored in MongoDB (local and/or remote Atlas cluster)

### V5 Database Schema

All data is stored in a single MongoDB database (`frc_data`) with multiple collections:

- `scouting` - All scouting data (match, prescout, pit), differentiated by `docType`
- `events` - Event and district information
- `matches` - Match data from TBA/FMS
- `schedule` - Match schedules
- `teams` - Team registration and historical data
- `training` - Scouter training data
- `statistics` - Calculated stats (OPR, DPR, CCWM, EPA)

Document types in `scouting` collection:
- `DT_SCOUTING_MATCH` - Match scouting data
- `DT_SCOUTING_PRESCOUT` - Pre-scouting data
- `DT_SCOUTING_PIT` - Pit scouting data

### Key Configuration Files

- `Common/frc_6413_common/config.py` - V5 schema constants, collection names, docTypes (shared by Scouting-Scripts, Tools, and the Strategy-Dashboard)
- `Common/frc_6413_common/credentials.py` - MongoDB connection strings, TBA API key (gitignored; copy from `Common/credentials.py.example`); also used by the Strategy-Dashboard, which no longer has its own local `credentials.py`
- `Scouting-App/config.js` - Event code for scouting app (edit `eventCode` field)
- `Strategy-Dashboard/config.py` - Dashboard-only UI configuration (visualization colors, stat mappings, page configs). Shared schema constants (DB/collection/docType names) are imported from `Common/frc_6413_common/config.py` rather than duplicated here.

### Script Versioning

Many scripts have version suffixes (e.g., `scouting_2025_v1.py`, `scouting_2025_v2.py`). Always use the highest version number (no suffix is typically the latest).

### Scouting App QR Code Key Mapping

The scouting app generates QR codes with compact keys that get "inflated" in Python:

| Short Key | Long Key |
|-----------|----------|
| cl | compLevel |
| mn | matchNumber |
| i | scouter |
| a1-a12 | autoL4, autoL4Miss, autoL3, autoL3Miss, ... |
| t1-t13 | teleL4, teleL4Miss, teleL3, ... climb |
| ns | noShow |
| c | card |
| d | died |
| r | role |
| co | comments |

See `scouting_2025.py:inflate_tablet_data()` for the complete mapping.

### TBA Event Codes

Event codes follow the pattern `{year}{state}{event}` (e.g., `2025azfg`, `2025mabos`).

### MongoDB Connection

Primary database: `frc_data` on localhost:27017 by default. Can be configured to use MongoDB Atlas for remote storage.

### Dashboard Pages

- **All Teams**: Compare all teams at event with box plots and tables
- **Team Summary**: Individual team summaries with line charts and tables
- **Match Schedule**: Full match schedule from TBA
- **Match Scouter**: Scout future matches for strategy formulation
- **Alliance Explorer**: Create speculative alliance scenarios
- **Niche Finder**: Find teams by niche capabilities (upper quartiles/maxs)

## Important Notes

- The repo is year-specific; a new repo is created each FRC season
- Credentials (MongoDB connection strings, TBA API key) are in `Common/frc_6413_common/credentials.py` - keep this file private (it is gitignored)
- Data log files (`ScoutingData_*.data`) are automatically generated during scanning sessions for replay
- When working with stats, the calculated fields (e.g., `totalCoral`, `totalCoralAccuracy`) are added during data collection, not stored raw
- Defense scouting uses a separate script (`defense_scouting_2025.py`) and HTML page (`index-defense.html`)