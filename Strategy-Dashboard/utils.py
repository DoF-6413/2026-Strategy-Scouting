import json
import math
import os
import re as regex

import config as cfg
import credentials as creds
import plotly
import plotly.graph_objects as go
import scipy.stats as stats
import streamlit as st
from pandas import DataFrame
from PIL import Image
from plotly.subplots import make_subplots
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

comp_level_keys = ["qm", "sf", "f"]

# region DATA QUERYING

@st.cache_resource(ttl=90)
def get_mongo_db () -> Database:
    """Connects to MongoDB and returns the MongoDB database. 

    Returns:
        Database: The MongoDB database
    """
    client: MongoClient = MongoClient(creds.PRIMARY_CONNECTION_STRING)
    db: Database = client[cfg.DB_NAME]

    return db

@st.cache_data(ttl=90)
def get_scouting_data() -> DataFrame:
    """Gets the data stored in the scouting collection in the MongoDB as a DataFrame. Filters the data to only include data from selected events.

    Returns:
        DataFrame: DataFrame containing the data from the MongoDB.
    """
    db: Database = get_mongo_db()
    collection = db[cfg.V5_COL_SCOUTING]

    # Convert the data to a DataFrame
    df: DataFrame = DataFrame(list(collection.find("")))

    # Filter the data to only include data from selected events
    df = df[df["eventCode"].isin(st.session_state["dataEventCodes"])]

    df["team"] = df["team"].astype(str)

    return df

@st.cache_data(ttl=90)
def get_prescouting_data() -> DataFrame:
    """Gets the data stored in the MongoDB as a DataFrame. Filters the data to only include data from selected events.

    Filters the data to only include prescouting scouting doctypes

    Returns:
        DataFrame: DataFrame containing the data from the MongoDB.
    """

    # Get the data from the MongoDB
    df: DataFrame = get_scouting_data()
    # Filter the DataFrame to only include entries where the docType is prescouting data
    df = df[df["docType"]==cfg.DT_SCOUTING_PRESCOUT]

    return df

@st.cache_data(ttl=90)
def get_match_data() -> DataFrame:
    """Gets the data stored in the MongoDB as a DataFrame. Filters the data to only include data from selected events.

    Filters the data to only include match scouting doctypes

    Returns:
        DataFrame: DataFrame containing the data from the MongoDB.
    """
    db: Database = get_mongo_db()
    collection = db[cfg.V5_COL_SCOUTING]

    # Convert the data to a DataFrame
    df: DataFrame = DataFrame(list(collection.find({
        "eventCode": {"$in": st.session_state["dataEventCodes"]},
        "docType": cfg.DT_SCOUTING_MATCH,
        "team": {"$exists": True}
    })))

    return df

@st.cache_data(ttl=600)
def get_event_schedule(event_code: str) -> list:
    """Gets the match schedule from MongoDB for an event.

    Args:
        event_code (str): The current event code to get the matches for. Normally found in ``st.session_state["currentEventCode"]``.

    Returns:
        dict: The match data for the event. `Here <https://www.thebluealliance.com/api/v3/event/2024aztem/matches>`__ is an example of the dictionary structure.
    """
    try:
        # Gets a list of match dictionaries in TBA format
        # If using random data, it will get the data from a file named "RandomDataEvent.json"
        # If using real data, it will get the data from The Blue Alliance
        if cfg.DASHBOARD_MODE == "random":
            f = open("RandomDataEvent.json", "r")
            matches: list = json.loads(f.read())

            # Generates the match keys for each match. This is ONLY for random data
            for match in matches:
                match["key"] = f'{event_code}_{match["comp_level"]}m{match["match_number"]}'
        elif cfg.DASHBOARD_MODE == "real":
            current_event_code: str = st.session_state["currentEventCode"]
            db: Database = get_mongo_db()
            collection: Collection = db.get_collection(cfg.V5_COL_MATCHES)

            matches = list(collection.find({"event_key": event_code}))

        return matches
    except:
        return None


def get_all_event_codes() -> list:
    """Gets every single event codes we have data for. 

    Returns:
        list: List of every event code in the MongoDB.
    """
    client: MongoClient = MongoClient(creds.PRIMARY_CONNECTION_STRING)
    db = client[cfg.DB_NAME]
    collection = db[cfg.V5_COL_SCOUTING]

    df: DataFrame = DataFrame(list(collection.find("")))

    if len(df) == 0:
        return []
    else:
        return df["eventCode"].unique().tolist()

#endregion

######################
######################
######################

#region GENERAL

@st.cache_data(ttl=600)
def get_event_teams(event_code: str) -> list:
    """Returns a list of all teams for the specified event code that we have data for in the MongoDB.

    Args:
        event_code (str): The event code to get the teams for.

    Returns:
        list: A list of all teams found in the data for the specified event code.
    """
    db: Database = get_mongo_db()
    col: Collection = db.get_collection(cfg.V5_COL_EVENTS)

    df: DataFrame = DataFrame(list(col.find("")))
    filtered_df = df[ (df["docType"]==cfg.DT_EVENTS_TEAMS) & (df["event_key"]==event_code) ]

    teams: list = filtered_df["team_number"].unique().astype(str).tolist()

    # Sort descending by team number
    teams.sort(key=lambda x: int(x))

    return teams

def match_key_to_dict(match_key: str) -> dict:
    """Converts a string containing a match key to a dictionary containing the event code, competition level, match number, and set number.

    Args:
        match_key (str): The match key to convert. Format should follow ``<event code>_<comp level><set number>m<match number>`` eg ``2024aztem_qm1`` or ``2024aztem_f1m1``. For quals there is no set number.

    Returns:
        dict: Dictionary containing the event code, competition level, match number, and set number. Keys are ``event_code``, ``comp_level``, ``match_number``, and ``set``, respectively.
    """
    comp_level: str = regex.search(r"qm|f|sf(?=\d+)", match_key).group()
    match_number: str = int(regex.search(r"(?<=m)\d+$", match_key).group())

    # If quals is the comp level, the set number is irrelevant
    if comp_level != "qm":
        set_number = int(regex.search(r"(?<=f)\d+(?=m)", match_key).group())
    else:
        set_number = None

    # Return a dictionary holding the match data separated
    return {
        "comp_level": comp_level,
        "match_number": match_number,
        "set_number": set_number
    }

