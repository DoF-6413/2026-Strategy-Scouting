DASHBOARD_MODE = "real"
"""
The mode the dashboard is running in. Used to choose whether to get random data or
the real TBA/scouting data.

Valid options: "random" or "real"
"""


##### DATABASE CONFIG #####
#region DATABASE CONFIG

# The DB/collection/docType names are shared with the rest of the scripts in
# this repo, so they live in frc_6413_common.config instead of being
# duplicated here.
from frc_6413_common.config import (  # noqa: E402, F401
    DB_NAME,
    DT_EVENTS_TEAMS,
    DT_SCOUTING_MATCH,
    DT_SCOUTING_PRESCOUT,
    V5_COL_EVENTS,
    V5_COL_MATCHES,
    V5_COL_SCHEDULE,
    V5_COL_SCOUTING,
)

#endregion

#####################################
#####################################
#####################################

##### GENERAL DASHBOARD CONFIGURATION #####
#region GENERAL
COMP_LEVEL_KEY_TO_TEXT = {
    "qm": "Quals",
    "sf": "Playoffs",
    "f": "Finals"
}
""""Dictionary mapping comp level keys to human readable text"""

DEFAULT_COMPARE_GRAPH_COLORS = [
    "rgb(31, 119, 180)",
    "rgb(214, 39, 40)",
    "rgb(255, 127, 14)",
    "rgb(44, 160, 44)",
    "rgb(148, 103, 189)",
]
"""List of our preferred visualization colors to default to.
First two are blue and red for blue and red alliance comparisons
"""

TREND_SLOPE_MAPPING = [
    -0.8,
    -0.3,
    0.3,
    0.8,
]
"""List holding thresholds for how significant the slope of a trend is.

Thresholds are for (ordered): major down, minor down, minor up, major up"""

SLOPE_COLOR_MAPPING = [
    "red",
    "chocolate",
    "grey",
    "olivedrab",
    "darkgreen",
]
"""List holding colors that correspond to trend indexes. Colors should follow css color conventions.

Trend indexes and each of the values in this list correspond to:
major down, minor down, no significant change, minor up, major up."""

SLOPE_LABEL_MAPPING = [
    "Major Downward Trend",
    "Minor Downward Trend",
    "No Significant Trend",
    "Minor Upward Trend",
    "Major Upward Trend",
]
"""List holding human-readable labels that correspond to trend indexes, in the
same order (and for the same indexes) as ``SLOPE_COLOR_MAPPING``. Used as
chart legend entries."""

ROBOT_PHOTOS_FOLDER = "formatted_photos"
"""String holding the name of the folder for formatted robot photos in the Strategy Dashboard directory."""

ROBOT_PHOTOS_UNFORMATTED_FOLDER = "raw_photos"
"""String holding the name of the folder for raw, unformatted robot photos."""

NO_PHOTO_FILE_NAME = "no_photo"
"""String holding the name of a placeholder in the robot photos folders that is displayed when there's no image available for a team"""

ROBOT_PHOTOS_WIDTH = 400
"""Integer holding the despired width (in pixels) that robot photos should be resized to."""

ROBOT_PHOTOS_FORMAT = "jpg"
"""String holding the file extension used for formatted robot photos"""
#endregion

#####################################
#####################################
#####################################

##### GAME SPECIFIC VARIABLES #####
#region GAME SPECIFIC

# TODO: This whole region gets hand-rewritten every season (see the 2025->2026
# port). Scouting-Scripts/mappings.json already drives its field mapping data
# instead of hardcoding it per season - consider a similar data-driven
# approach here (e.g. a per-season stats mapping file) so a new season's
# dashboard stats/labels/colors/tabs can be reconfigured without editing
# Python, and so this file stops drifting out of sync with the actual stored
# schema between seasons.

SELECTABLE_STATS = [
    'totalGamePieces',
    'autoHub',
    'autoHubMiss',
    'teleHub',
    'teleHubMiss',
]
"""List containing all standard stats selectable by stat_selector inputs.

Every value in this list should correspond to a column in the MongoDB match scouting entries
"""

