import config
import config as cfg
import pandas as pd
import plotly.express as px
import scipy.stats as stats
import streamlit as st
import utils
from pandas import DataFrame


@st.fragment
def box_plots (df: DataFrame) -> None:
    """ Writes a box plot where the x axis is the team number and the y is the value of the desired key. The boxes will be colored according to the trend in the data
    
    Args:
        df (DataFrame): The match entries DataFrame
    
    Returns:
        None. Writes chart directly.
    """
    cols = st.columns(2)
    with cols[0]:
        key = utils.stat_selector("all_teams", False)

    with cols[1]:
        pills_session_state_key = "use_last_matches"
        pills_session_state_input_temp = "_use_last_matches_input"
        if pills_session_state_key in st.session_state:
            selected_pill = st.session_state[pills_session_state_key]
        else:
            selected_pill = "All Matches"
            st.session_state[pills_session_state_key] = selected_pill
        last_matches_selection = st.pills(
            label="Use data from",
            options=["All Matches",  "Last Five Matches", "Last Three Matches"],
            default=selected_pill,
            selection_mode="single",
            key=pills_session_state_input_temp,
            on_change=utils.input_change, args=[pills_session_state_key, pills_session_state_input_temp]
            )

    # st.pills with selection_mode="single" returns None if the already-selected
    # pill is clicked again (it toggles off). Treat that the same as "All Matches"
    # instead of leaving the data-selection branches below unmatched.
    if last_matches_selection is None:
        last_matches_selection = "All Matches"

    # dropna() before median() so a team with no (or all-NaN) values for this stat
    # doesn't trigger numpy's "Mean of empty slice" RuntimeWarning, which its
    # nanmedian implementation emits internally for an all-NaN slice.
    if last_matches_selection == "All Matches":
        # Calculate medians for each team
        medians = df.groupby('team')[key].apply(lambda x: x.dropna().median()).reset_index()
    elif last_matches_selection == "Last Three Matches":
        # Calculate medians for each team
        medians = df.groupby('team')[key].apply(lambda x: x.tail(3).dropna().median()).reset_index()
    elif last_matches_selection == "Last Five Matches":
        # Calculate medians for each team
        medians = df.groupby('team')[key].apply(lambda x: x.tail(5).dropna().median()).reset_index()

    # Sort the x-axis by team number (ascending) so a specific team is easy to
    # find in the chart. Unlike the table below, there's no need for a
    # stat-based sort order here.
    team_order = sorted(medians['team'].tolist(), key=int)

    # Add the trend colors to the box plots
    box_df = DataFrame()
    for team in df["team"].unique():
        team_df: DataFrame = df[df["team"]==team]
        # Sorts the values in the team df by the match number so the trend is accurate
        team_df = utils.sort_matches(team_df)
        if last_matches_selection == "Last Three Matches":
            team_df = team_df.tail(3)
        if last_matches_selection == "Last Five Matches":
            team_df = team_df.tail(5)
        values = list(team_df[key]) # Get every value of the desired key
        slope = (stats.linregress(list(range(1, len(values) + 1)), values)[0] if len(values) > 1 else 0) #Get the slope of the trend

        trend_index = utils.slope_to_trend_index(slope) if slope is not None else 2

        team_df["trend"] = cfg.SLOPE_LABEL_MAPPING[trend_index] # Add the trend label to the trend column
        box_df = pd.concat([box_df, team_df], ignore_index=True)

    # Maps each trend label to its color for the legend/boxes. Built from the
    # full label list (not just labels present in box_df) so the legend
    # always uses a consistent color-to-label mapping.
    color_map = dict(zip(cfg.SLOPE_LABEL_MAPPING, cfg.SLOPE_COLOR_MAPPING))

    # Write the box plot
    fig = px.box(
        data_frame=box_df,                                       # Provides a DataFrame to get data for the chart from
        x="team",                                                # Column in the DataFrame (box_df) storing the x-axis values
        y=key,                                                   # Column in the DataFrame (box_df) storing the y-axis values
        color="trend",                                           # Column in the DataFrame (box_df) storing the color values
        color_discrete_map=color_map,                            # Maps trend labels to colors
        category_orders={'team': team_order, 'trend': cfg.SLOPE_LABEL_MAPPING}    # Orders box plots/legend
    )
    fig.update_layout(
        xaxis=dict(
            title="Team",                       # Label x-axis as "Team"
            type="category",                    # Group the teams in category mode
        ),
        yaxis_title=cfg.STAT_KEY_TO_TEXT[key],  # Labels y-axis according to the stat key mapped to human readable text
        hovermode="closest",                    # Show the hover menu for the closest box
        legend_title_text="Trend",              # Label the legend explaining the box colors
        legend=dict(
            orientation="h",                    # Lay the legend out horizontally...
            yanchor="top",
            y=-0.15,                            # ...and place it below the plot area instead of
            xanchor="center",                   # crowding the right side, which matters most at
            x=0.5,                              # large events with many teams on the x-axis.
        ),
        boxmode="overlay"                       # setting the boxmode to overlay fixes a display bug where all the boxes are extremely thin
    )

    # Use Streamlit's native plotly_chart selection support instead of the
    # unmaintained streamlit_plotly_events package, which vendors its own
    # frozen, years-old copy of Plotly.js in its frontend build. That old JS
    # doesn't correctly render figures generated by newer plotly.py (box
    # traces with categorical x-axes ended up with some teams' boxes showing
    # data that didn't match their own row in the table below). st.plotly_chart
    # renders with the plotly.js version matching the installed plotly
    # package, so there's no such mismatch.
    chart_event = st.plotly_chart(fig, on_select="rerun", selection_mode="points")
    if chart_event and chart_event.selection["points"]:
        # Value of the selection on the x-axis (aka team number)
        selected_team = chart_event.selection["points"][0]["x"]
        # Set the selected team in the session state to the selected team.
        # This will modify the Team Summary input directly
        st.session_state["team_summary_selected_teams"] = [selected_team]
        # Switch page to the team summary
        st.switch_page("dashboard_pages/team_summary.py")