def slope_to_trend_index(slope: float) -> int:
    """Returns a "trend index" integer from 0 to 4, where 
    - 0/1: major/minor down, 
    - 2: no significant positive or negative trend,
    - 3/4: minor/major up

    Args:
        slope (float): The slope of the trend line to convert

    Returns:
        int: The "trend index" integer.
    """
    thresholds: list = cfg.TREND_SLOPE_MAPPING

    if slope <= thresholds[0]:
        return 0
    elif slope < thresholds[1]:
        return 1
    elif slope < thresholds[2]:
        return 2
    elif slope < thresholds[3]:
        return 3
    elif slope >= thresholds[3]:
        return 4

def team_stat_five_num_summary(df: DataFrame, team: str, stat: str) -> list:
    """Generates a ``team``'s five number summary for the stat ``stat`` using data in ``df`` 

    Five number summary contains min, lower quartile, median, upper quartile, and max. 

    Args:
        df (DataFrame): The match data DataFrame to get data from.
        team (str): The team to get the five number summary for
        stat (str): The data to get the five number summary for.

    Returns:
        list: A list of five float values, which, altogether, hold the five number summary:
        - min (lowest value in the data for the stat)
        - q1 (lower quartile, or 25th percentile)
        - median 
        - q3 (upper quartile, or 75th percentile)
        - min (highest value in the data for the stat)
    """
    team_df: DataFrame = df[df["team"].astype(str) == str(team)]
    values: DataFrame = team_df[stat]

    min = float(values.min())
    q1 = float(values.quantile(0.25))
    median = float(values.quantile(0.5))
    q3 = float(values.quantile(0.75))
    max = float(values.max())

    return [min, q1, median, q3, max]

def team_stat_mean(df: DataFrame, team: str | int, stat: str) -> float:
    """Returns the mean for a stat (``stat``) by a team (``team``) in the match data DataFrame ``df``.

    Args:
        df (DataFrame): The match data DataFrame to get data from.
        team (str | int): The team to get the mean for
        stat (str): The stat to get the mean for. Should correspond to a column in ``df``

    Returns:
        float: A float holding the team's mean in a stat. Not rounded, should be rounded if it is going to be displayed directly (eg the raw value in a table)
    """
    team_df: DataFrame = df[df["team"] == str(team)]
    values: DataFrame = team_df[stat]
    return values.mean()

def get_averages_ranks(df: DataFrame, keys: list, team_averages: list) -> dict:
    """Gets the rank of averages (means) passed in ``team_averages`` relative to all other teams in the current event.

    Args:
        df (DataFrame): The global match DataFrame.
        keys (list): The stats to get ranks for. Corresponds to those in ``team_averages``.
        team_averages (list): The values to compare to the rest of the averages. Corresponds to the stats in ``keys``

    Returns:
        dict: Dict containing each stat's rank. Keys will be the same as ``keys`` and the values will be the ranks of ``team_averages``
    """
    non_nan_averages = [average for average in team_averages if not math.isnan(average)]
    rankings = dict()
    if len(non_nan_averages) > 0:
        # Constructs a base dict with each key holding an empty list
        averages: dict = {key: list() for key in keys}

        # Iterates over each team in the current event code and adds their averages to the lists in the averages dict.
        teams_list: list = get_event_teams(st.session_state["currentEventCode"])
        for team in teams_list:
            team_df: DataFrame = df[df['team'] == team]
            if len(team_df) > 0:
                # For each key, append to the corresponding key in averages the team's mean for that key.
                for key in keys:
                    averages[key].append(team_df[key].mean())

        # Sorts each key in averages in descending order. Necessary for ranking.
        for key in averages:
            averages[key] = sorted(averages[key], reverse=True)
        # Adds the teams ranking to a rankings dict, where each key holds a stat's mean
        for key in keys:
            rankings[key] = averages[key].index(team_averages[key]) + 1
    else:
        for key in keys:
            rankings[key] = "-"

    return rankings

def write_radar_chart (values: list, axes: list, trace_names: list, axes_max: int) -> None:
    """Writes a radar chart across stats for a list of data points
    
    Args:
        values (list): List of lists of values to be charted for each of the ``axes``. Each list within this list corresponds to a different trace in ``trace_names``
        axes (list): List of axes. These should be stat keys which are findable in ``cfg.stat_key_to_text``
        trace_names (list): List of names for each trace. This will generally be the alliance name or team number.
        axes_max (int): The highest value that should be used on the range for each axes. Normally 1 if graphing teams or 3 if graphing alliances

    Returns:
        None. Writes the chart directly
    """
    # if we have enough colors in cfg.default_compare_vis_colors, use those for the colors
    if len(trace_names) <= len(cfg.DEFAULT_COMPARE_GRAPH_COLORS):
        colors: list = cfg.DEFAULT_COMPARE_GRAPH_COLORS
    else:
        colors: list = plotly.colors.DEFAULT_PLOTLY_COLORS

    radar_chart = go.Figure()

    for i, trace in enumerate(trace_names):
        # Adds the trace to the radar chart for the alliance
        radar_chart.add_trace(go.Scatterpolar(
            r=values[i],                                                   # The values for each axis
            theta=axes,                                                 # The axes
            fill="toself",
            name=trace_names[i],                                        # The name of the trace for the legend and hover tooltip
            marker_color=colors[i],                                     # The color of the alliance's trace
            customdata=[trace_names[i] for x in axes],           # customdata to be used for the hovertemplate
            hovertemplate='<b>%{customdata}</b><br><br>' +              # The template of text for the hover tooltip
            '<b>%{theta}</b>: %{r}' + '<extra></extra>',
            hoverlabel=dict(                                            # Styles the hover tooltip to match the color of the alliance
                bgcolor=colors[i],
                font_color="white"
            )
        ))

    # Set the axes to all be on the scale specified in the params
    radar_chart.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, axes_max],
            )),
    )
    # Map the axes labels from stat keys to human readable text
    radar_chart.update_polars(
        angularaxis=dict(
            labelalias=dict(
                (axis, cfg.STAT_KEY_TO_TEXT[axis]) for axis in axes),
        )
    )

    # Write the chart on Streamlit
    st.plotly_chart(radar_chart)

