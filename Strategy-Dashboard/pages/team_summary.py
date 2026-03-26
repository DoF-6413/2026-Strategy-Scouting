import config as cfg
import plotly
import plotly.graph_objects as go
import streamlit as st
import utils
from pandas import DataFrame


@st.fragment
def write_team_compare_box_plot(df: DataFrame, teams: list) -> None:
    """Writes a box plot comparing teams on a chosen stat. 

    The desired stat is selected in this function using ``utils.stat_selector``

    Args:
        df (DataFrame): Match data DataFrame to get data from.
        teams (list): List of team numbers to display on the graph

    Returns:
        None. Writes chart directly.
    """
    # Selected stat from a stat_selector element
    selected_stat = utils.stat_selector(
        selector_key="team_comparison_box_plot",
        multiselect=False,
        custom_label="Select Box Plot Stat"
    )

    # if we have enough colors in cfg.default_compare_vis_colors, use those for the colors
    if len(teams) <= len(cfg.DEFAULT_COMPARE_GRAPH_COLORS):
        colors = cfg.DEFAULT_COMPARE_GRAPH_COLORS
    else:
        colors = plotly.colors.DEFAULT_PLOTLY_COLORS

    ##### WRITING THE CHART #####
    box_plots = go.Figure()
    # Add a box plot for each team for the stat
    for team in teams:
        box_plots.add_trace(go.Box(
            y=df[df["team"] == team][selected_stat],    # The y-axis values should be those of the team's stat values
            x=df[df["team"] == team]["team"],           # The x-axis values is just the team number to group together
            name=team,                                  # The name of the trace (shown in legend and hover) is the team number
            marker_color=colors[teams.index(team)],     # The color of the team's box plot
        ))

    # Set the title of the y-axis to the stat key mapped to a human readable label
    box_plots.update_yaxes(title_text=cfg.STAT_KEY_TO_TEXT[selected_stat])
    # Set the title of the x-axis to Team and group all data in category mode
    box_plots.update_xaxes(title_text="Team", type="category")

    # Write the box plots
    st.plotly_chart(box_plots)

@st.fragment
def write_team_compare_radar_chart(df: DataFrame, teams: list) -> None:
    """Writes a radar chart comparing teams across various areas. 

    Desired stats are selected in this function using ``utils.stat_selector``

    Args:
        df (DataFrame): Match data DataFrame to get data from.
        teams (list): List of team numbers to display on the graph

    Returns:
        None. Writes chart directly.
    """
    # List of selected stats from a stat_selector element
    selected_stats = utils.stat_selector(
        selector_key="team_comparison_radar_chart",
        multiselect=True,
        custom_label="Select Radar Stats"
    )

    # List of lists of every team's normalized mean
    all_normalized_means: list = list()
    # Iterate over every team and add their list of normalized means to the broader list
    for team in teams:
        # normalized_means holds a list of values representing the teams' mean in each stat normalized on a scale of 0-1
        # Team means are normalized with the formula (<team mean> / <highest team mean>) for each stat
        team_normalized_means: list = list()
        for stat in selected_stats:
            all_means = [utils.team_stat_mean(df, team, stat)
                         for team in df["team"].unique()]
            mean = utils.team_stat_mean(df, team, stat)
            normalized_mean = mean / max(all_means) if mean > 0 else 0
            team_normalized_means.append(normalized_mean)
        all_normalized_means.append(team_normalized_means)

    # Write the radar chart
    utils.write_radar_chart(
        values=all_normalized_means,
        axes=selected_stats,
        trace_names=teams,
        axes_max=1
    )


def main ():
    # Write the page title
    st.title("Team Summaries")

    # List of team numbers selected for summary
    team_numbers: list = utils.team_selector("team_summary", True)

    # Don't proceed if no teams have been selected
    if team_numbers == None or len(team_numbers) == 0:
        st.write("Select a team to view a summary of their data.")
        return

    # Gets the DataFrames for the match data and the prescouting data
    match_df = utils.get_match_data()
    prescouting_df = utils.get_prescouting_data()

    # If there's more than one team selected, write graphs to compare them
    if len(team_numbers) > 1:
        # Write a header noting this is team comparisons
        st.header("Team Comparison")

        # On separate columns, write box plots and a radar chart to compare the selected teams with.
        cols: list = st.columns(2)
        with cols[0]:
            write_team_compare_box_plot(match_df, team_numbers)
        with cols[1]:
            write_team_compare_radar_chart(match_df, team_numbers)

    # Write the team summaries for the selected teams
    utils.write_team_summaries(match_df, prescouting_df, team_numbers)

main()
