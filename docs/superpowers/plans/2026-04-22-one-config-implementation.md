# Centralize config.py and credentials.py — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate three duplicated `config.py` files and three drifted `credentials.py` files into a single shared uv workspace package (`frc-6413-common`), with all script imports migrated to read from it. Strategy-Dashboard's local `config.py` is left untouched (its cleanup is a separate future branch).

**Architecture:** New top-level `Common/` directory becomes the 4th uv workspace member. It contains a Python package `frc_6413_common` with `config.py` and `credentials.py` (gitignored), plus a committed `credentials.py.example` template. Every script outside `Strategy-Dashboard/` switches its `import config as cfg` / `import credentials as creds` lines to `from frc_6413_common import config as cfg, credentials as creds`. The old per-folder files (tracked `config.py` and `credentials.py.example`) are removed from git after the import migration is verified.

**Tech Stack:** Python 3.11+, uv (workspace mode), hatchling (build backend), ruff (linter). No test framework — verification is via `uv sync`, `uv run ruff check`, and `python -c "..."` smoke imports.

**Reference spec:** `docs/superpowers/specs/2026-04-22-one-config-design.md`

**Repo platform note:** All `uv sync` commands use `--link-mode=copy` because Windows requires it (per CLAUDE.md). Mac/Linux users can drop the flag.

---

## File Structure

**New files (committed):**
- `Common/pyproject.toml` — declares `frc-6413-common` package, hatchling build backend
- `Common/credentials.py.example` — template for new users, identical to today's example
- `Common/frc_6413_common/__init__.py` — empty marker file
- `Common/frc_6413_common/config.py` — verbatim copy of current `Scouting-Scripts/config.py`

**New files (gitignored, per-user local):**
- `Common/frc_6413_common/credentials.py` — created during Phase 1 by copying from existing local credentials

**Modified files:**
- Root `pyproject.toml` — add `Common` to workspace members
- `Scouting-Scripts/pyproject.toml` — declare `frc-6413-common` workspace dependency
- `Tools/pyproject.toml` — declare `frc-6413-common` workspace dependency
- `Strategy-Dashboard/pyproject.toml` — declare `frc-6413-common` workspace dependency (no dashboard source files change)
- 16 Python scripts (8 in `Scouting-Scripts/`, 8 in `Tools/`) — import line edits only
- `Scouting-Scripts/prescouting_make_template.py:391` — additional rename `creds.TBAAUTHKEY` → `creds.TBA_AUTH_KEY`
- `UV_SCRIPTS.md` — credentials setup section + import-line note
- `UV_SETUP_SUMMARY.md` — Common package entry + workspace diagram update + new "Shared Configuration" paragraph
- `CLAUDE.md` — update "Key Configuration Files" and the credentials sentence in "Important Notes"

**Files removed from git:**
- `Scouting-Scripts/config.py`
- `Scouting-Scripts/credentials.py.example`
- `Tools/config.py`
- `Tools/credentials.py.example`
- `Strategy-Dashboard/credentials.py.example`

**Files removed from local working copy only (gitignored — never tracked):**
- `Scouting-Scripts/credentials.py`
- `Tools/credentials.py`
- `Strategy-Dashboard/credentials.py`

**Files explicitly NOT touched:**
- `Strategy-Dashboard/config.py` — left as-is, including its duplicated V5 schema constants
- All `Strategy-Dashboard/*.py` and `Strategy-Dashboard/pages/*.py` source files
- All `Scouting-App/*` files (separate JS app)
- `README.md` (out of scope per spec)

---

## Phase 1 — Create the shared package

This phase produces a working `frc-6413-common` package that nothing yet depends on. No script imports change here.

### Task 1.1: Scaffold `Common/` directory and package marker

**Files:**
- Create: `Common/frc_6413_common/__init__.py`

- [ ] **Step 1: Create the directories and empty package marker**

```bash
mkdir -p Common/frc_6413_common
```

Create `Common/frc_6413_common/__init__.py` with this single-line content:

```python
"""Shared configuration constants and credentials for FRC 6413 scripts."""
```

- [ ] **Step 2: Verify the directory layout**

Run: `ls Common/ Common/frc_6413_common/`
Expected: `Common/` shows `frc_6413_common`. `Common/frc_6413_common/` shows `__init__.py`.

---

### Task 1.2: Create `Common/pyproject.toml`

**Files:**
- Create: `Common/pyproject.toml`

- [ ] **Step 1: Write `Common/pyproject.toml` with this exact content**

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

---

### Task 1.3: Create `Common/frc_6413_common/config.py`

**Files:**
- Create: `Common/frc_6413_common/config.py`

This file is a **verbatim copy** of `Scouting-Scripts/config.py` (which is byte-identical to `Tools/config.py`). All 251 lines, including every comment.

- [ ] **Step 1: Copy the file with full content preservation**