def sort_matches(matches: list | DataFrame) -> dict:
    """ Function applied to sort matches and ensure the rounds always end up at the end. 
    
    With a pure sort based on match number, some playoff matches would be next to quals 1 since they both have match number 1
    
    Args:
        matches (list, DataFrame): Variable holding matches in one of two formats:
        - TBA format (as a list of dicts). 
        - MongoDB match scouting format (DataFrame)

    Returns:
        list/DataFrame: The matches sorted by comp level and then, within that, match number or set number, depending on the comp level
    """
    if isinstance(matches, list):
        # Map comp level value to a value that will be added to every match number in sorting
        # by adding matches length, we ensure we will always sort from quals-finals in order.
        max_match_num = max([x["match_number"] for x in matches])
        comp_level_value = {
            "qm": 0,
            "sf": max_match_num,
            "f": max_match_num*2,
        }

        # Sorts the matches
        matches.sort(key=lambda x: comp_level_value[x["comp_level"]] + (x["match_number"] if x["comp_level"]=="qm" else x["set_number"]))
        return matches
    elif isinstance(matches, DataFrame):
        # Map comp level value to a value that will be added to every match number in sorting
        # by adding matches length, we ensure we will always sort from quals-finals in order.
        comp_level_value = {
            "qm": 0,
            "sf": matches["matchNumber"].max(),
            "f": matches["matchNumber"].max()*2
        }
        matches["sortVal"] = [int(comp_level_value[row["compLevel"]]) + row["matchNumber"] for i,row in matches.iterrows()]
        # Sorts the matches
        matches = matches.groupby(by="eventCode").apply(lambda x: x.sort_values(by="sortVal", ascending=True))
        matches = matches.reset_index(drop=True)
        return matches

#endregion

######################
######################
######################

#region INPUT ELEMENTS

def input_change(session_state_key: str, temp_key: str, match_input: bool = False) -> None:
    """A callback function for when an input changes. Simply sets ``session_state_key`` to the value of ``temp_key``. 
   
    Because of the way Streamlit works, every input defines a ``key`` where the value is stored for each rerun, but only temporarily.

    If ``match_input`` is ``True``, this also update the full match key stored in the session state.

    Used as a callback by ``stat_selector``, ``team_selector``, and ``match_selector``.

    Args:
        session_state_key (str): Key in session state where the value will be stored long-term.
        temp_key (str): Key in session state where the value is stored temporarily. This is the ``key`` arg in the input.
        match_input (bool, optional): Set to ``True`` if this is being called by ``match_selector``. Defaults to ``False``.
    
    Returns:
        None. session state modified directly.
    """
    # Set the value of the new permanent key to the value of the temp key
    new_selection = st.session_state[temp_key]
    st.session_state[session_state_key] = new_selection

    # If this is a match input, update all the match data in session state.
    if match_input:
        full_match_key = regex.split("(_cl|_mn|_set)$", session_state_key)[0]

        cl = st.session_state[f"{full_match_key}_cl"]                   # The comp level
        mn = st.session_state[f"{full_match_key}_mn"]                   # The match number
        sn = st.session_state[f"{full_match_key}_set"]                  # The set number

        # If the match isn't a quals, make sure to write the set number. Otherwise, just ignore the set
        if st.session_state[f"{full_match_key}_cl"] != "qm":
            st.session_state[full_match_key] = f"{cl}{sn}m{str(mn)}"
            st.write(st.session_state[full_match_key])
        else:
            st.session_state[full_match_key] = f"qm{str(mn)}"


def stat_selector(selector_key: str, multiselect: bool, custom_label: str = None, custom_options: list = None) -> list:
    """Creates a stat selector dropdown used by the user to select stats. Returns the stat(s) selected by the user. 

    If the stat selector has been used before, it will remember the previous selection, even if the page was switched.

    Default selected stats are managed in the config under ``config.stat_selector_defaults``. If there are no default stats configured, it will use the fallback in ``config.stat_selector_fallback_default``.

    Args:
        selector_key (str): The key of the stat selector. Prefix for session storage keys where the selected stats are stored. Also used in the config for default values: ``config.stat_selector_defaults``.
        multiselect (bool): Set to ``True`` if the dropdown should allow multiple selections, or ``False`` if it should be single selection.
        custom_label (str, optional): A string representing a custom label that should be applied to the input element. Defaults to ``None``.
        custom_options (list, optional): This can be passed to give the input a special list of keys that can be selected. If not passed, the input will use the options in ``cfg.selectable_stats``

    Returns:
        list: A keys list of the selected stats. Should directly correspond to the keys in the match DataFrame.
    """
    # Stats wish to be displayed. Key with display name
    # Will normally default to cfg.selectable stats, but if a list of custom stats is passed, it will use that instead.
    selectable_stats: list = (cfg.SELECTABLE_STATS
                              if custom_options is None
                              or not isinstance(custom_options, list)
                              else custom_options)

    # Key where the selected stats are stored long-term
    session_state_key: str = f"{selector_key}_selected_stats"
    # Temporary key the input saves values to
    input_key: str = f"_{selector_key}_selected_stats_input"

    # If there's stat selections stored, set those as the selection. Otherwise, use the config default
    if session_state_key in st.session_state and st.session_state[session_state_key] != "":
        selected_stats: list = st.session_state[session_state_key]
    elif session_state_key not in st.session_state:
        selected_stats: list = cfg.STAT_SELECTOR_DEFAULTS[selector_key]
        if not selected_stats:
            selected_stats = cfg.STAT_SELECTOR_FALLBACK_DEFAULT
        st.session_state[session_state_key] = selected_stats

    # Use a Streamlit multiselect element if multiselect is True, otherwise use a Streamlit selectbox element (single selection)
    if multiselect:
        # Write the stat selector input
        st.multiselect(
            label=custom_label if custom_label is not None else "Select stats",             # The label shown above the input
            options=selectable_stats,                                                       # The options the user can select
            default=selected_stats,                                                         # Set the default stats to be selected for the dropdown
            format_func=lambda x: cfg.STAT_KEY_TO_TEXT[x],                                  # Format the options from mapping of keys -> human readable text. Uses the cfg.stat_key_to_text which stores human readable names
            key=input_key,                                                                  # A session state key where the data will be temporary stored. Note storage from this method is NOT the same as normal session state. It is TEMPORARY
            on_change=input_change, args=[session_state_key, input_key],                    # When the value of the input changes, run input_change with the params specified in args
        )
    else:
        # Write the stat selector input
        st.selectbox(
            label=custom_label if custom_label is not None else "Select stat",              # The label shown above the input
            options=selectable_stats,                                                       # The options the user can select
            index=selectable_stats.index(                                                   # Set the default stats to be selected for the dropdown
                                        selected_stats[0]
                                        if isinstance(selected_stats, list)
                                        else selected_stats),
            format_func=lambda x: cfg.STAT_KEY_TO_TEXT[x],                                  # Format the options from mapping of keys -> human readable text. Uses the cfg.stat_key_to_text which stores human readable names
            key=input_key,                                                                  # A session state key where the data will be temporary stored. Note storage from this method is NOT the same as normal session state. It is TEMPORARY
            on_change=input_change, args=[session_state_key, input_key],                    # When the value of the input changes, run input_change with the params specified in args
        )

    # Returns the keys selected as stored in the session state under session_state_key
    return st.session_state[session_state_key]