# ponytail: 2026's single game piece has no per-level scoring and the
# scouting script doesn't precompute an accuracy field (see
# scouting_2026_v2.py's inflate_tablet_data), so there's nothing to list
# here this year. Add accuracy keys back if/when that gets computed.
SELECTABLE_ACCURACY_KEYS = []
"""
List containing stats that are accuracies. Used for stat_selectors when we only want the
user to select accuracy stats

Every value in this list should correspond to a column in the MongoDB match scouting entries
"""

STAT_KEY_TO_TEXT = {
    'totalGamePieces': 'Total Game Pieces',
    'autoHub': 'Hub (Auto)',
    'autoHubMiss': 'Hub Misses (Auto)',
    'teleHub': 'Hub (Teleop)',
    'teleHubMiss': 'Hub Misses (Teleop)',
}
"""Dictionary mapping stat keys as specified in the database to human readable text"""

STAT_COLOR_MAPPING = {
    'totalGamePieces': 'black',
    'autoHub': 'royalblue',
    'autoHubMiss': 'indianred',
    'teleHub': 'darkblue',
    'teleHubMiss': 'firebrick',
}
"""Dictionary mapping stat keys as specified in the database to colors so traces roughly align with the desired stat."""

##### CONFIGURATIONS FOR SPECIFIC PAGES #####

ALL_TEAMS_TABLE_KEYS = [
    'totalGamePieces',
    'autoHub',
    'autoHubMiss',
    'teleHub',
    'teleHubMiss',
]
"""List of stat keys to be used for the table on the All Teams page.

Every value in this list should correspond to a column in the MongoDB match scouting entries.
"""

STAT_SELECTOR_DEFAULTS = {
    'all_teams': 'totalGamePieces',
    'alliance_comparison_radar_chart': [ 'totalGamePieces', 'autoHub', 'teleHub' ],
    'team_comparison_radar_chart': [ 'totalGamePieces', 'autoHub', 'teleHub' ],
    'alliance_comparison_box_plot': 'totalGamePieces',
    'team_comparison_box_plot': 'totalGamePieces',
    'alliance_team_comparison': [ 'totalGamePieces', 'autoHub', 'teleHub' ],
    'niche_finder_stats': ['autoHub', 'teleHub'],
    'niche_finder_accuracies': [],
}
"""Dictionary storing a list of default selected stats for every input key.
Keys should directly correspond to values given to ``utils.stat_selector`` elements

Every value in these lists should correspond to a column in the MongoDB match scouting entries
"""

STAT_SELECTOR_FALLBACK_DEFAULT = [
    'totalGamePieces'
]
"""A fallback input value used if ``utils.stat_selector`` is passed a key not in ``stat_selector_defaults``
This should be a list with a single value in it.

This value should correspond to a column in the MongoDB match scouting entries
"""

TEAM_SUMMARY_LINE_CHART_KEYS = {
    "Overall": [
        'totalGamePieces',
    ],
    "Auto": [
        'autoHub',
        'autoHubMiss',
    ],
    "Teleop": [
        'teleHub',
        'teleHubMiss',
    ],
}
"""Dictionary holding the stat keys to display on the team summary line charts.

Each separate key in the dict will create a different tab for a different line chart.
The values in each list are the stat keys that will be rendered on each tab

Every value in this list should correspond to a column in the MongoDB match scouting entries
"""

TEAM_SUMMARY_TABLE_KEYS = {
    "Overall": [
        'totalGamePieces',
    ],
    "Auto": [
        'autoHub',
        'autoHubMiss',
    ],
    "Teleop": [
        'teleHub',
        'teleHubMiss',
    ],
}
"""Dictionary holding the stat keys to display on the team summary tables.

Each separate key in the dict will create a different tab for a different table.
The values in each list are the stat keys that will be rendered on each tab

Every value in this list should correspond to a column in the MongoDB match scouting entries
"""

# ponytail: CLIMB_KEY/CLIMB_INT_TO_TEXT and ROLE_KEY/ROLE_INT_TO_TEXT lived
# here for the 2025 game (climb + offense/defense role fields), both removed
# from the schema in 2026 (see Scouting-Scripts/2026_schema.txt). Restore
# them here, in this same GAME SPECIFIC region, if a future game brings
# equivalent fields back.
#endregion
