import config as cfg
import streamlit as st
import utils
from pandas import DataFrame


def color_team_matches(v: any) -> str | None:
    """Highlights cells in the match schedule where the value is 6413

    Args:
        v (any): Cell value of DataFrame

    Returns:
        A string with a style in it if 6413 was the cell value OR `None` otherwise
    """
    return f"background-color: {'gold'};" if str(v)=="6413" else None


def get_schedule_table(matches: list) -> DataFrame:
    """Gets a table storing match schedule

    Table columns are Match number/text, three red team columns, and three blue team columns.

    Args:
        matches (list): List holding matches in TBA format (dicts).

    Returns:
        DataFrame: The table holding the match schedule.
    """
    table_df: DataFrame = DataFrame(columns=["Match", "Red 1", "Red 2", "Red 3", "Blue 1", "Blue 2", "Blue 3", "Key"])

    sorted_matches = utils.sort_matches(matches)

    # Iterate over each match and add a row to df for it
    for match in sorted_matches:
        row: dict = dict()

        # Gets the comp level as a human readable label
        comp_level_text: str = cfg.COMP_LEVEL_KEY_TO_TEXT[match["comp_level"]]

        # Adds the match text with comp level and match/set number
        # If the match is a quals or finals match, use the match number. If its sf, use the set number.
        if match["comp_level"] == "qm" or match["comp_level"] == "f":
            match_text = f"{comp_level_text} {match['match_number']}"
        else:
            match_text = f"{comp_level_text} {match['set_number']}"

        # Set the row's match column to the match text and the key column to the match key
        row["Match"] = match_text
        row["Key"] = match["key"]

        # Iterate over each red team and add a column for them to the table
        for team in match["alliances"]["red"]["team_keys"]:
            row["Red " + str(match["alliances"]["red"]["team_keys"].index(team) + 1)] = team.replace("frc", "")
        # Iterate over each blue team and add a column for them to the table
        for team in match["alliances"]["blue"]["team_keys"]:
            row["Blue " + str(match["alliances"]["blue"]["team_keys"].index(team) + 1)] = team.replace("frc", "")

        # Append the row to the table
        table_df.loc[len(table_df)] = row

    # Returns the table
    return table_df


def main():
    # The page title
    st.title("Match Schedule")

    schedule: list = utils.get_event_schedule(st.session_state["currentEventCode"])
    # If match data not found, we can't proceed.
    if len(schedule) == 0:
        st.write("No match data found in the MongoDB.")
        return

    st.write("Click on the grey area to the left of a row to open up the Match Scouter.")

    # Checkbox to only show DoF matches on the schedule. Defaults to True
    only_dof = st.checkbox("Show only DoF", True)
    # Checkbox to show match key column on the schedule. Defaults to False
    include_key_col = st.checkbox("Show match key", False)

    # Get the schedule table DataFrame
    # schedule_df: DataFrame = get_schedule_table(st.session_state["tbaData"][st.session_state["currentEventCode"]])
    schedule_df: DataFrame = get_schedule_table(utils.get_event_schedule(st.session_state["currentEventCode"]))

    # If the "Show only DoF" checkbox is checked, filter the table to only rows with '6413'
    if only_dof:
        schedule_df = schedule_df[schedule_df.eq('6413').any(axis=1)]

    # Style schedule data to make more readable - red teams as red, blue as blue, and 6413 highlighted.
    styled_df: DataFrame = (schedule_df.style
                    .set_properties(**{'background-color': '#fee'}, subset=["Red 1", "Red 2", "Red 3"])
                    .set_properties(**{'background-color': '#eef'}, subset=["Blue 1", "Blue 2", "Blue 3"])
                    .map(color_team_matches))

    # Write the table and listen for selections to redirect to the match scouter
    table = st.dataframe(
        data=styled_df,                                                 # The DataFrame to get data from (in this case our table)
        height=2000,                                                     # Height to use for the table. We set it to a large number to fill the page so you don't have to scroll
        use_container_width=True,                                       # Expand the table width to fill the container's width
        column_config=({"Key": None} if not include_key_col else {}),   # Hide the "Key" column if the "Show match key" checkbox isn't checked
        hide_index=True,                                                 # Hide the DataFrame's index
        on_select="rerun",                                              # When a row is selected on the table, rerun the page
        selection_mode="single-row",                                    # Only allow one row to be selected at a time
    )

    # Check the table for selections and open the Match Scouter if there is one
    if len(table.selection["rows"]):
        selected_row = table.selection["rows"][0]
        # Sets the selected match for Match Scouter to the selected row's match key.
        # This modifies the match input on the Match Scouter page directly
        st.session_state["match_scouter_selected_match"] = schedule_df.iloc[selected_row]["Key"].split("_")[1]
        # Opens the Match Scouter page.
        st.switch_page("pages/match_scouter.py")


main()