def team_selector(selector_key: str, multiselect: bool) -> list:
    """Creates a team selector dropdown used to select teams. Returns the team(s) selected by the user. 

    If the selector has been used before, it will remember the previous selection, even if the page was switched.<

    Args:
        selector_key (str): The key of the team selector. Serves as the start of session storage keys where the selected teams are stored. Should be unique to each input.
        multiselect (bool): Set to ``True`` if the dropdown should allow multiple selections, or ``False`` if it should be single selection.

    Returns:
        list: A list of team numbers for the selected teams. 
    """
    selectable_teams: list = get_event_teams(st.session_state["currentEventCode"])

    # Key where the selected teams are stored long-term
    session_state_key: str = f"{selector_key}_selected_teams"
    # Temporary key the input saves values to
    input_key: str = f"_{selector_key}_selected_teams_input"

    # If there's team selections stored, set those as the selection. Otherwise, use the config default
    if session_state_key in st.session_state and st.session_state[session_state_key] != "":
        selected_teams: list = st.session_state[session_state_key]
    else:
        selected_teams: list = [selectable_teams[0]]
        st.session_state[session_state_key] = selected_teams

    # Write the team selector element
    st.multiselect(
        label="Team Numbers" if multiselect else "Team Number",                             # The label shown above the input
        options=selectable_teams,                                                           # The options the user can select
        default=selected_teams,                                                             # Set the default teams to be selected for the dropdown
        key=input_key,                                                                      # A session_state key where the data will be temporary stored. Note storage from this method is NOT the same as normal session state. It is TEMPORARY
        on_change=input_change, args=[session_state_key, input_key],                        # When the value of the input changes, run input_change with the params specified in args
        max_selections=None if multiselect else 1
    )

    # Returns the teams selected as stored in the session state under session_state_key
    return st.session_state[session_state_key]

#endregion

######################
######################
######################

#region TEAM SUMMARY

@st.cache_data
def write_team_summaries(match_df: DataFrame, prescouting_df: DataFrame, team_numbers: list) -> None:
    """Generates a summary of the data for each team passed to the script using match data in ``match_df``.
    Every team summary contains three elements:
    - A table with an overview of the data for each stat. Stats displayed can be configured in ``config.team_summary_table_keys``.
    - A line chart showing the stats for each match. Stats displayed can be configured in ``config.team_summary_line_chart_keys``.
    - A list of comments for each match, separated by event.

    Args:
        match_df (DataFrame): DataFrame containing the scouting match data.
        prescouting_df (DataFrame): DataFrame containing the prescouting data.
        team_numbers (list): A list of team numbers to generate summaries for.

    Returns:
        None. Team summaries written directly by this function.
    """
    # List of DataFrames, each index corresponding to the team number in team_numbers
    team_match_dfs: list = [match_df[match_df["team"] == str(team_number)] for team_number in team_numbers]

    # The number of teams passed in team_numbers
    team_len: int = len(team_numbers)

    # Null check all team match dfs. If they're null, stop without proceeding
    for i, df in enumerate(team_match_dfs):
        if len(df) == 0:
            missing_team = team_numbers[i]
            st.write("No data found for team: " + str(missing_team))
            return

    ##### TEAM HEADERS ######
    # Writes the headers for the corresponding teams/headers
    with st.container():
        cols: list = st.columns(team_len)
        for i, team in enumerate(team_numbers):
            cols[i].header(team)

    if st.session_state["showImages"]:
        ##### ROBOT PHOTOS ######
        with st.container():
            cols: list = st.columns(team_len)
            for i, team in enumerate(team_numbers):
                # Try displaying the photo for the team, if it exists
                if os.path.exists(f"{cfg.ROBOT_PHOTOS_FOLDER}/{team}.{cfg.ROBOT_PHOTOS_FORMAT}"):
                    try:
                        img = Image.open(f"{cfg.ROBOT_PHOTOS_FOLDER}/{team}.{cfg.ROBOT_PHOTOS_FORMAT}")
                        cols[i].image(img)

                    except Exception as e:
                        print(f"Unexpected error occurred while loading team summary robot image: {e}")
                        continue

                # Try displaying the photo for when there's no robot image if it exists
                elif os.path.exists(f"{cfg.ROBOT_PHOTOS_FOLDER}/{cfg.NO_PHOTO_FILE_NAME}.{cfg.ROBOT_PHOTOS_FORMAT}"):
                    try:
                        img = Image.open(f"{cfg.ROBOT_PHOTOS_FOLDER}/{cfg.NO_PHOTO_FILE_NAME}.{cfg.ROBOT_PHOTOS_FORMAT}")
                        cols[i].image(img)

                    except Exception as e:
                        print(f"Unexpected error occurred while loading no image found image: {e}")
                        continue

    ##### SUMMARY TABLES #####
    with st.container():
        # Dictionary storing every table tab and then, under those keys, the stats for each table tab.
        table_key_dict: dict = cfg.TEAM_SUMMARY_TABLE_KEYS
        # Streamlit columns for each team passed
        cols: list = st.columns(team_len)

        # Loop through each team and generate the summary tables
        for i, team_num in enumerate(team_numbers):
            with cols[i]:
                team_match_df: DataFrame = team_match_dfs[i]
                if len(team_match_df) == 0:
                    st.write("No data for team " + str(team_num))
                    continue
                st.subheader("Table")

                # List of tabs each titled after the keys of table_key_dict
                tabs: list = st.tabs(table_key_dict.keys())

                # Loop through each tab and generate the summary table for each
                for j, tab in enumerate(tabs):
                    # The stats to be displayed on the table.
                    stats = table_key_dict[list(table_key_dict.keys())[j]]

                    with tab:
                        write_team_summary_table(
                            global_df=match_df,                   # The global DataFrame holding all match data
                            team_df=team_match_df,                # The team DataFrame holding just the data for the specific team
                            keys=stats                      # The stats to be displayed on the table.
                        )

    ##### LINE CHARTS #####
    with st.container():
        # Streamlit columns for each team passed
        cols = st.columns(team_len)

        for i, team_number in enumerate(team_numbers):
            with cols[i]:
                # The currently iterating teams' DataFrame.
                team_match_df: DataFrame = team_match_dfs[i]
                if len(team_match_df) == 0:
                    continue
                st.subheader("Matches")

                # Dictionary storing every chart tab and then, under those keys, the stats for each chart tab.
                chart_key_dict: dict = cfg.TEAM_SUMMARY_LINE_CHART_KEYS
                # List of tabs, each titled after the keys of table_key_dict
                tabs: list = st.tabs(chart_key_dict.keys())


                # Loop through each tab and generate the line chart for each
                for j, tab in enumerate(tabs):
                    # Every desired stat to plot on the line in this tab
                    stats: list = chart_key_dict[list(chart_key_dict.keys())[j]]
                    # The maximum value for the y-axis. This is set to the highest value in any of the teams' DataFrame. This is to ensure the y-axis is consistent across all teams' charts.
                    max_y: float = (match_df[match_df["team"].isin(team_numbers)]           # Filter the global Dataframe to teams that are in team_numbers
                                    [stats]                                     # Get only the columns for the stats in stats
                                    .max()                                      # Get the max value of each column
                                    .max()                                      # Get the max value of the column max values
                                    )

                    with tab:
                        # Write the team match line chart for the team
                        write_team_match_line_chart(
                            team_df=team_match_df,                                         # The team's DataFrame, filtered only to match entries belonging to them
                            keys=stats,                                         # The stats to use to write the line chart
                            max_y=max_y                                         # Sets the high of the y axis
                        )

    ##### Write comments #####
    with st.container():
        # Streamlit columns for each team passed
        cols: list = st.columns(team_len)

        # Loop through each team and add the comments
        for i in range(team_len):
            with cols[i]:
                team_match_df: DataFrame = team_match_dfs[i]
                team_prescouting_df: DataFrame = prescouting_df[prescouting_df["team"]==team_numbers[i]]

                if len(team_match_df) == 0:
                    continue

                # Writes the comments for the team
                write_team_comments(team_match_df, team_prescouting_df)