```bash
cp Scouting-Scripts/config.py Common/frc_6413_common/config.py
```

- [ ] **Step 2: Verify byte-for-byte match**

Run: `diff Scouting-Scripts/config.py Common/frc_6413_common/config.py`
Expected: no output (files identical).

---

### Task 1.4: Create `Common/frc_6413_common/credentials.py` (gitignored)

This file holds the implementer's local secrets and is gitignored. The cleanest source is `Tools/credentials.py`, which already uses the canonical `TBA_AUTH_KEY` name. (If `Tools/credentials.py` doesn't exist on this machine, fall back to `Scouting-Scripts/credentials.py` and rename `TBAAUTHKEY` to `TBA_AUTH_KEY` after copying.)

**Files:**
- Create: `Common/frc_6413_common/credentials.py` (gitignored — never committed)

- [ ] **Step 1: Copy local credentials into the new location**

```bash
cp Tools/credentials.py Common/frc_6413_common/credentials.py
```

If `Tools/credentials.py` is missing on this machine, instead run:

```bash
cp Scouting-Scripts/credentials.py Common/frc_6413_common/credentials.py
```

then open `Common/frc_6413_common/credentials.py` and rename the variable `TBAAUTHKEY` to `TBA_AUTH_KEY` (the value after the `=` stays the same).

- [ ] **Step 2: Verify the file defines `TBA_AUTH_KEY`**

Run: `grep -E '^TBA_AUTH_KEY' Common/frc_6413_common/credentials.py`
Expected: one matching line beginning with `TBA_AUTH_KEY = `.

- [ ] **Step 3: Verify gitignore is keeping it out of git**

Run: `git check-ignore Common/frc_6413_common/credentials.py`
Expected: output is `Common/frc_6413_common/credentials.py` (meaning git is ignoring it).

---

### Task 1.5: Create `Common/credentials.py.example`

**Files:**
- Create: `Common/credentials.py.example`

This file is a verbatim copy of the existing `Scouting-Scripts/credentials.py.example` (already canonical; uses `TBA_AUTH_KEY`).

- [ ] **Step 1: Copy the example template**

```bash
cp Scouting-Scripts/credentials.py.example Common/credentials.py.example
```

- [ ] **Step 2: Verify match**

Run: `diff Scouting-Scripts/credentials.py.example Common/credentials.py.example`
Expected: no output.

---

### Task 1.6: Add `Common` to root workspace

**Files:**
- Modify: `pyproject.toml` (root, line 33)

- [ ] **Step 1: Edit the workspace members list**

In root `pyproject.toml`, change:

```toml
[tool.uv.workspace]
members = ["Scouting-Scripts", "Strategy-Dashboard", "Tools"]
```

to:

```toml
[tool.uv.workspace]
members = ["Common", "Scouting-Scripts", "Strategy-Dashboard", "Tools"]
```

---

### Task 1.7: Sync workspace and verify the new package builds

- [ ] **Step 1: Run uv sync from repo root**

Run: `uv sync --link-mode=copy`
Expected: completes without errors. Output mentions resolving `frc-6413-common` from the workspace. No `Could not find a version that satisfies` errors.

- [ ] **Step 2: Verify the package can be imported with no consumers wired up yet**

Run: `uv run --project Common python -c "from frc_6413_common import config, credentials; print(config.DB_NAME, credentials.TBA_AUTH_KEY[:6])"`
Expected: `frc_data <first 6 chars of TBA key>` printed to stdout. No `ImportError`.

If the credentials line fails with `AttributeError: module 'frc_6413_common.credentials' has no attribute 'TBA_AUTH_KEY'`, return to Task 1.4 Step 1 fallback and complete the variable rename.

---

### Task 1.8: Commit Phase 1

- [ ] **Step 1: Stage and commit only the tracked new files**

```bash
git add Common/pyproject.toml Common/credentials.py.example Common/frc_6413_common/__init__.py Common/frc_6413_common/config.py pyproject.toml
git status
```

Expected `git status` output: 5 staged files (the four `Common/...` files plus root `pyproject.toml`). `Common/frc_6413_common/credentials.py` should **not** appear (gitignored).

```bash
git commit -m "$(cat <<'EOF'
Add frc-6413-common shared workspace package

Creates a new uv workspace member Common/ containing the
frc_6413_common Python package. Holds shared V5 schema constants
(config.py) and credentials (credentials.py, gitignored) plus a
committed credentials.py.example template.

No consumers depend on this package yet; that wiring lands in the
next commit. The package is buildable and importable on its own.
EOF
)"
```

---

## Phase 2 — Wire up consumer dependencies

Each of the three existing packages declares the new shared package as a workspace dependency. No script source files change in this phase.

### Task 2.1: Add dependency to `Scouting-Scripts/pyproject.toml`

**Files:**
- Modify: `Scouting-Scripts/pyproject.toml`

