# This script is used to create the Markdown prescouting template for
# all teams going to an FRC event.  All it needs is a valid TBA event code
# and it will create and save the Markdown to the file you tell it to.
#
# The Markdown is intended to be Imported into a Google Doc to collect all
# prescouting notes for every team going to the specified event.  The Markdown
# is used by the prescouting_upload.py script to import data to our MongoDB.
#
# In V11 we updated the get_teams_for_event() to make more efficient use of the
# TBA API calls.  With that we also removed get_team_rookie_years() which is
# now obsolete.  We also added back the blank line between the pre-scouting
# categories in the Markdown file.
#
# In V12 we added a "Team Page" link to the team's TBA page before the
# statistical info in the Markdown template.

import sys
from typing import Any, Dict, List, Optional, Set, TextIO, Tuple

import config as cfg
import credentials as creds
import statbotics
import tbaapiv3client
from colorama import Fore, Style, init
from tabulate import tabulate
from tbaapiv3client.api import TBAApi
from tbaapiv3client.api_client import ApiClient
from tbaapiv3client.rest import ApiException


###############################################################################
###############################################################################
def is_TBA_down(api_client: ApiClient) -> Tuple[bool, int, int]:
    """
    Check if the TBA API is down.  It also returns the current_season and
        max_season values from the TBA API

    Args:
        api_client (ApiClient): An instance of the TBA API client.

    Returns:
        Tuple[bool, int, int]: A tuple containing:
            - A boolean indicating the TBA API is down.
            - The current_season value
            - The max_season value
    """
    try:
        # Create an instance of the API class
        api_instance = TBAApi(api_client)

        # Perform the API status check
        api_response = api_instance.get_status()

        # Extract data from API response
        is_down = api_response.is_datafeed_down
        current_season = api_response.current_season
        max_season = api_response.max_season

        # Return the API status info
        return is_down, current_season, max_season
    except ApiException as e:
        print(f"{Fore.RED}Exception when calling TBAApi.get_status: %s{Style.RESET_ALL}\n" % e)
        return True, None, None  # Treat any exception as API being down


###############################################################################
###############################################################################
def display_pre_event_stats(team_stats: List[Dict[str, Any]]) -> None:
    """
    Formats Statbotics data into a table and highlights the top 10% 
    of teams in Auto, Teleop, and Endgame categories.
    """
    headers = ["Rank", "Team", "Nickname", "Pre-Event EPA", "Auto", "Teleop", "Endgame"]
    table_data = []

    # Helper function to get thresholds for a specific breakdown key
    def get_threshold(data_list, key):
        scores = [t.get("epa", {}).get("breakdown", {}).get(key, 0) or 0 for t in data_list]
        if not scores: return 999
        return sorted(scores)[-max(1, int(len(scores) * 0.1))]

    auto_th = get_threshold(team_stats, "auto_points")
    tele_th = get_threshold(team_stats, "teleop_points")
    end_th = get_threshold(team_stats, "endgame_points")

    for rank, team in enumerate(team_stats, start=1):
        epa_root = team.get("epa", {})
        breakdown = epa_root.get("breakdown", {})
        stats_inner = epa_root.get("stats", {})

        # Data Extraction
        team_num = team.get("team")
        nickname = team.get("team_name", "N/A")[:20]
        start_epa = stats_inner.get("start", 0.0)

        auto = breakdown.get("auto_points", 0.0)
        teleop = breakdown.get("teleop_points", 0.0)
        endgame = breakdown.get("endgame_points", 0.0)

        # Apply formatting to the numbers themselves if they meet the threshold
        # We wrap elite scores in asterisks to make them pop visually
        auto_display = f"*{round(auto, 1)}*" if auto >= auto_th and auto > 0 else round(auto, 1)
        tele_display = f"*{round(teleop, 1)}*" if teleop >= tele_th and teleop > 0 else round(teleop, 1)
        end_display = f"*{round(endgame, 1)}*" if endgame >= end_th and endgame > 0 else round(endgame, 1)

        table_data.append([
            rank,
            team_num,
            nickname,
            round(start_epa, 1),
            auto_display,
            tele_display,
            end_display
        ])

    print("\n### PRE-EVENT SCOUTING SUMMARY ###")
    print("Note: Values wrapped in *asterisks* represent the Top 10% in that category.")
    print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", numalign="center"))