def write_team_summary_table(global_df: DataFrame, team_df: DataFrame, keys: list) -> None:
    """Writes the team summary table for a team.

    ``global_df`` is the full match data DataFrame, while ``team_df`` holds a DataFrame with only entries from a given team

    Args:
        global_df (DataFrame): The full match data DataFrame.
        team_df (DataFrame): DataFrame with entries filtered to the team whose data is being summarized on the table.
        keys (list): The stats to be displayed on the table

    Returns:
        None. Writes the table directly.
    """
    # Gets the mean, standard deviation, max, and rank for each stat
    averages: list = team_df[keys].mean()                           # Stat means
    sd: list = team_df[keys].std()                                  # Stat standard deviations
    maxs: list = team_df[keys].max()                                # Stat maxs
    ranks: list = get_averages_ranks(global_df, keys, averages)     # Stat ranks

    # Static variable holding the trend arrow symbols
    trend_symbols: list = [
        "↓",
        "⇣",
        "-",
        "⇡",
        "↑",
    ]
    # The "trend index" integer for each stat
    trend_indexes: list = [
        slope_to_trend_index(
            stats.linregress(
                x=team_df[key].to_list(),
                y=range(len(team_df[key].to_list()))
            )[0]
        )
        if len(team_df[key].unique()) > 1 else 2
        for key in keys
    ]
    # Convert the "trend index" integer to a symbol in trend_symbols
    trend_texts = [trend_symbols[ti] for ti in trend_indexes]

    # Write the table cell values using a DataFrame
    table_df = DataFrame(columns=keys, index=["Average", "SD", "Max", "Rank"])
    table_df.loc["Average"] = [f'{averages[i].round(2)} {trend_texts[i]}'
                               for i in range(len(sd))]
    table_df.loc["SD"] = [f"± {str(sd[i].round(2))}"
                          for i in range(len(sd))]
    table_df.loc["Max"] = maxs
    table_df.loc["Rank"] = ranks

    # Change the column labels from raw stat keys to human readable labels
    table_df.rename(columns=lambda x: cfg.STAT_KEY_TO_TEXT[x], inplace=True)

    # Function used as a callback for applymap to style the DataFrame according to trends
    def apply_trend_color(value):
        value = str(value)
        for symbol in trend_symbols:
            if symbol in value:
                return f"color: {cfg.SLOPE_COLOR_MAPPING[trend_symbols.index(symbol)]}; font-weight: bold;"
        return "color: grey;"
    # Apply the trend color to each cell of the table
    styled_df: DataFrame = table_df.style.map(
        func=apply_trend_color).format(precision=2)

    # Write the team's table
    st.dataframe(styled_df, use_container_width=True)