- [ ] **Step 1: Add the dependency and uv source**

In `Scouting-Scripts/pyproject.toml`, modify the `[project]` section's `dependencies` list to include `"frc-6413-common"` as the first entry, and add a new `[tool.uv.sources]` section at the bottom of the file. The full file becomes:

```toml
[project]
name = "frc-6413-scouting-scripts"
version = "2026.0.0"
description = "Python scripts for collecting scouting data via QR codes"
requires-python = ">=3.11"
dependencies = [
    "frc-6413-common",
    "pymongo>=4.6.0",
    "tba-api-v3client @ git+https://github.com/TBA-API/tba-api-client-python@4f6ded8fb4bf8f7896891a9aa778ce15a2ef720b",
    "colorama>=0.4.6",
    "tqdm>=4.66.0",
    "statbotics>=3.0.0",
    "tabulate>=0.10.0",
]

[project.scripts]
# Main scripts can be run via uv run
scouting-match = "scouting_2025:main"
scouting-defense = "defense_scouting_2025:main"
scouting-training-check = "training_checking_2025:main"
scouting-training-collect = "training_collection_2025:main"

[tool.uv.sources]
frc-6413-common = { workspace = true }
```

---

### Task 2.2: Add dependency to `Tools/pyproject.toml`

**Files:**
- Modify: `Tools/pyproject.toml`

- [ ] **Step 1: Add the dependency and uv source**

The full file becomes:

```toml
[project]
name = "frc-6413-scouting-tools"
version = "2026.0.0"
description = "Utility scripts for data generation and management"
requires-python = ">=3.11"
dependencies = [
    "frc-6413-common",
    "pymongo>=4.6.0",
    "tba-api-v3client @ git+https://github.com/TBA-API/tba-api-client-python@4f6ded8fb4bf8f7896891a9aa778ce15a2ef720b",
    "colorama>=0.4.6",
    "tqdm>=4.66.0",
]

[tool.uv.sources]
frc-6413-common = { workspace = true }
```

---

### Task 2.3: Add dependency to `Strategy-Dashboard/pyproject.toml`

**Files:**
- Modify: `Strategy-Dashboard/pyproject.toml`

This is the only file under `Strategy-Dashboard/` that gets edited in this PR. No dashboard `.py` source file changes.

- [ ] **Step 1: Add the dependency and uv source**

The full file becomes:

```toml
[project]
name = "frc-6413-strategy-dashboard"
version = "2026.0.0"
description = "Streamlit dashboard for visualizing and analyzing scouting data"
requires-python = ">=3.11"
dependencies = [
    "frc-6413-common",
    "streamlit>=1.41.0",
    "plotly>=5.24.0",
    "numpy>=2.0.0",
    "pandas>=2.2.0",
    "scipy>=1.13.0",
    "pymongo>=4.6.0",
    "tba-api-v3client @ git+https://github.com/TBA-API/tba-api-client-python@4f6ded8fb4bf8f7896891a9aa778ce15a2ef720b",
    "colorama>=0.4.6",
    "streamlit-plotly-events>=0.0.6",
    "tqdm>=4.66.0",
    "pillow-heif>=0.22.0",
    "pillow>=10.0.0",
]

[tool.uv.sources]
frc-6413-common = { workspace = true }
```

---

### Task 2.4: Sync and verify cross-package imports

- [ ] **Step 1: Re-sync the workspace**

Run: `uv sync --link-mode=copy`
Expected: completes without errors. uv resolves `frc-6413-common` as a workspace dependency of all three consumers.

- [ ] **Step 2: Smoke-import from each consumer environment**

Run each command in turn. Each must print `frc_data <6 chars>` and exit 0:

```bash
uv run --package frc-6413-scouting-scripts python -c "from frc_6413_common import config, credentials; print(config.DB_NAME, credentials.TBA_AUTH_KEY[:6])"
uv run --package frc-6413-scouting-tools python -c "from frc_6413_common import config, credentials; print(config.DB_NAME, credentials.TBA_AUTH_KEY[:6])"
uv run --package frc-6413-strategy-dashboard python -c "from frc_6413_common import config, credentials; print(config.DB_NAME, credentials.TBA_AUTH_KEY[:6])"
```

Expected: each prints `frc_data <chars>` and exits successfully. If any reports `ModuleNotFoundError: No module named 'frc_6413_common'`, re-check that the corresponding `pyproject.toml` has both the `dependencies` entry *and* the `[tool.uv.sources]` block, then re-run `uv sync --link-mode=copy`.

---

### Task 2.5: Commit Phase 2

- [ ] **Step 1: Stage and commit the three pyproject changes**

