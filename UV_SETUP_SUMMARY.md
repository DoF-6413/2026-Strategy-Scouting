# UV Workspace Migration Summary

## What Was Changed

### New Files Created

1. **Root `pyproject.toml`** - Workspace configuration
   - Defines the workspace with 3 member packages
   - Sets Python version requirement (>=3.11)
   - Includes optional `common` dependency group

2. **`Scouting-Scripts/pyproject.toml`** - Scouting scripts package
   - Dependencies: `pymongo`, `tba-api-v3client`, `colorama`, `tqdm`
   - Defines entry points for main scripts (can use `uv run scouting-match`)

3. **`Strategy-Dashboard/pyproject.toml`** - Dashboard package
   - Dependencies: `streamlit`, `plotly`, `numpy`, `pandas`, `scipy`, `pymongo`, `tba-api-v3client`, `colorama`, `streamlit-plotly-events`, `tqdm`, `pillow-heif`, `pillow`
   - Entry point for dashboard (`uv run strategy-dashboard`)

4. **`Tools/pyproject.toml`** - Utility scripts package
   - Dependencies: `pymongo`, `tba-api-v3client`, `colorama`, `tqdm`
   - Standalone - can run any tool script directly

5. **`UV_SCRIPTS.md`** - Complete script reference
   - All commands for running Python scripts with uv
   - Organized by package (Scouting-Scripts, Strategy-Dashboard, Tools)

### Files Modified

1. **Batch files** (Windows):
   - `Scouting Match v8 Scan.bat` - Updated to use `uv run`
   - `Scouting Defense v3 Scan.bat` - Updated to use `uv run`
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

## Workspace Structure

```
2026-Strategy-Scouting/
├── pyproject.toml          # Workspace config
├── uv.lock                 # Generated after first `uv sync`
├── Scouting-App/           # Static HTML/JS (no pyproject.toml)
├── Scouting-Scripts/
│   └── pyproject.toml      # Package: frc-6413-scouting-scripts
├── Strategy-Dashboard/
│   └── pyproject.toml      # Package: frc-6413-strategy-dashboard
└── Tools/
    └── pyproject.toml      # Package: frc-6413-scouting-tools
```