def write_team_match_line_chart(team_df: DataFrame, keys: list, max_y: int = None) -> None:
    """Writes the match line chart from the data in ``team_df`` in the columns ``keys``. ``team_df`` should already be team-filtered.

    If ``max_y`` is set, the y-axis will go up to ``max_y``. This is used to synchronize y-axes across side-by-side charts.

    Args:
        team_df (DataFrame): Match data DataFrame used to get the data. Should be filtered to the team desired.
        keys (list): A list of the stats to display on the line chart. Should correspond to columns in ``team_df``.
        max_y (int, optional): Set to designate the y-axis scale. Defaults to None.

    Returns:
        None. Writes the line chart directly.
    """
    # Group all match data entries by event code and sort within each event code by match number
    team_df = sort_matches(team_df)

    # The figure that the traces are added to
    fig: go.Figure = go.Figure()

    # The following lines extract a bunch of values from the DataFrame.
    # This is done they can be more easily manipulated to separate the events in the data
    match_numbers: list = team_df["matchNumber"].tolist()               # Simply a list of match numbers
    match_number_indexes: list = list(range(len(match_numbers)))        # A list of match number indexes. Necessary to normalize the step of the x-axis ticks
    comp_levels: list = team_df["compLevel"].tolist()                 # A list of comp level values
    stat_vals: list = [team_df[key].tolist() for key in keys]           # A list of lists for each stat key's values
    comments: list = team_df["comments"].tolist()                       # A list of match comments
    scouters: list = team_df["scouter"].tolist()                        # A list of values of the "scouter" field
    relays: list = team_df["relayed"].tolist()                          # A list of values of the "relayed" field
    herds: list = team_df["herded"].tolist()                            # A list of values of the "herded" field
    dieds: list = team_df["died"].tolist()                              # A list of values of the "died" field

    # Writes annotations on the line chart, marking the event code divisions if there's data for >1 event code.
    event_codes = team_df["eventCode"].unique()
    if len(event_codes) > 1:
        for i, code in enumerate(event_codes):
            # Gets the DataFrame's indexes for the first and last occurrence of the event in the data
            first_event_index: int = team_df.index[team_df["eventCode"] == code][0] + i - (0 if i == 0 else 1)
            last_event_index: int = team_df.index[team_df["eventCode"] == code][-1] + i - (0 if i == 0 else 1)

            # Adds lines at that help to visually separate data from each event
            # Line at the start of the event's data:
            fig.add_vline(
                x=int(first_event_index),
                opacity=0.2,
                annotation=dict(font_size=15, text=code, font_color="black"),
            )
            # Line at the end of the event's data:
            fig.add_vline(
                x=int(last_event_index),
                opacity=0.2,
            )
            # A rectangle that slightly shades the extent of each event's data
            fig.add_vrect(
                x0=int(first_event_index),
                x1=int(last_event_index),
                fillcolor="grey",
                opacity=0.05,
            )

            # If this isn't the first event index, we insert a None value to each of the lists
            # This provides a gap in the lines between each event code to help distinguish events
            if i != 0:
                match_numbers.insert(first_event_index, None)
                match_number_indexes.insert(first_event_index, None)
                comp_levels.insert(first_event_index, None)
                comments.insert(first_event_index, None)
                scouters.insert(first_event_index, None)
                relays.insert(first_event_index, None)
                herds.insert(first_event_index, None)
                dieds.insert(first_event_index, None)
                for j, key in enumerate(keys):
                    vals = stat_vals[j]
                    vals.insert(first_event_index, None)
                    stat_vals[j] = vals

    ##### DUMMY TRACE #####
    # Acts as a text placeholder. Displays comments, match number, and any other fields desired on hover.
    # Doesn't actually display anything directly on the graph, only on hover.
    fig.add_trace(go.Scatter(
        x=match_number_indexes,                                                                 # The x values (in this case, we use matchNumberIndexes to normalize distance between ticks)
        y=match_number_indexes,                                                                 # The y values. In this case, we just use a dummy value because the y is irrelevant to this dummy trace
        mode="text",                                                                            # Sets the mode to text to avoid odd behavior
        customdata=[                                                                            # customdata holds data per x-value that can be accessed in hovertemplate
            f'<b>{cfg.COMP_LEVEL_KEY_TO_TEXT[comp_levels[i]]} {match_num}</b><br>' +                                                   # Adds the match number
            f'<b>Comments: {comments[i]}</b><br>' +                                             # Adds the comments
            f'<b>Scouter: {scouters[i]}</b><br>' +                                              # Adds the scouter
            ("<br><b>Relayed fuel</b>" if relays[i] == 1 else "") +                             # Adds the relayed flag
            ("<br><b>Herded fuel</b>" if herds[i] == 1 else "") +                               # Adds the herded flag
            ("<br><b><span style='color:red'>DIED/DISABLED</span></b>" if dieds[i] == 1 else "") +  # Adds a warning if the robot died
            '<extra></extra>'                                                                   # Hides extra clutter around the hover tooltip that we don't want to see
            for i, match_num in enumerate(match_numbers)
            if match_num is not None
        ],
        hovertemplate='%{customdata}',                                                          # Change what data is show on hover using the customdata
        showlegend=False,                                                                       # Don't show this trace on the legend
    ))

    # Iterates over every desired statistic and adds a trace/line to the chart displaying data.
    for i, key in enumerate(keys):
        # If cfg.stat_color_mapping has specified a color associated with this stat/key, use it for the color.
        if key in cfg.STAT_COLOR_MAPPING:
            color: str = cfg.STAT_COLOR_MAPPING[key]
        else:   # Otherwise just go with the default plotly colors.
            default_colors: list = plotly.colors.DEFAULT_PLOTLY_COLORS
            color: str = default_colors[keys.index(key)]

        # Add the line for the current stat
        fig.add_trace(go.Scatter(
            x=match_number_indexes,                                     # The x values (in this case, we use matchNumberIndexes to normalize distance between ticks)
            y=stat_vals[i],                                             # the y values. Simply the column from the DataFrame under the name we are currently looping through
            name=cfg.STAT_KEY_TO_TEXT[key],                             # The name of the trace in the legend. cfg.stat_key_to_text just maps the key to a human readable name for the stat.
            mode="lines",
            customdata=[cfg.STAT_KEY_TO_TEXT[key]                       # Adds the human readable name of the stat to the customdata field. SOLELY so it can be accessed easily by hovertemplate.
                  for i in stat_vals[i]],
            hovertemplate='<i>%{customdata}</i>: %{y}<extra></extra>',  # Modify the hovertemplate to be more minimal. The extra tags hide additional clutter around the hover.
            marker_color=color                                          # Sets the color of the line
        ))

    ##### MATCH WARNINGS #####
    # Gets a list of the index of each "warning"
    # A warning just flags a concerning value such as if they died or were carded to make it pop on the line chart
    warning_match_indexes: list = [val
                                   for i, val in enumerate(match_number_indexes)
                                   if dieds[i] == 1 or cards[i] in [1, 2] ]

    # Iterates over each warning and adds a simple vertical line on the match number to flag it
    for warning in warning_match_indexes:
        fig.add_vline(
            x=warning,
            line_color="red",
            opacity=0.1,
            line_width=6
        )

    # Updates the layout and formatting of the line charts to improve the UX
    fig.update_layout(
        xaxis=dict(
            # tickvals/ticktext are set to match number and match number indexes.
            # This ensures the proper match numbers are displayed on the x-axis while maintaining a standard distance between ticks.
            tickvals=match_number_indexes,
            ticktext=match_numbers,
            title="Match Number",                                       # Titles the x-axis to "Match Number"
        ),
        yaxis=dict(
            title="Value",                                              # Titles the y-axis to "Value"
            range=[0, max_y if max_y else team_df[keys].max()],         # Sets the so the y-axis goes up to max_y, if it has been set.
        ),
        hovermode="x unified",                                          # Unifies hovering along the x-axis. Makes viewing a match of info easier.
    )

    # Gets an id value used to give every plotly_chart a unique key because otherwise Streamlit yells at you
    # For all other components, Streamlit will autogenerate unique keys, but not for plotly_chart...
    plot_id = st.session_state["teamSummaryUsedIdLen"]
    st.session_state["teamSummaryUsedIdLen"] += 1

    # Writes the chart
    st.plotly_chart(figure_or_data=fig, key="team_summary" + str(plot_id))


