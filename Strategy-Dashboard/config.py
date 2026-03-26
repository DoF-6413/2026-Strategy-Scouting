DASHBOARD_MODE = "real"
"""The mode the dashboard is running in. Used to choose whether to get random data or the real TBA/scouting data. 

Possible options: "random" or "real" 
"""

##### DATABASE CONFIG #####
#region DATABASE CONFIG

DB_NAME = "frc_data"
"""The database for scouting data in the MongoDB"""

V5_COL_SCOUTING = "scouting"
"""The collection for the scouting data in the database"""

V5_COL_EVENTS = "events"
"""The collection for the events data in the database"""

V5_COL_SCHEDULE = "schedule"
"""The collection for the match schedules in the database"""

V5_COL_MATCHES = "matches"
"""The collection for the event matches in the database"""

DT_SCOUTING_PRESCOUT = "prescout"
"""The docType value for prescouting entries in the database"""

DT_SCOUTING_MATCH = "match"
"""The docType value for match scouting entries in the database"""

DT_EVENTS_TEAMS = "teams"
"""The docType value for teams entries in the database"""

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

SELECTABLE_STATS = [
    'totalGamePieces',
    'totalCoral',
    'totalAlgae',
    'didClimb',
    'totalAutoCoral',
    'totalAutoAlgae',
    'totalL4',
    'totalL3',
    'totalL2',
    'totalL1',
    'totalNet',
    'totalProcessor',
    'autoL4',
    'autoL3',
    'autoL2',
    'autoL1',
]
"""List containing all standard stats selectable by stat_selector inputs. 

Every value in this list should correspond to a column in the MongoDB match scouting entries
"""

SELECTABLE_ACCURACY_KEYS = [
    'totalCoralAccuracy',
    'totalAlgaeAccuracy',
    'totalL1Accuracy',
    'totalL2Accuracy',
    'totalL3Accuracy',
    'totalL4Accuracy',
    'totalNetAccuracy',
    'totalAutoCoralAccuracy',
    'totalAutoAlgaeAccuracy',
]
"""List containing stats that are accuracies. Used for stat_selectors when we only want the user to select accuracy stats

Every value in this list should correspond to a column in the MongoDB match scouting entries
"""

STAT_KEY_TO_TEXT = {
    'totalGamePieces': 'Total Game Pieces',
    'totalCoral': 'Total Coral',
    'totalAlgae': 'Total Algae',
    'didClimb': 'Climb Rate',
    'totalL4': 'L4',
    'totalL3': 'L3',
    'totalL2': 'L2',
    'totalL1': 'L1',
    'totalNet': 'Net',
    'totalAutoCoral': 'Total Coral (Auto)',
    'totalAutoAlgae': 'Total Algae (Auto)',
    'totalCoralAccuracy': "Coral Accuracy",
    'totalAlgaeAccuracy': "Algae Accuracy",
    'totalL1Accuracy': 'L1 Accuracy',
    'totalL2Accuracy': 'L2 Accuracy',
    'totalL3Accuracy': 'L3 Accuracy',
    'totalL4Accuracy': 'L4 Accuracy',
    'totalNetAccuracy': 'Net Accuracy',
    'totalAutoCoralAccuracy': 'Coral Accuracy (Auto)',
    'totalAutoAlgaeAccuracy': 'Algae Accuracy (Auto)',
    'totalProcessor': 'Processor',
    'totalCoralMiss': 'Coral Misses',
    'totalAlgaeMiss': 'Algae Misses',
    'autoL4': 'L4 (Auto)',
    'autoL3': 'L3 (Auto)',
    'autoL2': 'L2 (Auto)',
    'autoL1': 'L1 (Auto)',
    'autoNet': 'net (Auto)',
    'autoProcessor': 'Processor (Auto)',
    'teleL4': 'L4 (Teleop)',
    'teleL3': 'L3 (Teleop)',
    'teleL2': 'L2 (Teleop)',
    'teleL1': 'L1 (Teleop)',
    'teleNet': 'Net (Teleop)',
    'teleProcessor': 'Processor (Teleop)',
    'climb': 'Climb',
}
"""Dictionary mapping stat keys as specified in the database to human readable text"""

