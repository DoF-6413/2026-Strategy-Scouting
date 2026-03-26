import config
import config as cfg
import pandas as pd
import plotly.express as px
import scipy.stats as stats
import streamlit as st
import utils
from pandas import DataFrame
from streamlit_plotly_events import plotly_events


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

    if last_matches_selection == "All Matches":
        # Calculate medians for each team
        medians = df.groupby('team')[key].median().reset_index()
    elif last_matches_selection == "Last Three Matches":
        # Calculate medians for each team
        medians = df.groupby('team')[key].apply(lambda x: x.tail(3).median()).reset_index()
    elif last_matches_selection == "Last Five Matches":
        # Calculate medians for each team
        medians = df.groupby('team')[key].apply(lambda x: x.tail(5).median()).reset_index()

    # Sort teams based on medians
    medians = medians.sort_values(by=key, ascending=False)
    team_order = medians['team'].tolist()

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

        color = cfg.SLOPE_COLOR_MAPPING[utils.slope_to_trend_index(slope) if slope is not None else 2]

        team_df["trend"] = color # Add the color to the trend column
        box_df = pd.concat([box_df, team_df], ignore_index=True)

    # Creates a color map necessary for plotly. Plotly can't just take the color param, it needs a color_discrete_map
    used_trend_colors = box_df["trend"].unique()
    color_map = {used_trend_colors[i]: used_trend_colors[i] for i in range(len(used_trend_colors))}

    # Write the box plot
    fig = px.box(
        data_frame=box_df,                      # Provides a DataFrame to get data for the chart from
        x="team",                               # Column in the DataFrame (box_df) storing the x-axis values
        y=key,                                  # Column in the DataFrame (box_df) storing the y-axis values
        color="trend",                          # Column in the DataFrame (box_df) storing the color values
        color_discrete_map=color_map,           # Maps color keys from the "colors" field to actual colors
        category_orders={'team': team_order}    # Orders box plots according to the team_order
    )
    fig.update_layout(
        xaxis=dict(
            title="Team",                       # Label x-axis as "Team"
            type="category",                    # Group the teams in category mode
        ),
        yaxis_title=cfg.STAT_KEY_TO_TEXT[key],  # Labels y-axis according to the stat key mapped to human readable text
        hovermode="closest",                    # Show the hover menu for the closest box
        showlegend=False,                       # Hide the legend
        boxmode="overlay"                       # setting the boxmode to overlay fixes a display bug where all the boxes are extremely thin
    )

    # An event holding all selections on the box plot
    chart_click_event: list = plotly_events(fig, click_event=True)
    if chart_click_event:
        # Value of the selection on the x-axis (aka team number)
        selected_team = chart_click_event[0]['x']
        # Set the selected team in the session state to the selected team.
        # This will modify the Team Summary input directly
        st.session_state["team_summary_selected_teams"] = [selected_team]
        # Switch page to the team summary
        st.switch_page("pages/team_summary.py")

def main():
    st.title("All Teams")
    st.write("Click on a box plot to open the team's summary.")

    # Get the DataFrame holding the match data from the MongoDB
    df = utils.get_match_data()

    event_teams = utils.get_event_teams(st.session_state["currentEventCode"])
    filtered_teams = [team for team in event_teams if len(df[df["team"]==team]) > 0]

    df = df[df["team"].isin(filtered_teams)]

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
        # Sets the value of the Team column to the team number
        team_row["Team"] = str(team)
        # Iterate over every key in table_keys and add a column to the table with it
        for key in table_keys:
            mean = team_df[key].mean().round(2)    # Gets the team's mean in the stat rounded to two decimal points
            team_row[config.STAT_KEY_TO_TEXT[key]] = mean       # Adds a column to the row with the value of the mean. The column name is the stat key mapped to a human readable label
        # Add the team's row to the end of the table
        table_df = pd.concat([table_df, pd.DataFrame([team_row])], ignore_index=True)

    # Sort the table using the values in the first column
    table_df = table_df.sort_values(by=config.STAT_KEY_TO_TEXT[table_keys[0]], ascending=False)

    # Write the table
    # table_event stores the currently selected row(s) in the DataFrame
    table_event = st.dataframe(
        data=table_df,                  # DataFrame to write the table with
        height=1000,                    # The height of the table. Here it's just a large number because the table should fill the rest of the page
        use_container_width=True,       # Use all the available width in the container
        hide_index=True,                # Hide the DataFrame's index
        on_select="rerun",              # When a row of the DataFrame is selected, rerun the page
        selection_mode="single-row",    # Only allow one row to be selected
    )

    # Process selected rows to bring up the Team Summary for a selected team
    if len(table_event.selection["rows"]):
        selected_row = table_event.selection["rows"][0]
        # Set the selected team in the Team Summary to the team who's row was selected
        # This modifies the Team Summary input directly
        st.session_state["team_summary_selected_teams"] = [table_df.iloc[selected_row]["Team"]]
        # Opens the Team Summary page
        st.switch_page("pages/team_summary.py")


main()