def write_team_comments(match_df: DataFrame, prescouting_df: DataFrame) -> None:
    """Writes the comments and prescouting for a team from data in ``team_df``

    Separates comments by event. Notes the match number and scouter for each comment.

    Args:
        match_df (DataFrame): The team's match DataFrame to write the match comments with. This is filtered to the team
        prescouting_df (DataFrame): The team's prescouting DataFrame to write the prescouting notes with. This is filtered to the team

    Returns:
        None. Writes comments directly.
    """
    # Group all match data entries by event code and sort within each event code by match number
    match_df = sort_matches(match_df)

    if len(prescouting_df) > 0:
        st.header("Pre-scouting")
        for key in prescouting_df["notes"].values[0].keys():
           st.subheader(key)
           st.write(prescouting_df["notes"].values[0][key])

    st.header("Match Comments")

    # Get a list of all events the script has data from.
    events: list = match_df["eventCode"].unique().tolist()

    # Iterate through all the events and write match comments.
    for event in events:
        st.subheader(event)

        # Filtered DataFrame holding only entries from that match
        event_filtered_team_df: DataFrame = match_df.loc[match_df["eventCode"] == event]

        # Iterates over every event and writes the comments for it, if there are any.
        for i, e in event_filtered_team_df.iterrows():
            comment = str(e["comments"])

            # If there's no comment for the match, skip it.
            if not comment or comment == "" or comment == "nan":
                continue

            match_number = e["matchNumber"]
            comp_level = e["compLevel"]
            st.write(f"**{cfg.COMP_LEVEL_KEY_TO_TEXT[comp_level]} {match_number}:** {str(comment)} ({e['scouter']})")

#endregion

######################
######################
######################

#region ALLIANCE VIEW

@st.fragment
def write_alliances_view(match_df: DataFrame, prescouting_df: DataFrame, alliances: list, alliance_names: list = None) -> None:
    """Writes information on ``alliances`` using data from ``df``. 

    Writes two separate elements. An alliance comparison if there's more than one alliance and alliances summaries per alliance.
    Alliance summary has a tab for graphs comparing the teams in the alliance and team summaries side-by-side

    Args:
        match_df (DataFrame): Match data DataFrame to get data from.
        prescouting_df (DataFrame): Prescouting DataFrame to get data from.
        alliances (list): list of lists. This is a list of teams lists, where each teams list is an alliance
        alliance_names (list, optional): The name of each alliance. Indexes should correspond to indexes in ``alliances``. If not specified, it will auto-generate alliance names using "Alliance (index of alliance)".
    
    Returns:
        None. Writes view directly.
    """
    # If there's only one alliance:
    if len(alliances) == 1:
        # Create the alliance name if there is none
        if alliance_names == None:
            alliance_names = [f"Alliance ({'/'.join(map(str, alliances[0]))})"]

        # Write the alliance summary (no need to write an alliance comparison if there's only one alliance)
        write_alliance_summaries(match_df, prescouting_df, alliances, alliance_names)
    elif len(alliances) > 1:
        # If alliance names is none, generate alliance names for all alliances.
        if alliance_names == None:
            alliance_names = [
                            f"Alliance {i + 1} ({'/'.join(map(str, alliances[i]))})"
                            for i in range(len(alliances))]

        # Write the alliance comparison graphs
        write_alliance_comparison(match_df, alliances, alliance_names)
        # Write the alliance summaries
        write_alliance_summaries(match_df, prescouting_df, alliances, alliance_names)

def write_alliance_comparison(df: DataFrame, alliances: list, alliance_names: list) -> None:
    """Writes alliance comparison graphs holding a box plot and radar chart graphing the alliances.

    Args:
        df (DataFrame): Match data DataFrame to get data from.
        alliances (list): list of lists. This is a list of teams lists, where each teams list is an alliance
        alliance_names (list): The name of each alliance. Indexes should correspond to indexes in ``alliances``

    Returns: 
        None. Writes chart directly.
    """
    st.header("Alliance Comparisons")
    # list of two Streamlit columns, one per graph
    columns: list = st.columns(2)

    # On the first column, write the box plot
    with columns[0]:
        write_alliance_compare_box_plot(df, alliances, alliance_names)

    # On the second column, write the radar chart
    with columns[1]:
        write_alliance_compare_radar_chart(df, alliances, alliance_names)

@st.fragment
def write_alliance_compare_box_plot(df: DataFrame, alliances: list, alliance_names: list) -> None:
    """Writes a box plot comparing alliances across various areas. 

    Stats are selected in this function using ``stat_selector``

    Args:
        df (DataFrame): Match data DataFrame to get data from.
        alliances (list): list of lists. This is a list of teams lists, where each teams list is an alliance
        alliance_names (list): The name of each alliance. Indexes should correspond to indexes in ``alliances``

    Returns:
        None. Writes chart directly.
    """
    # Selected stat from a stat_selector element
    selected_stat = stat_selector(
        selector_key="alliance_comparison_box_plot",
        multiselect=False,
        custom_label="Select Box Plot Stat"
    )

    # if we have enough colors in cfg.default_compare_vis_colors, use those for the colors
    if len(alliances) <= len(cfg.DEFAULT_COMPARE_GRAPH_COLORS):
        colors = cfg.DEFAULT_COMPARE_GRAPH_COLORS
    else:
        colors = plotly.colors.DEFAULT_PLOTLY_COLORS

    ##### WRITING THE CHART #####
    box_plots = go.Figure()
    for i, alliance_teams in enumerate(alliances):
        # A dict holding every team's five number summaries, where the keys are the team numbers and the values are the list of five number summaries
        # Five number summary is min, 1st quartile, median, 3rd quartile, max
        team_five_num_summaries: dict = dict()
        for team in alliance_teams:
            team_five_num_summaries[team] = team_stat_five_num_summary(df, team, selected_stat)

        # Gets the alliance-wide five number summary by adding together each element of the five number summary per team
        alliance_fns = [[], [], [], [], []]
        for j in range(5):
            alliance_fns[j] = sum([team_five_num_summaries[team][j]
                                  for team in alliance_teams])

        # Add the box plot for the alliance
        box_plots.add_trace(go.Box(
            lowerfence=[alliance_fns[0]],                   # The min
            q1=[alliance_fns[1]],                           # The first quartile
            median=[alliance_fns[2]],                       # The median
            q3=[alliance_fns[3]],                           # The third quartile
            upperfence=[alliance_fns[4]],                   # The max
            name=alliance_names[i], x=[alliance_names[i]],  # The alliance's name. Used for the legend and hover tooltip
            marker_color=colors[i],                         # The alliance's marker color
        ))

    # Update the graph layout to look nicer and label axes
    box_plots.update_layout(
        hovermode="x",                                  # Merges all hovering on the x-axis
        yaxis=dict(
            title=cfg.STAT_KEY_TO_TEXT[selected_stat],  # Sets the name of the y-axis to the stat key mapped to  human readable text
        ),
        xaxis=dict(
            title="Alliance",                           # Titles the x-axis as Alliance
            type="category"                             # category type ensures the data is set in x-axis as categories
        )
    )

    # Write the chart
    st.plotly_chart(box_plots)

