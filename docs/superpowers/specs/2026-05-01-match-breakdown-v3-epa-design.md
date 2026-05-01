# Match Breakdown v3 — Statbotics EPA Display

**Date:** 2026-05-01
**Branch:** feature/match-breakdown-v3-epa

## Summary

Add Statbotics `norm_epa['current']` values next to each team number in the
match breakdown output. This gives the strategy team an at-a-glance EPA
signal alongside pre-scouting notes without changing any other behavior.

## Files Changed

- `Tools/pyproject.toml` — add `statbotics` dependency
- `Tools/get_match_breakdown_2026_v3.py` — new file, based on v2

## Design

### Dependency

Add `statbotics` to `Tools/pyproject.toml` dependencies and run `uv sync
--link-mode=copy` to install it.

### New function: `get_epa(team_number: int) -> Optional[float]`

- Creates a `statbotics.Statbotics()` instance and calls `get_team(team_number)`
- Extracts and returns `norm_epa['current']` as a float
- Returns `None` on any exception (API unavailable, team not found, missing field)
- Exceptions are logged at WARNING level; nothing is printed to the user

### `main()` changes

After fetching `prescout_map`, build:

```python
epa_map: Dict[str, Optional[float]] = {
    tk: get_epa(int(tk[3:])) for tk in all_teams
}
```

Pass `epa_map` into `print_alliance_block` and `print_opponent_block`.

### Print function changes

Each team header line changes from:

```
6413
```

to one of:

```
6413 (EPA: 1847.3)
6413 (EPA: N/A)
```

- EPA is always shown — `N/A` only when `epa_map[tk]` is `None`
- Value formatted to one decimal place: `f"{epa:.1f}"`
- Header color unchanged (blue for alliance, red for opponents)

### No other changes

Prescout notes display, "No data" logic, CLI args (`-e`, `-t`, `-m`), logging,
MongoDB connection, and error handling are identical to v2.

## Error Handling

| Situation | Behavior |
|-----------|----------|
| Statbotics API unreachable | `get_epa` returns `None` → shows `(EPA: N/A)` |
| Team not in Statbotics | `get_epa` returns `None` → shows `(EPA: N/A)` |
| `norm_epa` field missing | `get_epa` returns `None` → shows `(EPA: N/A)` |

## Example Output

```
Our alliance:

6413 (EPA: 1234.5)
  Strong auto, reliable L3 climb

4774 (EPA: 987.2)
  No data

Opponents:

254 (EPA: 2015.0)
  Weak defense
```
