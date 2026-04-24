# Centralize config.py and credentials.py into a Shared Workspace Package

**Date:** 2026-04-22
**Branch:** `one_config`
**Status:** Approved design, pending implementation plan

## Problem

The repo currently has three near-duplicate `config.py` files and three drifted `credentials.py` files, one in each Python package:

- `Scouting-Scripts/config.py` and `Tools/config.py` are byte-identical copies of the V5 schema constants.
- `Strategy-Dashboard/config.py` contains a partial copy of the same V5 schema constants (with one local rename, `V5_COL_MATCHES` instead of `V5_COL_MATCH`) plus a large body of dashboard-only UI configuration (colors, stat mappings, page configs, climb/role labels, etc.).
- `Scouting-Scripts/credentials.py` defines `TBAAUTHKEY`; the other two `credentials.py` files and `credentials.py.example` use the newer `TBA_AUTH_KEY` name. Only one script (`Scouting-Scripts/prescouting_make_template.py`) still references the old name. A latent bug exists in `Scouting-Scripts/find_missing_data.py` which references `creds.TBA_AUTH_KEY` against a credentials file that defines only `TBAAUTHKEY`.

Maintaining three copies has caused drift (key naming, constant naming) and means a schema change has to be applied in three places.

## Goal

Consolidate the shared schema constants and credentials into a single source of truth, exposed as a uv workspace package that the other three packages depend on. Leave the Strategy-Dashboard's local `config.py` untouched in this work — its cleanup is a separate, planned piece of work on its own branch.

## Decisions (made during brainstorming)

1. **Content scope:** Only the constants that are actually shared move into the central file. Dashboard-only UI configuration stays in `Strategy-Dashboard/config.py`.
2. **Location:** A new uv workspace package `Common/` containing the importable Python package `frc_6413_common`.
3. **Migration scope:** All Python files outside `Strategy-Dashboard/` that currently import the local `config` or `credentials` get migrated. Old per-folder `config.py` / `credentials.py` / `credentials.py.example` files are deleted (except `Strategy-Dashboard/config.py`, which stays).
4. **Credential standardization:** The shared `credentials.py` defines `TBA_AUTH_KEY`. `Scouting-Scripts/prescouting_make_template.py:391` is updated to match.
5. **Strategy-Dashboard handling:** Zero edits to any Python source file under `Strategy-Dashboard/`. The single exception is `Strategy-Dashboard/pyproject.toml`, which gets the same workspace dependency line as the other consumer packages so the dashboard can resolve `frc-6413-common` once the future cleanup branch wires up the imports. The dashboard's local `config.py` keeps its full current content; the duplicate constants stay until the future cleanup branch (see Future Work).

## Architecture

### File layout (new)

```
Common/
├── pyproject.toml                  # Declares package "frc-6413-common"
├── credentials.py.example          # Committed; template for new users
└── frc_6413_common/
    ├── __init__.py                 # Empty / docstring only
    ├── config.py                   # Shared V5 schema constants
    └── credentials.py              # Gitignored; user-local
```

### Files removed (after import migration verified)

**Removed from git (tracked files):**
- `Scouting-Scripts/config.py`
- `Scouting-Scripts/credentials.py.example`
- `Tools/config.py`
- `Tools/credentials.py.example`
- `Strategy-Dashboard/credentials.py.example`

**Removed from each user's working copy only (gitignored — never tracked):**
- `Scouting-Scripts/credentials.py`
- `Tools/credentials.py`
- `Strategy-Dashboard/credentials.py`

The gitignored files are the user's local secrets. Removing them from the working copy is part of the per-machine migration chore (Risks section), not a git change.

### Files NOT touched

- `Strategy-Dashboard/config.py` — keeps its full current content, including the duplicated V5 schema constants. No edits, no TODO comment.
- All Strategy-Dashboard scripts (`utils.py`, `format_photos.py`, `pages/*.py`) — keep `import config as cfg` pointing at the local file.
- All `Scouting-App/` files — separate JS app, out of scope.

### `.gitignore`

No changes required. The existing bare-pattern line `credentials.py` matches files of that name at any depth, so `Common/frc_6413_common/credentials.py` is already excluded. The existing `*/credentials.py` line is technically redundant but is left alone.

## Content split

### Goes into `Common/frc_6413_common/config.py`

Verbatim copy of the current `Scouting-Scripts/config.py` (which is byte-identical to `Tools/config.py`), including all explanatory comments. Constants:

- `DB_NAME`
- `V5_COL_DATA`, `V5_COL_EVENTS`, `V5_COL_MATCH`, `V5_COL_SCHEDULE`, `V5_COL_SCOUTING`, `V5_COL_STATISTICS`, `V5_COL_TEAMS`, `V5_COL_TRAINING`
- `DT_EVENTS_EVENT`, `DT_EVENTS_DISTRICT`, `DT_EVENTS_TEAMS`
- `DT_SCOUTING_PIT`, `DT_SCOUTING_PRESCOUT`, `DT_SCOUTING_MATCH`
- `DT_STATISTICS_OPR`, `DT_STATISTICS_DPR`, `DT_STATISTICS_CCWM`, `DT_STATISTICS_EPA`
- `MATCHLEVEL_QUALIFIERS`, `MATCHLEVEL_QUARTERS`, `MATCHLEVEL_SEMIS`, `MATCHLEVEL_FINALS`
- `ALL_TEAMS`, `ALL_TEAMS_DETAILED`
- `PRESCOUTING_FIELDS`