STAT_COLOR_MAPPING = {
    'totalGamePieces': 'black',
    'totalCoral': 'coral',
    'totalAlgae': 'green',
    'totalL4': 'darkblue',
    'totalL3': 'royalblue',
    'totalL2': 'cornflowerblue',
    'totalL1': 'lightblue',
    'totalProcessor': 'greenyellow',
    'totalNet': 'forestgreen',
    'totalMiss': 'firebrick',
    'totalCoralMiss': 'indianred',
    'totalAlgaeMiss': 'olive',
    'totalCoralAccuracy': "violet",
    'totalAlgaeAccuracy': "purple",
}
"""Dictionary mapping stat keys as specified in the database to colors so traces roughly align with the desired stat."""

##### CONFIGURATIONS FOR SPECIFIC PAGES #####

ALL_TEAMS_TABLE_KEYS = [
    'totalCoral',
    'totalAlgae',
    'didClimb',
    'totalAutoCoral',
    'totalAutoAlgae',
]
"""List of stat keys to be used for the table on the All Teams page.

Every value in this list should correspond to a column in the MongoDB match scouting entries.
"""

STAT_SELECTOR_DEFAULTS = {
    'all_teams': 'totalGamePieces',
    'alliance_comparison_radar_chart': [ 'totalGamePieces', 'totalCoral', 'totalAlgae', 'didClimb' ],
    'team_comparison_radar_chart': [ 'totalGamePieces', 'totalCoral', 'totalAlgae', 'didClimb' ],
    'alliance_comparison_box_plot': 'totalGamePieces',
    'team_comparison_box_plot': 'totalGamePieces',
    'alliance_team_comparison': ['totalGamePieces', 'totalCoral', 'totalAlgae', 'didClimb' ],
    'niche_finder_stats': ['totalL4', 'totalNet'],
    'niche_finder_accuracies': ['totalL4Accuracy', 'totalNetAccuracy'],
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
        'totalCoral',
        'totalAlgae',
    ],
    "Coral": [
        'totalL1',
        'totalL2',
        'totalL3',
        'totalL4',
    ],
    "Algae": [
        'totalNet',
        'totalProcessor',
    ]
}
"""Dictionary holding the stat keys to display on the team summary line charts.

Each separate key in the dict will create a different tab for a different line chart. 
The values in each list are the stat keys that will be rendered on each tab

Every value in this list should correspond to a column in the MongoDB match scouting entries
"""

TEAM_SUMMARY_TABLE_KEYS = {
    "Overall": [
        'totalCoral',
        'totalAlgae',
        'didClimb',
    ],
    "Coral": [
        'totalL1',
        'totalL2',
        'totalL3',
        'totalL4',
    ],
    "Algae": [
        'totalAlgae',
        'totalNet',
    ],
}
"""Dictionary holding the stat keys to display on the team summary tables.

Each separate key in the dict will create a different tab for a different table. 
The values in each list are the stat keys that will be rendered on each tab

Every value in this list should correspond to a column in the MongoDB match scouting entries
"""

CLIMB_KEY = "climb"
"""The key used in the MongoDB match entries where the climb integer is stored"""

CLIMB_INT_TO_TEXT = [
    "Did not attempt",
    "Shallow",
    "Deep",
    "Failed"
]
"""Holds a list of text values where every index corresponds to a value of climb int"""

ROLE_KEY = "role"
"""The key used in the MongoDB match entries where the role integer is stored"""

ROLE_INT_TO_TEXT = [
    "Offense",
    "Defense",
    "None"
]
"""Holds a list of text values where every index corresponds to a value of role int"""
#endregion
