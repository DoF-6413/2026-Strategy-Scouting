# A page where hypothetical alliances can be made up to compare them and their summaries
import numpy as np
import streamlit as st
import utils


def alliance_teams_changed(alliance_index: int):
    """Callback for when the teams input of an alliance container is edited.

    Only used for ``create_alliance_edit_container``

    Args:
        alliance_index (int): Index of the edited alliance in the list of alliances stored in the session state for the alliance explorer.
    """
    # New teams selection value from input
    new_teams = st.session_state["_allianceMultiSelect" + str(alliance_index)]
    # Set allianceExplorerData in session state to the new selection
    st.session_state["allianceExplorerData"][alliance_index] = new_teams

def delete_alliance(alliance_index) -> None:
    """Callback for when the delete button is clicked on an alliance container.

    Only used for ``create_alliance_edit_container``.

    Args:
        alliance_index (int): Index of the alliance in the list of alliances stored in the session state for the alliance explorer.
    """
    # Deletes the entry in the allianceExplorerData of session state
    del st.session_state["allianceExplorerData"][alliance_index]

def create_alliance_edit_container(teams: list, all_teams: list, alliance_index: int) -> None:
    """Creates alliance editing container with teams input and delete button

    Args:
        teams (list): List of teams in the alliance
        all_teams (list): List of all teams at the event
        alliance_index (int): Index of the alliance in the list of alliances stored in the session state for the alliance explorer
    """
    with st.container(border=1):
        col1, col2 = st.columns([3,1]) # Make columns with 3:1 width ratio

        # Write the team numbers input
        # In this case we use a special input instead of a utils.team_selector because we need more control over how the permanent keys are handled
        col1.multiselect(
            label="Teams",                                      # The input label
            options=all_teams,                                  # Options to show on dropdown
            default=teams,                                      # Default selections
            key="_allianceMultiSelect" + str(alliance_index),   # A session_state key where the data will be temporary stored. Note storage from this method is NOT the same as normal session state. It is TEMPORARY
            on_change=alliance_teams_changed,                   # Callback function for when the input is changed
            args=(alliance_index,),                              # args to pass to the callback function (alliance_teams_changed)
        )
        # Write the delete button
        col2.button(
            label="Delete",                                     # Text on button to label it
            key="_allianceDeleteBtn" + str(alliance_index),     # A session_state key where the data will be temporary stored. Note storage from this method is NOT the same as normal session state. It is TEMPORARY
            on_click=delete_alliance,                           # Callback function for when the input is changed
            args=(alliance_index,),                              # args to pass to the callback function (delete_alliance)
        )

def main():
    # Page title
    st.title("Alliance Explorer")

    # List of alliances from alliance explorer saved in session storage
    stored_alliances = st.session_state["allianceExplorerData"]
    # Fetch the match and prescouting data
    match_df = utils.get_match_data()
    prescouting_df = utils.get_prescouting_data()

    # Write button to add an aliiance and check if its clicked
    add_alliance_btn = st.button("Add Alliance")
    if add_alliance_btn:
        stored_alliances.append(list())

    # If there aren't aren't alliances already stored, add a blank one to the list so the entry container can be displayed
    if len(stored_alliances) < 1:
        stored_alliances.append(list())

    # Get teams to be used for the team inputs
    teams_list = utils.get_event_teams(st.session_state["currentEventCode"])
    # Write the container to edit an alliance for each alliance
    for index, alliance in enumerate(stored_alliances):
        create_alliance_edit_container(alliance, teams_list, index)

    # If the alliance(s) are blank, don't try to render data/charts for them
    if np.sum([1 if len(x) > 0 else 0 for x in stored_alliances]) == 0:
        st.write("Add alliances to visualize data")
        return

    # Write the information on the alliances
    utils.write_alliances_view(match_df, prescouting_df, stored_alliances)

main()