### Goes into `Common/frc_6413_common/credentials.py`

Same content as the current `Tools/credentials.py` (keys: `TBA_AUTH_KEY`, `PRIMARY_CONNECTION_STRING`, `SECONDARY_CONNECTION_STRING`), with all the explanatory comments preserved.

### Goes into `Common/credentials.py.example`

Verbatim copy of the existing `Scouting-Scripts/credentials.py.example` (already canonical — uses `TBA_AUTH_KEY`).

### Stays in `Strategy-Dashboard/config.py` (untouched)

Everything currently in that file: the duplicated V5 schema subset (`DB_NAME`, `V5_COL_SCOUTING`, `V5_COL_EVENTS`, `V5_COL_SCHEDULE`, `V5_COL_MATCHES`, `DT_SCOUTING_PRESCOUT`, `DT_SCOUTING_MATCH`, `DT_EVENTS_TEAMS`) plus all the dashboard-only UI configuration (`DASHBOARD_MODE`, `COMP_LEVEL_KEY_TO_TEXT`, `DEFAULT_COMPARE_GRAPH_COLORS`, `TREND_SLOPE_MAPPING`, `SLOPE_COLOR_MAPPING`, `ROBOT_PHOTOS_*`, `SELECTABLE_STATS`, `SELECTABLE_ACCURACY_KEYS`, `STAT_KEY_TO_TEXT`, `STAT_COLOR_MAPPING`, `ALL_TEAMS_TABLE_KEYS`, `STAT_SELECTOR_DEFAULTS`, `STAT_SELECTOR_FALLBACK_DEFAULT`, `TEAM_SUMMARY_LINE_CHART_KEYS`, `TEAM_SUMMARY_TABLE_KEYS`, `CLIMB_KEY`, `CLIMB_INT_TO_TEXT`, `ROLE_KEY`, `ROLE_INT_TO_TEXT`).

### Naming-conflict note

The shared file's `V5_COL_MATCH = "matches"` and the dashboard's local `V5_COL_MATCHES = "matches"` resolve to the same string value, so even though the names differ, neither breaks anything as long as the dashboard keeps using its own `cfg.V5_COL_MATCHES`. The shared file does not need a `MATCHES` alias.

## Migration mechanics

### Per-script import-line edits

Mechanical change pattern — only import lines change; references to `cfg.X` and `creds.X` in the body of each script are unchanged:

| Before | After |
|---|---|
| `import config as cfg` | `from frc_6413_common import config as cfg` |
| `import credentials as creds` | `from frc_6413_common import credentials as creds` |
| `import config` (bare) | `from frc_6413_common import config` |

### One additional code edit

`Scouting-Scripts/prescouting_make_template.py:391` — change `creds.TBAAUTHKEY` → `creds.TBA_AUTH_KEY`. This standardizes the name and incidentally fixes the latent bug in `Scouting-Scripts/find_missing_data.py:220`, which already uses `creds.TBA_AUTH_KEY` but currently runs against a credentials file that only defines `TBAAUTHKEY`.

### Files to edit (16 total — Strategy-Dashboard files NOT included)

**`Scouting-Scripts/`:**
- `defense_scouting_2026.py`
- `file_to_MongoDB_v1.py`
- `find_missing_data.py`
- `prescouting_make_template.py` (import + the `TBAAUTHKEY` reference)
- `prescouting_upload.py`
- `scouting_2026.py`
- `training_checking_2026.py`
- `training_collection_2026.py`

**`Tools/`:**
- `get_event_list_of_teams_2025_v1.py`
- `get_event_matches_2022_v2.py`
- `get_event_matches_2025_v2.py`
- `get_event_matches_2026_v1.py`
- `get_event_schedule_from_mongodb_2025_v1.py`
- `get_event_teams_simple_2025_v1.py`
- `get_events_by_year_keys_2026_v1.py`
- `MongoDB_to_MongoDB_v1.py`

## Workspace wiring

### `Common/pyproject.toml` (new)

```toml
[project]
name = "frc-6413-common"
version = "2026.0.0"
description = "Shared configuration constants and credentials for FRC 6413 scripts"
requires-python = ">=3.11"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["frc_6413_common"]
```

### Root `pyproject.toml` change

```toml
[tool.uv.workspace]
members = ["Common", "Scouting-Scripts", "Strategy-Dashboard", "Tools"]
```

### Each consumer pyproject.toml (`Scouting-Scripts/`, `Strategy-Dashboard/`, `Tools/`)

Add `frc-6413-common` to dependencies and a `[tool.uv.sources]` entry that resolves it from the workspace:

```toml
[project]
dependencies = [
    "frc-6413-common",
    # ... existing entries unchanged
]

[tool.uv.sources]
frc-6413-common = { workspace = true }
```

The `Strategy-Dashboard/pyproject.toml` is updated *only* to declare this dependency. No dashboard source file uses the import in this work; the dependency exists so the dashboard cleanup branch can flip the switch in one line later.

### Build backend note

`hatchling` is used for `frc-6413-common` because it's the modern uv-friendly default. If `uv sync` ever surfaces a Windows-specific issue with hatchling, swapping to `setuptools` is a non-breaking alternative.

## Documentation updates (in scope)

### `UV_SCRIPTS.md`

1. New section near the top titled "**Setting up credentials**" explaining that each user copies `Common/credentials.py.example` to `Common/frc_6413_common/credentials.py` and fills in their TBA key + MongoDB connection strings.
2. The "Adding Dependencies" section gains a note that shared schema constants and credentials live in the `frc-6413-common` package and are imported as `from frc_6413_common import config, credentials`.

### `UV_SETUP_SUMMARY.md`

1. "New Files Created" gains an entry for `Common/pyproject.toml` describing the shared package.
2. The "Workspace Structure" diagram is updated to show the 4-member workspace and `Common/frc_6413_common/{config.py, credentials.py, credentials.py.example}`.
3. New short section: "**Shared Configuration**" — one paragraph explaining where shared constants live versus dashboard-specific ones.

### `CLAUDE.md`

The current line "Credentials (MongoDB connection strings, TBA API key) are in `credentials.py` files - keep these private" becomes stale once the per-folder files are gone. Update to point at the single `Common/frc_6413_common/credentials.py`. The "Key Configuration Files" section is also updated:

- `Scouting-Scripts/config.py` → `Common/frc_6413_common/config.py` (description: "V5 schema constants, collection names, docTypes")
- A line is added explaining that `Strategy-Dashboard/config.py` still exists and holds dashboard-only UI configuration plus a still-duplicated subset of schema constants (slated for cleanup on its own branch).

### `README.md`

Out of scope — owner will update if/when needed.

## Verification

Run before deleting any old files, and again after deletion:

1. `uv sync --link-mode=copy` from repo root.
2. `uv run ruff check .` — must pass with zero warnings about unresolved imports.
3. End-to-end smoke imports proving each consumer package can resolve the new shared package:
   - `uv run --package frc-6413-scouting-scripts python -c "from frc_6413_common import config, credentials; print(config.DB_NAME, credentials.TBA_AUTH_KEY[:6])"`
   - `uv run --package frc-6413-scouting-tools python -c "from frc_6413_common import config, credentials; print(config.DB_NAME, credentials.TBA_AUTH_KEY[:6])"`
   - `uv run --package frc-6413-strategy-dashboard python -c "from frc_6413_common import config, credentials; print(config.DB_NAME, credentials.TBA_AUTH_KEY[:6])"`
4. Spot-check one script per package by running it with `--help` or its first interactive prompt and confirming no `ImportError` / `AttributeError`.

## Risks and known gotchas

- **Per-machine credentials migration:** every user (Bruce, scouts, etc.) must manually copy their existing `Scouting-Scripts/credentials.py` (or `Tools/credentials.py`) values into the new `Common/frc_6413_common/credentials.py` before scripts will run. This is a one-time chore per machine; the doc updates above call it out.
- **Stale `__pycache__`:** existing `__pycache__` directories in `Scouting-Scripts/`, `Tools/`, `Strategy-Dashboard/` will contain compiled copies of the old `config.py` / `credentials.py`. These are harmless (Python ignores `.pyc` files whose source is gone) but a one-time cleanup pass is included in the verification step.
- **Dashboard divergence window:** between this PR landing and the dashboard cleanup, `Strategy-Dashboard/config.py` is the canonical source for the dashboard's schema constants. Any change to a constant in `Common/frc_6413_common/config.py` (e.g., renaming a collection) has to be mirrored manually in the dashboard's local file until the cleanup. This is a known, time-boxed cost.
- **Build backend choice:** `hatchling` is the default; `setuptools` is the fallback if uv on Windows ever complains.

## Future work (separate dashboard cleanup branch — NOT this PR)

Captured here as a note to future self.

1. In `Strategy-Dashboard/config.py`, replace the duplicated V5 schema-constant block with a single line at the top of the file:
   ```python
   from frc_6413_common.config import *
   ```
   This makes the shared file the source of truth and removes the duplication.
2. Decide on the `V5_COL_MATCHES` vs `V5_COL_MATCH` naming. Either rename across the dashboard codebase, or keep an alias in the local file (`V5_COL_MATCHES = V5_COL_MATCH`) to avoid touching every dashboard page.
3. Audit dashboard-only constants in `Strategy-Dashboard/config.py` for the 2026-game cleanup already noted in the project memory (stat keys, climb/role text, etc. — many are still 2025-shaped).
4. No dashboard import lines need to change. `import config as cfg` keeps working because the local file re-exports everything via `from frc_6413_common.config import *`.