@st.fragment
def write_alliance_compare_radar_chart(df: DataFrame, alliances: list, alliance_names: list) -> None:
    """Writes a radar chart comparing alliances across various areas. 

    Desired stats are selected in this function using ``stat_selector``

    Args:
        df (DataFrame): Match data DataFrame to get data from.
        alliances (list): list of lists. This is a list of teams lists, where each teams list is an alliance
        alliance_names (list): The name of each alliance. Indexes should correspond to indexes in ``alliances``

    Returns:
        None. Writes chart directly.
    """
    # List of selected stats from a stat_selector element
    selected_stats = stat_selector(
        selector_key="alliance_comparison_radar_chart",
        multiselect=True,
        custom_label="Select Radar Stats"
    )


    # List of lists of every alliance's normalized mean
    all_normalized_means: list = list()
    # Iterate over every alliance and add their list of normalized means to the broader list
    for i, alliance_teams in enumerate(alliances):
        # normalized_means holds a list of values representing the alliances' mean in each stat normalized on a scale of 0-3 (0-1 per team)
        # Team means are normalized with the formula (<team mean> / <highest team mean>) for each stat
        # Alliance normalized means comes from the sum of all normalized team means
        alliance_normalized_means = list()
        for stat in selected_stats:
            every_mean: list = [team_stat_mean(df, team, stat)
                          for team in df["team"].unique()]
            alliance_team_means: list = [team_stat_mean(
                df, team, stat) for team in alliance_teams]
            team_means_normalized: list = [
                mean / max(every_mean) if mean > 0 else 0 for mean in alliance_team_means]
            alliance_normalized_means.append(sum(team_means_normalized))
        all_normalized_means.append(alliance_normalized_means)

    # Writes the radar chart
    write_radar_chart(
        values=all_normalized_means,
        axes=selected_stats,
        trace_names=alliance_names,
        axes_max=3
    )


@st.fragment
def write_alliance_summaries(match_df: DataFrame, prescouting_df: DataFrame, alliances: list, alliance_names: list) -> None:
    """Writes information on alliances. This will always write comparison charts and alliance summaries holding team summaries and team comparison graphs in the alliance.

    Args:
        match_df (DataFrame): Match data DataFrame to get data from.
        prescouting_df (DataFrame): Prescouting data DataFrame to get data from.
        alliances (list): list of lists. This is a list of teams lists, where each teams list is an alliance
        alliance_names (list): The name of each alliance. Indexes should correspond to indexes in ``alliances``.
    
    Returns:
        None. Writes the summaries directly.
    """
    st.header("Alliance Summaries")
    # List of selected stats from a stat_selector element
    selected_stats = stat_selector(
        selector_key="alliance_team_comparison",
        multiselect=True
    )

    # Iterate over every alliance and write their box plots and team summaries
    for index, teams in enumerate(alliances):
        st.subheader(alliance_names[index])
        # Writes the two tabs for charts and team summaries
        charts_tab, summaries_tab = st.tabs(
            ["Alliance Charts", "Team Summaries"])

        ##### ALLIANCE SUMMARY CHARTS #####
        with charts_tab:
            # The number of columns that should be side by side for the charts
            col_num: int = 3
            # The selected stats length is less than the column number, just use the selected stats length for the column number
            if len(selected_stats) < col_num:
                col_num = len(selected_stats)

            # Number of graph rows. Should be stats / columns rounded up
            rows = math.ceil(len(selected_stats) / col_num)

            # Makes subplots for the graphs
            fig = make_subplots(
                rows=rows, cols=col_num, subplot_titles=selected_stats, horizontal_spacing=0.4/col_num)

            # if we have enough colors in cfg.default_compare_vis_colors, use those for the colors
            if len(teams) <= len(cfg.DEFAULT_COMPARE_GRAPH_COLORS):
                colors: list = cfg.DEFAULT_COMPARE_GRAPH_COLORS
            else:
                colors: list = plotly.colors.DEFAULT_PLOTLY_COLORS

            # max_ys holds the highest y-value for every stat.
            max_ys: list = list()

            # Iterate over each selected stat and create a box plot for it
            for stat in selected_stats:
                # Manually setting index because it should start at 1
                index: int = selected_stats.index(stat) + 1

                # The row and column for the current stat's graph
                # Because we are using subplots, plotly formats the graphs as a grid with row and column indexes
                row: int = math.ceil(index / col_num)
                col: int = index % col_num if index % col_num > 0 else col_num

                # Loop through the teams and add a trace for each one
                for i, team in enumerate(teams):
                    # The DataFrame holding the data filtered to the currently iterating team.
                    team_df: DataFrame = match_df[match_df["team"] == str(team)]

                    # Adds the box plot for the current team and stat
                    fig.add_trace(
                        go.Box(
                            x=team_df["team"],                          # x-axis values should be the team number
                            y=team_df[stat],                            # y-axis values should be the stat's values
                            name=team,                                  # The name of the trace is the team number
                            marker_color=colors[i],                     # The color of the team's box plot
                            showlegend=False if index > 1 else True     # Only write to the legend for the first plot to avoid repeat names in the legend
                        ),
                        row=row, col=col,                               # Sets the row and column to write the box plot subplot to
                    )
                    # For the current row and column, set the y-axis title to the stat key mapped to a human readable text
                    fig.update_yaxes(
                        title_text=cfg.STAT_KEY_TO_TEXT[stat],
                        row=row, col=col
                    )
                    # Set the title of the x-axis to Team and group x-axis values in category mode
                    fig.update_xaxes(title_text="Team", type="category")

                    # Append the team's highest value of the stat to max_ys
                    max_ys.append(team_df[stat].max())
                # Set the y-axis range for all graphs to go to the highest max_ys value.
                # We do this so graphs can be directly compared side-by-side with the same y-axis
                fig.update_yaxes(range=[0, max(max_ys) + 2])

                # Set the height of the total graph grid
                fig.update_layout(height=450 * rows)

            # Write the graphs to Streamlit
            st.plotly_chart(fig)

        # Write the summaries for the teams of the alliance on the summaries tab
        with summaries_tab:
            write_team_summaries(match_df, prescouting_df, teams)
