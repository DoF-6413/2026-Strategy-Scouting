# UV Workspace Migration Summary

## What Was Changed

### New Files Created

1. **`Common/pyproject.toml`** - Shared utilities package
   - Dependencies: none
   - Holds the `frc_6413_common` Python package with shared V5 schema constants and credentials
   - All other packages depend on this one as a workspace dependency

2. **Root `pyproject.toml`** - Workspace configuration
   - Defines the workspace with 3 member packages
   - Sets Python version requirement (>=3.11)
   - Includes optional `common` dependency group

3. **`Scouting-Scripts/pyproject.toml`** - Scouting scripts package
   - Dependencies: `pymongo`, `tba-api-v3client`, `colorama`, `tqdm`
   - Defines entry points for main scripts (can use `uv run scouting-match`)

4. **`Strategy-Dashboard/pyproject.toml`** - Dashboard package
   - Dependencies: `streamlit`, `plotly`, `numpy`, `pandas`, `scipy`, `pymongo`, `tba-api-v3client`, `colorama`, `tqdm`, `pillow-heif`, `pillow`
   - Entry point for dashboard (`uv run strategy-dashboard`)

5. **`Tools/pyproject.toml`** - Utility scripts package
   - Dependencies: `pymongo`, `tba-api-v3client`, `colorama`, `tqdm`
   - Standalone - can run any tool script directly

6. **`UV_SCRIPTS.md`** - Complete script reference
   - All commands for running Python scripts with uv
   - Organized by package (Scouting-Scripts, Strategy-Dashboard, Tools)

### Files Modified

1. **Batch files** (Windows):
   - `ScoutingMatchScan.bat` - Runs combined match and defense scouting script
   - `Strategy Dashboard.bat` - Updated to use `uv run`
   - All now use `cd /d "%~dp0"` for relative path handling

2. **`CLAUDE.md`** - Updated with:
   - uv workspace setup instructions
   - uv command examples
   - Reference to `UV_SCRIPTS.md`

## Next Steps

### To Start Using uv:

1. **Install uv** (if not already installed):
   ```bash
   pip install uv
   ```

2. **Sync dependencies** (run from repo root):
   ```bash
   # Windows (required - linking doesn't work on Windows)
   uv sync --link-mode=copy

   # Mac/Linux (can use default linking)
   uv sync
   ```

3. **Run scripts**:
   ```bash
   # Dashboard
   uv run --package frc-6413-strategy-dashboard streamlit run Strategy-Dashboard/main.py

   # Scouting
   uv run --package frc-6413-scouting-scripts python Scouting-Scripts/scouting_2025.py

   # Tools
   uv run --package frc-6413-scouting-tools python Tools/get_event_matches_2025_v2.py
   ```

### Optional: Clean Up Old Files

Once uv is working, you can remove:
- `.venv/` folder (if exists)
- `requirements.txt` (deprecated)
- `Scouting-Scripts/requirements.txt` (deprecated)

## Shared Configuration

The `frc-6413-common` package holds V5 schema constants and credentials shared by all Python scripts. Scripts import them as:

```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

`Strategy-Dashboard/config.py` still exists and holds dashboard-specific UI configuration (visualization colors, stat mappings, page configs) plus — for now — a duplicated subset of schema constants. That duplication will be reconciled on a separate dashboard cleanup branch.

## Workspace Structure

```
2026-Strategy-Scouting/
├── pyproject.toml                  # Workspace config (4 members)
├── uv.lock                         # Generated after first `uv sync`
├── Common/
│   ├── pyproject.toml              # Package: frc-6413-common
│   ├── credentials.py.example      # Committed template for new users
│   └── frc_6413_common/
│       ├── __init__.py
│       ├── config.py               # Shared V5 schema constants
│       └── credentials.py          # Gitignored; per-user secrets
├── Scouting-App/                   # Static HTML/JS (no pyproject.toml)
├── Scouting-Scripts/
│   └── pyproject.toml              # Package: frc-6413-scouting-scripts
├── Strategy-Dashboard/
│   ├── pyproject.toml              # Package: frc-6413-strategy-dashboard
│   └── config.py                   # Dashboard-only UI config (kept local)
└── Tools/
    └── pyproject.toml              # Package: frc-6413-scouting-tools
```