```bash
git add Scouting-Scripts/pyproject.toml Tools/pyproject.toml Strategy-Dashboard/pyproject.toml uv.lock
git commit -m "$(cat <<'EOF'
Wire frc-6413-common as workspace dependency of all 3 consumers

Each consumer pyproject.toml now declares frc-6413-common as a
workspace dependency so scripts can do
`from frc_6413_common import config, credentials`.

No script source files change in this commit. Strategy-Dashboard
gets the dependency line so the future dashboard cleanup branch
can flip imports in one move; no dashboard .py files are touched.
EOF
)"
```

Note: `uv.lock` may or may not have changed — `git add uv.lock` is harmless if it didn't.

---

## Phase 3 — Migrate Scouting-Scripts imports

Mechanical change pattern for every script:
- `import config as cfg` → `from frc_6413_common import config as cfg`
- `import credentials as creds` → `from frc_6413_common import credentials as creds`

References to `cfg.X` and `creds.X` in the script bodies are unchanged.

### Task 3.1: Migrate all 8 Scouting-Scripts files

**Files:**
- Modify: `Scouting-Scripts/defense_scouting_2026.py:16`
- Modify: `Scouting-Scripts/file_to_MongoDB_v1.py:30-31`
- Modify: `Scouting-Scripts/find_missing_data.py:20-21`
- Modify: `Scouting-Scripts/prescouting_make_template.py:20-21,391`
- Modify: `Scouting-Scripts/prescouting_upload.py:25-26`
- Modify: `Scouting-Scripts/scouting_2026.py:27-28`
- Modify: `Scouting-Scripts/training_checking_2026.py:24-25`
- Modify: `Scouting-Scripts/training_collection_2026.py:29-30`

- [ ] **Step 1: Edit `Scouting-Scripts/defense_scouting_2026.py`**

Replace this exact line at line 16:
```python
import config as cfg
```
with:
```python
from frc_6413_common import config as cfg
```

(File has no `import credentials` line.)

- [ ] **Step 2: Edit `Scouting-Scripts/file_to_MongoDB_v1.py`**

Replace these exact two lines at lines 30–31:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

- [ ] **Step 3: Edit `Scouting-Scripts/find_missing_data.py`**

Replace these exact two lines at lines 20–21 (note: original order is credentials first, then config — preserve that order):
```python
import credentials as creds
import config as cfg
```
with:
```python
from frc_6413_common import credentials as creds
from frc_6413_common import config as cfg
```

- [ ] **Step 4: Edit `Scouting-Scripts/prescouting_make_template.py` (TWO edits)**

Replace these exact two lines at lines 20–21:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

Then replace this exact line at line 391:
```python
    configuration = tbaapiv3client.Configuration( api_key={'X-TBA-Auth-Key': creds.TBAAUTHKEY} )
```
with:
```python
    configuration = tbaapiv3client.Configuration( api_key={'X-TBA-Auth-Key': creds.TBA_AUTH_KEY} )
```

(This rename brings the script into line with the canonical key name and incidentally fixes a latent bug in `find_missing_data.py:220`, which already references `creds.TBA_AUTH_KEY` against the old per-folder credentials file that defines only `TBAAUTHKEY`.)

- [ ] **Step 5: Edit `Scouting-Scripts/prescouting_upload.py`**

Replace these exact two lines at lines 25–26:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

- [ ] **Step 6: Edit `Scouting-Scripts/scouting_2026.py`**

Replace these exact two lines at lines 27–28:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

- [ ] **Step 7: Edit `Scouting-Scripts/training_checking_2026.py`**

Replace these exact two lines at lines 24–25:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

- [ ] **Step 8: Edit `Scouting-Scripts/training_collection_2026.py`**

Replace these exact two lines at lines 29–30:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

- [ ] **Step 9: Verify no `import config` or `import credentials` lines remain in `Scouting-Scripts/`**

Use the Grep tool with pattern `^(import config|import credentials)` over `Scouting-Scripts/*.py`.
Expected: zero matches.

Also verify no `TBAAUTHKEY` references remain:

Use the Grep tool with pattern `TBAAUTHKEY` over `Scouting-Scripts/*.py`.
Expected: zero matches.

- [ ] **Step 10: Bytecode-compile every Scouting-Scripts file (catches syntax / typos in the new import lines)**

Run: `uv run --package frc-6413-scouting-scripts python -m compileall -q Scouting-Scripts/`
Expected: no output and exit code 0. Any output means a file failed to compile — the message identifies which file and line.

- [ ] **Step 11: Smoke-import one representative migrated module (catches missing `frc_6413_common` resolution)**

Run: `uv run --package frc-6413-scouting-scripts python -c "import importlib.util, sys; spec = importlib.util.spec_from_file_location('m', 'Scouting-Scripts/scouting_2026.py'); mod = importlib.util.module_from_spec(spec); sys.modules['m'] = mod; spec.loader.exec_module(mod); print('ok')"`
Expected: prints `ok`. If it prints `ok` after some other script output (e.g., a banner from a `print` at module top), that's still a pass — the imports ran. If it fails with `ModuleNotFoundError: No module named 'config'` or `'credentials'`, a file in this phase still has the bare import — find it with the Grep tool using pattern `^(import config|import credentials)` over `Scouting-Scripts/*.py`.