def main():
    st.title("All Teams")
    st.write("Click on a box plot to open the team's summary.")

    # Get the DataFrame holding the match data from the MongoDB
    df = utils.get_match_data()

    if df.empty:
        st.info("No scouting data found yet for the selected event(s).")
        return

    event_teams = utils.get_event_teams(st.session_state["currentEventCode"])
    if len(event_teams) == 0:
        st.warning(
            "No registered teams found for this event. Run the \"Get Event Teams "
            "Simple\" tool (Tools/get_event_teams_simple_2025_v1.py) for this event "
            "code, then reload this page."
        )
        return
    filtered_teams = [team for team in event_teams if len(df[df["team"]==team]) > 0]

    df = df[df["team"].isin(filtered_teams)]

    if df.empty:
        st.info("No scouting data found yet for teams registered at the selected event(s).")
        return

    # Writes box plots for the teams using the match DataFrame
    box_plots(df)

    ##### TABLE #####
    st.write("Click on the grey area to the left of a row to open up the team's summary.")

    # Separate DataFrame which holds the information that will be written to the displayed table
    table_df = pd.DataFrame()
    # Gets the desired keys/columns to display on the table
    table_keys = config.ALL_TEAMS_TABLE_KEYS

    # Calculate the mean of the each of the table_keys for each team
    for team in filtered_teams:
        team_df = df[df["team"]==team]
        if len(team_df) == 0:
            continue

        team_row = dict()
        # Sets the value of the Team column to the team number as an int so
        # clicking the column header sorts numerically instead of
        # alphabetically (which would put "60" after "1101").
        team_row["Team"] = int(team)
        # Iterate over every key in table_keys and add a column to the table with it
        for key in table_keys:
            mean = round(team_df[key].mean(), 2)    # Gets the team's mean in the stat rounded to two decimal points
            team_row[config.STAT_KEY_TO_TEXT[key]] = mean       # Adds a column to the row with the value of the mean. The column name is the stat key mapped to a human readable label
        # Add the team's row to the end of the table
        table_df = pd.concat([table_df, pd.DataFrame([team_row])], ignore_index=True)

    # TODO: This table (like the ones on Niche Finder and Defense) initially
    # sorts descending by its primary displayed stat column (here, whichever
    # stat is first in table_keys, e.g. "Total Game Pieces"), so a user has to
    # manually re-sort by Team every time to browse teams in order. Consider
    # defaulting all team-number tables to ascending Team order for better
    # UX, with the stat sort as something the user opts into via the column
    # header.
    # Sort the table using the values in the first column
    table_df = table_df.sort_values(by=config.STAT_KEY_TO_TEXT[table_keys[0]], ascending=False)

    # TODO: Header text is left-aligned and value text is right-aligned in
    # this table, which some find hard to read (would prefer centered).
    # st.dataframe renders as a canvas-based grid (glide-data-grid), so CSS
    # can't restyle its cells, and released column_config classes (as of
    # Streamlit 1.55) don't expose a text-alignment option yet, though one is
    # in Streamlit's PR backlog. Revisit once that ships, or switch to a
    # custom HTML table (which would drop row-click-to-open-Team-Summary and
    # native column-header sorting) if centering is needed sooner.
    # Write the table
    # table_event stores the currently selected row(s) in the DataFrame
    table_event = st.dataframe(
        data=table_df,                  # DataFrame to write the table with
        height=1000,                    # The height of the table. Here it's just a large number because the table should fill the rest of the page
        width="stretch",                # Use all the available width in the container
        hide_index=True,                # Hide the DataFrame's index
        on_select="rerun",              # When a row of the DataFrame is selected, rerun the page
        selection_mode="single-row",    # Only allow one row to be selected
    )

    # Process selected rows to bring up the Team Summary for a selected team
    if len(table_event.selection["rows"]):
        selected_row = table_event.selection["rows"][0]
        # Set the selected team in the Team Summary to the team who's row was selected
        # This modifies the Team Summary input directly.
        # Select the "Team" column first, then index into it, rather than
        # table_df.iloc[selected_row]["Team"] - .iloc[row] pulls a whole row
        # across mixed dtypes (int Team + float stat columns), which pandas
        # silently promotes to a common float dtype (e.g. 60 -> 60.0),
        # producing a team string ("60.0") that doesn't match any option in
        # the Team Summary selector and crashes it.
        st.session_state["team_summary_selected_teams"] = [str(table_df["Team"].iloc[selected_row])]
        # Opens the Team Summary page
        st.switch_page("dashboard_pages/team_summary.py")


main()