###############################################################################
###############################################################################
def get_filtered_team_data(
    eventCode: str,
    team_strings: List[str]
) -> List[Dict[str, Any]]:
    """
    Fetches Statbotics data and filters by a team list.
    
    Args:
        eventCode: The TBA event key.
        team_strings: List of "NUMBER (NICKNAME)" strings.
    """
    sb = statbotics.Statbotics()

    # 1. Parse team numbers
    target_numbers: Set[int] = {
        int(s.split(' ')[0]) for s in team_strings if s.split(' ')[0].isdigit()
    }

    try:
        # 2. Fetch event data
        all_event_teams: List[Dict[str, Any]] = sb.get_team_events(event=eventCode, limit=100)

        # 3. Filter
        filtered_teams = [t for t in all_event_teams if t['team'] in target_numbers]

        # 4. Sort by the nested start EPA: epa -> stats -> start
        # Using .get() and chaining to prevent crashes if a key is missing
        filtered_teams.sort(
            key=lambda x: x.get("epa", {}).get("stats", {}).get("start", 0) or 0,
            reverse=True
        )

        return filtered_teams

    except Exception as e:
        print(f"Error: {e}")
        return []


###############################################################################
###############################################################################
def get_teams_for_event(
    api_client: ApiClient,
    eventCode: str
) -> Tuple[Optional[List[str]], Dict[int, int]]:
    '''
    Get team list and rookie year information for teams registered
    at the specified event.

    Args:
        api_client (ApiClient): An instance of the TBA API client.

        eventCode (str): The TBA event code.

    Returns:
        Tuple containing:
            List[str]: Team strings formatted as
                "<team number> (<team nickname>)"
            Dict[int, int]: Mapping of team_number -> rookie_year
            OR
            (None, {}) if an error occurs.
    '''

    api_instance = tbaapiv3client.TeamApi(api_client)

    try:
        teams = api_instance.get_event_teams(eventCode)

        if teams is None:
            print(f"{Fore.RED}ERROR: Unable to get the list of teams for {eventCode}.{Style.RESET_ALL}")
            return None, {}

        # Sort teams by team number
        teams_sorted = sorted(teams, key=lambda t: t.team_number)

        team_strings = []
        rookie_years = {}

        for team in teams_sorted:
            team_strings.append(f"{team.team_number} ({team.nickname})")
            rookie_years[team.team_number] = team.rookie_year

        return team_strings, rookie_years

    except ApiException as e:
        print(f"{Fore.RED}Exception when calling TeamApi.get_event_teams: %s{Style.RESET_ALL}\n" % e)
        return None, {}


###############################################################################
###############################################################################
def get_epa_threshold(team_stats: List[Dict[str, Any]]) -> float:
    """
    Calculate the EPA value representing the top 10% of teams.

    Args:
        team_stats (List[Dict[str, Any]]): A list of Statbotics team data
            dictionaries returned by the Statbotics API. Each dictionary
            contains EPA statistics for a team, including the nested
            structure:
                epa -> stats -> start
            which represents the team's pre-event EPA.

    Returns:
        float: The EPA value corresponding to the top 10% threshold.
            Any team with an EPA greater than or equal to this value
            is considered a "Top 10% Team". If no valid EPA values
            are found, a high sentinel value (999) is returned so
            that no teams are flagged.
    """

    epa_scores = [
        t.get("epa", {}).get("stats", {}).get("start", 0) or 0
        for t in team_stats
    ]

    if not epa_scores:
        return 999

    epa_scores.sort()

    team_count = len(epa_scores)
    top_10_percent_count = max(1, int(team_count * 0.1))

    threshold_index = team_count - top_10_percent_count

    return epa_scores[threshold_index]