(Hit Ctrl-C if the script blocks on stdin — that means top-level code is reading input, but the imports already ran successfully if no `ModuleNotFoundError` appeared first.)

- [ ] **Step 12: Run ruff**

Run: `uv run ruff check Scouting-Scripts/`
Expected: no errors. Warnings about unrelated style are pre-existing and OK; new errors are not.

- [ ] **Step 13: Commit**

```bash
git add Scouting-Scripts/
git commit -m "$(cat <<'EOF'
Migrate Scouting-Scripts imports to frc_6413_common

All 8 Scouting-Scripts/*.py files now import config and credentials
from the shared frc_6413_common package. References to cfg.X and
creds.X in script bodies are unchanged.

prescouting_make_template.py also gets a one-character rename
(creds.TBAAUTHKEY -> creds.TBA_AUTH_KEY) to use the canonical key
name. This incidentally fixes a latent bug in find_missing_data.py
which already used creds.TBA_AUTH_KEY against a credentials file
that defined only TBAAUTHKEY.
EOF
)"
```

---

## Phase 4 — Migrate Tools imports

Same mechanical pattern as Phase 3.

### Task 4.1: Migrate all 8 Tools files

**Files:**
- Modify: `Tools/get_event_list_of_teams_2025_v1.py:41-42`
- Modify: `Tools/get_event_matches_2022_v2.py:23`
- Modify: `Tools/get_event_matches_2025_v2.py:29-30`
- Modify: `Tools/get_event_matches_2026_v1.py:19-20`
- Modify: `Tools/get_event_schedule_from_mongodb_2025_v1.py:50-51`
- Modify: `Tools/get_event_teams_simple_2025_v1.py:37`
- Modify: `Tools/get_events_by_year_keys_2026_v1.py:43`
- Modify: `Tools/MongoDB_to_MongoDB_v1.py:30-31`

- [ ] **Step 1: Edit `Tools/get_event_list_of_teams_2025_v1.py`**

Replace these exact two lines at lines 41–42:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

- [ ] **Step 2: Edit `Tools/get_event_matches_2022_v2.py`**

Replace this exact line at line 23 (this file has only the credentials import, no config import):
```python
import credentials as creds
```
with:
```python
from frc_6413_common import credentials as creds
```

- [ ] **Step 3: Edit `Tools/get_event_matches_2025_v2.py`**

Replace these exact two lines at lines 29–30:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

- [ ] **Step 4: Edit `Tools/get_event_matches_2026_v1.py`**

Replace these exact two lines at lines 19–20:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

- [ ] **Step 5: Edit `Tools/get_event_schedule_from_mongodb_2025_v1.py`**

Replace these exact two lines at lines 50–51:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

- [ ] **Step 6: Edit `Tools/get_event_teams_simple_2025_v1.py`**

Replace this exact line at line 37 (this file has only the config import, no credentials import):
```python
import config as cfg
```
with:
```python
from frc_6413_common import config as cfg
```

- [ ] **Step 7: Edit `Tools/get_events_by_year_keys_2026_v1.py`**

Replace this exact line at line 43 (this file has only the config import):
```python
import config as cfg
```
with:
```python
from frc_6413_common import config as cfg
```

- [ ] **Step 8: Edit `Tools/MongoDB_to_MongoDB_v1.py`**

