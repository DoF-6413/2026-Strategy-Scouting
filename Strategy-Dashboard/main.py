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
        st.Page("dashboard_pages/all_teams.py", title="All Teams", default=True),     # default=True tells Streamlit to take the user to this page first.
        st.Page("dashboard_pages/team_summary.py", title="Team Summary"),
        st.Page("dashboard_pages/match_schedule.py", title="Match Schedule"),
        st.Page("dashboard_pages/match_scouter.py", title="Match Scouter"),
        st.Page("dashboard_pages/alliance_explorer.py", title="Alliance Explorer"),
        st.Page("dashboard_pages/niche_finder.py", title="Niche Finder"),
        st.Page("dashboard_pages/defense.py", title="Defense"),
    ]

    # Gives Streamlit the pages and starts off the navigation on the default
    # page (All Teams)
    pg = st.navigation(pages=pages)
    pg.run()


def sidebar_inputs() -> None:
    """
    Adds necessary inputs to the sidebar:

    - Current event code selector
    - Additional event codes selector
    - Refresh match schedule button
    - Refresh all button
    """
    # Write an input to select the current event code and set the session state
    # to the selection. Always shown, even with an empty MongoDB, since it's
    # the only way to set the event code in the first place.
    # The value is explicitly tied back to the permanent "currentEventCode"
    # session state (same pattern as stat_selector/team_selector/etc. in
    # utils.py) so the typed value keeps showing up across reruns/page
    # switches instead of resetting to blank.
    st.sidebar.text_input(
        "Current event code",
        value=st.session_state["currentEventCode"],
        key="_currentEventCodeInput",
        on_change=utils.input_change,
        args=["currentEventCode", "_currentEventCodeInput"]
        )

    # Get a list of all possible event codes that can be selected
    selectable_event_codes: list = utils.get_all_event_codes()

    if len(selectable_event_codes) == 0:
        st.write("No data found in the MongoDB. Check config.py and credentials.py")
        return

    # Data queries always include the Current Event Code automatically (see
    # utils.get_scouting_data/get_match_data), so this list is only for
    # events *in addition to* the current one (e.g. to compare against a
    # previous event). It defaults to empty (see init_session_state_keys) so
    # a user who only sets Current Event Code sees just that event's data,
    # never other events' data pulled in silently.
    default_data_event_codes = st.session_state["dataEventCodes"]

    current_event_code: str = st.session_state["currentEventCode"]
    current_event_year = current_event_code[:4]

    # Don't offer the current event as an "additional" option since it's
    # already included automatically. Also restrict to events from the same
    # season as the Current Event Code (event codes are "<year><rest>", e.g.
    # "2026azfg") so combined data stays comparable instead of mixing
    # different years' games together. Sorted alphabetically so the user can
    # scan the list instead of hunting through insertion order.
    additional_event_code_options = sorted(
        code for code in selectable_event_codes
        if code != current_event_code and code[:4] == current_event_year
    )

    # Write the additional data event codes input
    st.sidebar.multiselect(
        label="Additional Event Codes",                     # The input's label
        options=additional_event_code_options,               # Every option that can be selected in the dropdown
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
        utils._get_scouting_data.clear()
        utils._get_match_data.clear()

        st.rerun()

    # Button to clear the entire Streamlit cache
    if st.sidebar.button("Force Refresh All"):
        st.cache_data.clear()


# Use a wide page layout
st.set_page_config(layout="wide")

# Call the above functions to initialize the dashboard
init_session_state_keys()
sidebar_inputs()

if st.session_state["currentEventCode"] == "":
    st.sidebar.write("Enter current event code.")

# Always use our own page navigation (rather than Streamlit's automatic
# discovery, which is why the page scripts live in dashboard_pages/ instead
# of a folder literally named pages/ -- see the README) so the sidebar
# doesn't flip between two different navigation UIs depending on whether an
# event code has been entered yet. Individual pages already handle an
# empty/missing event code gracefully.
init_pages()