###############################################################################
###############################################################################
def write_template(
    file: TextIO,
    teams: List[str],
    team_stats: List[Dict[str, Any]],
    rookie_years: Dict[int, int],
    current_season: int
) -> None:
    """
    Write the prescouting Markdown template for all teams attending an event.

    For each team, the template includes:
        - An H1 header containing the team number and nickname
        - Optional indicators for Rookie Team or Second-Year Team
        - Optional "Top 10% Team" indicator based on pre-event EPA
        - Statbotics statistics (EPA, Auto, Teleop, Endgame)
        - Prescouting sections defined in cfg.PRESCOUTING_FIELDS

    Args:
        file (TextIO): An open file object (typically created using open())
            where the generated Markdown will be written.

        teams (List[str]): A list of team identifiers formatted as
            "<team number> (<team nickname>)". This list is normally
            retrieved from The Blue Alliance API and sorted by team number.

        team_stats (List[Dict[str, Any]]): Statbotics event data for teams.
            Each dictionary contains EPA statistics and scoring breakdowns
            for a team. This data is used to populate the Statbotics fields
            and determine whether a team falls within the top 10% EPA
            threshold for the event.

        rookie_years (Dict[int, int]): Dictionary mapping team_number to
            rookie_year retrieved from The Blue Alliance.

        current_season (int): The current FRC season year used to determine
            whether a team is a rookie or second-year team.
    """

    stats_lookup = {t["team"]: t for t in team_stats}
    epa_threshold = get_epa_threshold(team_stats)

    def safe_round(value):
        return round(value, 1) if isinstance(value, (int, float)) else "N/A"

    output_str: str = ""

    for team in teams:

        output_str += f"# {team}\n"

        try:
            team_num = int(team.split(" ")[0])
        except ValueError:
            team_num = None

        # -------------------------------------------------------------
        # Determine Rookie / Second-Year status
        # -------------------------------------------------------------
        rookie_flag = None

        if team_num in rookie_years and rookie_years[team_num]:
            years_active = current_season - rookie_years[team_num] + 1

            if years_active == 1:
                rookie_flag = "Rookie Team"
            elif years_active == 2:
                rookie_flag = "Second-Year Team"

        if rookie_flag:
            output_str += f"\n**{rookie_flag}**\n"

        # -------------------------------------------------------------
        # Extract Statbotics data for this team
        # -------------------------------------------------------------
        epa = auto = teleop = endgame = "N/A"
        is_top_team = False

        if team_num and team_num in stats_lookup:

            t = stats_lookup[team_num]

            epa_root = t.get("epa", {})
            breakdown = epa_root.get("breakdown", {})
            stats_inner = epa_root.get("stats", {})

            start_epa = stats_inner.get("start")

            epa = safe_round(start_epa)
            auto = safe_round(breakdown.get("auto_points"))
            teleop = safe_round(breakdown.get("teleop_points"))
            endgame = safe_round(breakdown.get("endgame_points"))

            if isinstance(start_epa, (int, float)) and start_epa >= epa_threshold:
                is_top_team = True

        if is_top_team:
            output_str += "\n**Top 10% EPA Team**\n"

        # -------------------------------------------------------------
        # Write TBA team page link
        # -------------------------------------------------------------
        if team_num:
            output_str += f"\n[Team Page](https://www.thebluealliance.com/team/{team_num})\n"

        # -------------------------------------------------------------
        # Write Statbotics stats
        # -------------------------------------------------------------
        output_str += f"\n**EPA:** {epa}  \n"
        output_str += f"**Auto:** {auto}  \n"
        output_str += f"**Teleop:** {teleop}  \n"
        output_str += f"**Endgame:** {endgame}  \n\n"

        # -------------------------------------------------------------
        # Write prescouting sections
        # -------------------------------------------------------------
        for field in cfg.PRESCOUTING_FIELDS:
            output_str += f"\n## {field}\n"

        output_str += "\n\n"

    file.write(output_str.strip())
    file.close()


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":

    eventCode: str = input("Enter the event code to get the team info for (or 'quit' to exit): ").strip()

    if eventCode.lower() == "quit":
        sys.exit(0)

    # Create required API configuration info
    configuration = tbaapiv3client.Configuration( api_key={'X-TBA-Auth-Key': creds.TBAAUTHKEY} )

    # To see coloring on Win10 consoles I found I needed to have this
    # colorama call before doing any output.
    init(convert=True)

    # Enter a context with an instance of the API client to be used by all
    # other functions that call TBA for data.
    with tbaapiv3client.ApiClient(configuration) as api_client:
        # No longer unpacking since we need the current season for work later.
        is_down, current_season, max_season = is_TBA_down(api_client)
        if is_down:
            print(f"The TBA API is {Fore.RED}DOWN{Style.RESET_ALL}.")
            sys.exit(0)

        teams, rookie_years = get_teams_for_event(api_client, eventCode)

        if teams is None:  # Check for None immediately after getting teams
            print(f"{Fore.RED}ERROR: Could not retrieve teams. Template not generated.{Style.RESET_ALL}")
            sys.exit(1)
        else: # if teams is not None, proceed
            # Use pre_event = True for prescouting as without it we get AT EVENT data
            # instead of data before the event...
            team_stats = get_filtered_team_data(eventCode, teams)

            # If you want to see who has the best Auto instead of the best overall EPA, you can sort
            # the list before passing it to the display function:
            # Sort by Auto Points instead of Start EPA (default)
            # team_stats.sort(key=lambda x: x.get("epa", {}).get("breakdown", {}).get("auto_points", 0), reverse=True)

            # Display the pre-event stat rankings of all teams...
            # display_pre_event_stats(team_stats)

            output_file_name: str = input("What file name would you like the template to be (excluding file extension)? ").strip()
            try: # wrap file opening in try/except to handle potential errors
                with open(output_file_name + ".md", "w+") as file:
                    write_template(file, teams, team_stats, rookie_years, current_season)
                    print(f"Template written to {output_file_name + '.md'}")
            except OSError as e: # catch OS errors, such as permission issues.
                print(f"{Fore.RED}Error writing to {output_file_name + '.md'}: {e}{Style.RESET_ALL}")
                sys.exit(1)