Replace these exact two lines at lines 30–31:
```python
import config as cfg
import credentials as creds
```
with:
```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

- [ ] **Step 9: Verify no bare `import config` or `import credentials` lines remain in `Tools/`**

Use the Grep tool with pattern `^(import config|import credentials)` over `Tools/*.py`.
Expected: zero matches.

- [ ] **Step 10: Bytecode-compile every Tools file**

Run: `uv run --package frc-6413-scouting-tools python -m compileall -q Tools/`
Expected: no output and exit code 0.

- [ ] **Step 11: Smoke-import one representative migrated module**

Run: `uv run --package frc-6413-scouting-tools python -c "import importlib.util, sys; spec = importlib.util.spec_from_file_location('m', 'Tools/get_event_matches_2026_v1.py'); mod = importlib.util.module_from_spec(spec); sys.modules['m'] = mod; spec.loader.exec_module(mod); print('ok')"`
Expected: prints `ok`. Same Ctrl-C caveat as Phase 3 if the script blocks on input; what matters is no `ModuleNotFoundError`.

- [ ] **Step 12: Run ruff**

Run: `uv run ruff check Tools/`
Expected: no new errors about unresolved imports.

- [ ] **Step 13: Commit**

```bash
git add Tools/
git commit -m "$(cat <<'EOF'
Migrate Tools imports to frc_6413_common

All 8 Tools/*.py files now import config and credentials from the
shared frc_6413_common package. References to cfg.X and creds.X in
script bodies are unchanged.
EOF
)"
```

---

## Phase 5 — Remove the old per-folder files

The new shared package is the only source of truth. The duplicates in `Scouting-Scripts/` and `Tools/` (and the `credentials.py.example` in `Strategy-Dashboard/`) are now unreferenced and get removed from git. Each user's gitignored local `credentials.py` files in those folders also get cleaned up from working copies.

### Task 5.1: Remove tracked files from git

**Files:**
- Delete: `Scouting-Scripts/config.py`
- Delete: `Scouting-Scripts/credentials.py.example`
- Delete: `Tools/config.py`
- Delete: `Tools/credentials.py.example`
- Delete: `Strategy-Dashboard/credentials.py.example`

- [ ] **Step 1: Remove the five tracked files**

```bash
git rm Scouting-Scripts/config.py Scouting-Scripts/credentials.py.example Tools/config.py Tools/credentials.py.example Strategy-Dashboard/credentials.py.example
```

Expected: git reports 5 files removed.

- [ ] **Step 2: Confirm `Strategy-Dashboard/config.py` is still present**

Run: `ls Strategy-Dashboard/config.py`
Expected: file exists. (This is the file we deliberately keep — the dashboard's own config is untouched.)

---

### Task 5.2: Remove gitignored local credentials files from working copy

These files are not tracked by git but exist in each user's working copy. Removing them prevents the user from accidentally editing the now-stale local copy.

- [ ] **Step 1: Remove the three local-only files**

```bash
rm -f Scouting-Scripts/credentials.py Tools/credentials.py Strategy-Dashboard/credentials.py
```

Expected: no errors. (Files may not exist on a fresh clone; `-f` makes that OK.)

- [ ] **Step 2: Confirm `git status` is clean for these paths**

Run: `git status`
Expected: no entries for the three removed files (they were never tracked).

---

### Task 5.3: Clean stale `__pycache__` directories

Compiled bytecode for the now-deleted `config.py` and `credentials.py` modules sits in `__pycache__/` directories. Stale `.pyc` files are harmless but cleaning them prevents confusion.

- [ ] **Step 1: Remove all `__pycache__` directories under the affected folders**

```bash
rm -rf Scouting-Scripts/__pycache__ Tools/__pycache__ Strategy-Dashboard/__pycache__
```

Expected: no errors. Directories may not exist if the user has never run a script; that's fine.

- [ ] **Step 2: Confirm no leftover `.pyc` references to the old modules**

Use the Grep tool with pattern `(Scouting-Scripts|Tools|Strategy-Dashboard)/__pycache__/(config|credentials)\.cpython` (just to surface any if they exist).
Expected: zero matches.

---

### Task 5.4: End-to-end verification after deletions

- [ ] **Step 1: Re-sync the workspace**

Run: `uv sync --link-mode=copy`
Expected: completes without errors.

- [ ] **Step 2: Run ruff over the whole repo**

Run: `uv run ruff check .`
Expected: no new errors compared to Phase 4 verification. Any pre-existing warnings about unrelated style issues are OK.

- [ ] **Step 3: Smoke-import a representative migrated script from each consumer**

```bash
uv run --package frc-6413-scouting-scripts python -c "import importlib.util, sys; spec = importlib.util.spec_from_file_location('m', 'Scouting-Scripts/scouting_2026.py'); mod = importlib.util.module_from_spec(spec); sys.modules['m'] = mod; spec.loader.exec_module(mod); print('ok')"
uv run --package frc-6413-scouting-tools python -c "import importlib.util, sys; spec = importlib.util.spec_from_file_location('m', 'Tools/get_event_matches_2026_v1.py'); mod = importlib.util.module_from_spec(spec); sys.modules['m'] = mod; spec.loader.exec_module(mod); print('ok')"
```

Expected: both print `ok`. (Hit Ctrl-C if either blocks on input.)

If either fails with `ModuleNotFoundError: No module named 'config'`, a script was missed in Phase 3 or 4 — find it (`grep -rn '^import config' Scouting-Scripts/ Tools/`) and migrate.

- [ ] **Step 4: Smoke-import the dashboard (which still uses its local config)**

```bash
uv run --package frc-6413-strategy-dashboard python -c "import importlib.util, sys; spec = importlib.util.spec_from_file_location('m', 'Strategy-Dashboard/utils.py'); mod = importlib.util.module_from_spec(spec); sys.modules['m'] = mod; spec.loader.exec_module(mod); print('ok')"
```

Expected: prints `ok`. The dashboard's `utils.py` still does `import config as cfg` and finds `Strategy-Dashboard/config.py` on its sys.path — this is the deliberate "left alone" behavior.

---

### Task 5.5: Commit Phase 5

- [ ] **Step 1: Stage and commit the deletions**

```bash
git add -u
git status
```

Expected `git status` shows 5 deletions (the tracked files only).

```bash
git commit -m "$(cat <<'EOF'
Remove per-folder config.py and credentials.py.example files

The shared frc_6413_common package is now the sole source of truth
for V5 schema constants and credentials. The old per-folder copies
in Scouting-Scripts/ and Tools/, plus the redundant
credentials.py.example files in all three consumer folders, are
removed.

Strategy-Dashboard/config.py is intentionally left in place — it
still holds dashboard-only UI configuration and a duplicated
subset of schema constants that will be reconciled on a separate
dashboard cleanup branch.
EOF
)"
```

---

## Phase 6 — Update documentation

### Task 6.1: Update `UV_SCRIPTS.md`

**Files:**
- Modify: `UV_SCRIPTS.md` (insert credentials setup section, add note in Adding Dependencies section)

- [ ] **Step 1: Insert a "Setting up credentials" section after the Initial Setup block**

In `UV_SCRIPTS.md`, find the existing block:

```markdown
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

## Quick Reference
```

Insert this new section between the closing triple-backtick of the Initial Setup block and the `## Quick Reference` heading:

```markdown
## Setting up credentials (one-time, per machine)

The shared package needs your TBA API key and MongoDB connection string before any script can run. Copy the committed example file and edit your local copy:

```bash
cp Common/credentials.py.example Common/frc_6413_common/credentials.py
```

Then open `Common/frc_6413_common/credentials.py` and fill in:

- `TBA_AUTH_KEY` — your The Blue Alliance API key from <https://www.thebluealliance.com/account>
- `PRIMARY_CONNECTION_STRING` — `"mongodb://localhost:27017/"` for a local MongoDB, or your Atlas connection string

`Common/frc_6413_common/credentials.py` is gitignored and will never be committed.

```

- [ ] **Step 2: Add a note to the "Adding Dependencies" section about the shared package**

In `UV_SCRIPTS.md`, find the existing "## Adding Dependencies" section and append this paragraph at the end of the section (after the last code block):

```markdown

### Shared configuration constants

V5 schema constants (`DB_NAME`, `V5_COL_*`, `DT_*`, etc.) and credentials live in the `frc-6413-common` package and are imported as:

```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

To edit shared schema constants, edit `Common/frc_6413_common/config.py`. Dashboard-specific UI configuration (colors, stat mappings, page configs) lives in `Strategy-Dashboard/config.py` instead.
```

---

### Task 6.2: Update `UV_SETUP_SUMMARY.md`

**Files:**
- Modify: `UV_SETUP_SUMMARY.md` (add Common entry, update workspace diagram, add Shared Configuration section)

- [ ] **Step 1: Add `Common/pyproject.toml` to the "New Files Created" list**

In `UV_SETUP_SUMMARY.md`, find the numbered list under `### New Files Created`. Insert a new item as item 1 (renumbering the rest):

```markdown
1. **`Common/pyproject.toml`** - Shared utilities package
   - Dependencies: none
   - Holds the `frc_6413_common` Python package with shared V5 schema constants and credentials
   - All other packages depend on this one as a workspace dependency
```

So `Root pyproject.toml` becomes item 2, `Scouting-Scripts/pyproject.toml` becomes item 3, etc.

- [ ] **Step 2: Update the Workspace Structure diagram**

Replace the existing workspace diagram block:

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

with:

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

- [ ] **Step 3: Add a "Shared Configuration" section before "## Workspace Structure"**

Insert this section in `UV_SETUP_SUMMARY.md` immediately above the `## Workspace Structure` heading:

```markdown
## Shared Configuration

The `frc-6413-common` package holds V5 schema constants and credentials shared by all Python scripts. Scripts import them as:

```python
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
```

`Strategy-Dashboard/config.py` still exists and holds dashboard-specific UI configuration (visualization colors, stat mappings, page configs) plus — for now — a duplicated subset of schema constants. That duplication will be reconciled on a separate dashboard cleanup branch.

```

---

### Task 6.3: Update `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md` (Key Configuration Files list and Important Notes section)

- [ ] **Step 1: Update the "Key Configuration Files" section**

In `CLAUDE.md`, find this exact block:

```markdown
### Key Configuration Files

- `Scouting-Scripts/config.py` - V5 schema constants, collection names, docTypes
- `Scouting-Scripts/credentials.py` - MongoDB connection strings, TBA API key
- `Scouting-App/config.js` - Event code for scouting app (edit `eventCode` field)
- `Strategy-Dashboard/config.py` - Dashboard visualization settings, stat mappings
```

Replace it with:

```markdown
### Key Configuration Files

- `Common/frc_6413_common/config.py` - V5 schema constants, collection names, docTypes (shared by Scouting-Scripts, Tools, and the Strategy-Dashboard once the dashboard cleanup branch lands)
- `Common/frc_6413_common/credentials.py` - MongoDB connection strings, TBA API key (gitignored; copy from `Common/credentials.py.example`)
- `Scouting-App/config.js` - Event code for scouting app (edit `eventCode` field)
- `Strategy-Dashboard/config.py` - Dashboard-only UI configuration (visualization colors, stat mappings, page configs) plus a still-duplicated subset of schema constants slated for cleanup on a separate branch
```

- [ ] **Step 2: Update the credentials line in "Important Notes"**

In `CLAUDE.md`, find this exact line in the "## Important Notes" section:

```markdown
- Credentials (MongoDB connection strings, TBA API key) are in `credentials.py` files - keep these private
```

Replace with:

```markdown
- Credentials (MongoDB connection strings, TBA API key) are in `Common/frc_6413_common/credentials.py` - keep this file private (it is gitignored)
```

---

### Task 6.4: Commit Phase 6

- [ ] **Step 1: Stage and commit the doc updates**

```bash
git add UV_SCRIPTS.md UV_SETUP_SUMMARY.md CLAUDE.md
git commit -m "$(cat <<'EOF'
Update docs for the consolidated frc_6413_common package

UV_SCRIPTS.md: new "Setting up credentials" section pointing at
Common/credentials.py.example, plus a note in Adding Dependencies
about the shared package.

UV_SETUP_SUMMARY.md: Common/pyproject.toml entry, updated workspace
diagram showing all 4 members and the Common/ layout, new
"Shared Configuration" section.

CLAUDE.md: Key Configuration Files now points at
Common/frc_6413_common/{config,credentials}.py; the Important Notes
credentials line is updated to match.

README.md is intentionally left alone (out of scope per spec).
EOF
)"
```

---

## Phase 7 — Final end-to-end verification

This phase is read-only verification — no edits, no commits.

### Task 7.1: Whole-repo sanity check

- [ ] **Step 1: Confirm `git status` is clean**

Run: `git status`
Expected: "nothing to commit, working tree clean" (apart from any pre-existing untracked files like local `OLLAMA_INFO.md`).

- [ ] **Step 2: Confirm no leftover `import config` or `import credentials` outside the dashboard**

Use the Grep tool with pattern `^(import config|import credentials)` over the whole repo.
Expected: matches only in `Strategy-Dashboard/` files (`utils.py`, `format_photos.py`, `pages/*.py`). Zero matches in `Scouting-Scripts/` or `Tools/`.

- [ ] **Step 3: Confirm no `TBAAUTHKEY` references remain anywhere in the codebase**

Use the Grep tool with pattern `TBAAUTHKEY` over the whole repo.
Expected: zero matches.

- [ ] **Step 4: Run ruff on the whole repo**

Run: `uv run ruff check .`
Expected: no errors. Pre-existing style warnings are OK.

- [ ] **Step 5: Confirm the deleted files are not on disk**

Run: `ls Scouting-Scripts/config.py Scouting-Scripts/credentials.py.example Tools/config.py Tools/credentials.py.example Strategy-Dashboard/credentials.py.example 2>&1 | head -20`
Expected: every line shows "No such file or directory".

- [ ] **Step 6: Confirm the new files are present**

Run: `ls Common/pyproject.toml Common/credentials.py.example Common/frc_6413_common/__init__.py Common/frc_6413_common/config.py Common/frc_6413_common/credentials.py`
Expected: all 5 files listed (no errors).

- [ ] **Step 7: Confirm git log shows the expected commit history on this branch**

Run: `git log --oneline -10`
Expected: 6 new commits on top of the design-doc commit (`40dd743`):
1. Add frc-6413-common shared workspace package
2. Wire frc-6413-common as workspace dependency of all 3 consumers
3. Migrate Scouting-Scripts imports to frc_6413_common
4. Migrate Tools imports to frc_6413_common
5. Remove per-folder config.py and credentials.py.example files
6. Update docs for the consolidated frc_6413_common package

If counts differ (e.g., a phase was split into multiple commits because something needed re-doing), that's fine as long as each commit is logically self-contained.

---

## Done

The repo now has:
- One source of truth for V5 schema constants: `Common/frc_6413_common/config.py`
- One source of truth for credentials: `Common/frc_6413_common/credentials.py` (gitignored)
- One template for new users: `Common/credentials.py.example`
- All 16 migrated scripts importing from the shared package
- The latent `find_missing_data.py` bug fixed as a side effect of the credential rename
- Strategy-Dashboard untouched at the source level (one pyproject.toml line added so the future cleanup branch can flip imports cleanly)

The dashboard cleanup is the next logical follow-up; see "Future work" in the design doc (`docs/superpowers/specs/2026-04-22-one-config-design.md`).
