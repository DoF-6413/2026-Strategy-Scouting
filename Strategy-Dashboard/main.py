import streamlit as st
import utils


def init_session_state_keys () -> None:
    """
    Initializes session state keys.

    Because session state is a dict, attempting to access non-existent keys
    will throw an error, which is why we have to initialize.
    """
    # Every value has the key being the key to initialize and the value pair is
    # the default value
    keys = {
        "allianceExplorerData": [],
        "currentEventCode": "",
        "dataEventCodes": [],
        "teamSummaryUsedIdLen": 0,
        "team_summary_selected_teams": "",
        "showImages": True
    }

    # Iterate over every item in keys and set the key in session state to the
    # default value if it doesn't exist.
    for key, value in keys.items():
        if key not in st.session_state:
            st.session_state[key] = value


def init_pages() -> None:
    """ Initializes all the pages to be used in Streamlit """
    # List of st.Page objects to use as pages
    pages = [
        st.Page("pages/all_teams.py", title="All Teams", default=True),     # default=True tells Streamlit to take the user to this page first.
        st.Page("pages/team_summary.py", title="Team Summary"),
        st.Page("pages/match_schedule.py", title="Match Schedule"),
        st.Page("pages/match_scouter.py", title="Match Scouter"),
        st.Page("pages/alliance_explorer.py", title="Alliance Explorer"),
        st.Page("pages/niche_finder.py", title="Niche Finder"),
        st.Page("pages/defense.py", title="Defense"),
    ]

    # Gives Streamlit the pages and starts off the navigation on the default
    # page (All Teams)
    pg = st.navigation(pages=pages)
    pg.run()


def sidebar_inputs() -> None:
    """
    Adds necessary inputs to the sidebar:

    - Current event code selector
    - Data event codes selector
    - Refresh match schedule button
    - Refresh all button
    """
    # Get a list of all possible event codes that can be selected
    selectable_event_codes: list = utils.get_all_event_codes()

    if len(selectable_event_codes) == 0:
        st.write("No data found in the MongoDB. Check config.py and credentials.py")
        return

    # Write an input to select the current event code and set the session state
    # to the selection
    st.sidebar.text_input(
        "Current event code",
        key="_currentEventCodeInput",
        on_change=utils.input_change,
        args=["currentEventCode", "_currentEventCodeInput"]
        )

    # Sets default data events codes to session state if it has them
    # otherwise defaults to the full list of event codes
    default_data_event_codes = st.session_state["dataEventCodes"]
    if len(st.session_state["dataEventCodes"]) == 0:
        default_data_event_codes = selectable_event_codes
        st.session_state["dataEventCodes"] = default_data_event_codes

    # Write the data event codes input
    st.sidebar.multiselect(
        label="Data Event Codes",                           # The input's label
        options=selectable_event_codes,                     # Every option that can be selected in the dropdown
        default=default_data_event_codes,                   # The default selected options
        key="_dataEventCodesInput",                         # A session_state key where the data will be temporary stored. Note storage from this method is NOT the same as normal session state. It is TEMPORARY
        on_change=utils.input_change,                       # Callback function used when the value is changed
        args=["dataEventCodes", "_dataEventCodesInput"]     # args to pass to the callback function (utils.input_change)
    )

    st.sidebar.divider()

    st.sidebar.checkbox(
        label="Show robot images?",
        value=True,
        key="_showImagesInput",
        on_change=utils.input_change,
        args=["showImages", "_showImagesInput"]
    )

    st.sidebar.divider()

    def refresh_match_schedule():
        """
        Fetches TBA match data and refreshes the match schedule if possible
        """
        # Status message indicating the status of the request
        st.toast("Refreshing match schedule...")

        # Clear the cache of the get_event_schedule function
        # This is so we can call it without Streamlit just returning the cached value
        utils.get_event_schedule.clear()

    # Button to refresh match schedule. Calls refresh_match_schedule on click.
    st.sidebar.button("Refresh Match Schedule", on_click=refresh_match_schedule)

    # Button to refresh scouting data by clearing the cache
    if st.sidebar.button("Refresh Scouting Data"):
        mongo_func = utils.get_scouting_data
        match_data_func = utils.get_match_data

        mongo_func.clear()
        match_data_func.clear()

        st.rerun()

    # Button to clear the entire Streamlit cache
    if st.sidebar.button("Force Refresh All"):
        st.cache_data.clear()


# Use a wide page layout
st.set_page_config(layout="wide")

# Call the above functions to initialize the dashboard
init_session_state_keys()
sidebar_inputs()

if st.session_state["currentEventCode"] != "":
    init_pages()
else:
    st.write("Enter current event code.")
