# This script is used to find missing match entries in the MongoDB.
#
# It takes an event code, a team number (or no team number for all teams),
# and a match number. It will find missing data for that team at the event
# through the specified match
#
# Outputs all missing data

import sys
import re as regex
from typing import Tuple, List, Optional
from tbaapiv3client.configuration import Configuration
from tbaapiv3client.api import TBAApi, EventApi
from tbaapiv3client.api_client import ApiClient
from tbaapiv3client.models.match_simple import MatchSimple
from tbaapiv3client.rest import ApiException
from colorama import init, Fore, Style
from pymongo import MongoClient
from pymongo.collection import Collection
import credentials as creds
import config as cfg

# Simple list holding
comp_level_order = [
    "qm",
    "sf",
    "f"
]


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
def mongo_collection () -> Collection | None:
    """
    Attempts to get the data from the MongoDB scouting collection. Returns None if unsuccessful

    Returns:
        A Collection from the MongoDB if the connection was successful. Otherwise, returns None
    """
    try:
        client: MongoClient = MongoClient(creds.PRIMARY_CONNECTION_STRING)
        db = client.get_database(cfg.DB_NAME)
        collection = db.get_collection(cfg.V5_COL_SCOUTING)

        return collection
    except ApiException as e:
        print(f"{Fore.RED}Exception when fetching MongoDB data: %s{Style.RESET_ALL}\n" % e)
        return None  # Treat any exception as API being down


###############################################################################
###############################################################################
def get_matches(api_client: ApiClient, event_code: str, team_number: str) -> List[dict] | None:
    """
    Get all the matches with the given event_code and team_number

    Args:
        api_client (ApiClient): An instance of the TBA API client.
        event_code (str): The event code to get the matches from.
        team_number (str): The team number to get the matches for.

    Returns:
        List[dict]: A list of dicts
    """
    # Create an instance of the API class
    api_instance = EventApi(api_client)
    try:
        api_response = api_instance.get_event_matches_simple(event_code)

        if api_response is None:
            # No data found, display error message with colorama
            error_message = f"{Fore.RED}ERROR: Unable to get the list of matches for {eventCode}. Check your event code and try again!{Style.RESET_ALL}"
            print(error_message)
        else:
            if len(team_number) > 0:
                # Filter the matches by team number
                matches = [match for match in api_response if f"frc{team_number}" in match.alliances.blue.team_keys or f"frc{team_number}" in match.alliances.red.team_keys]
            else:
                matches = api_response
            return matches

        # Return the API event matches info
        return matches
    except ApiException as e:
        print(f"{Fore.RED}Exception when getting matches: %s{Style.RESET_ALL}\n" % e)
        return None


###############################################################################
###############################################################################
def check_mongo_for_match(collection: Collection, match: MatchSimple, team: str) -> list:
    """
    Compares the data in the MongoDB with that of the match data to confirm the MongoDB holds the data

    Args:
        collection (Collection): The MongoDB collection to check data in
        match (MatchSimple): A TBA MatchSimple object of the match to check
        team (str): The team number to filter checks to. If an empty string, it will check for all teams in the match.

    Returns:
        A list of all missing scouting data entries for the match. If there are no missing entries, the list will be of length zero.
    """
    missing_entries: List[str] = list()

    # If the team is specified, just set the all_teams list to the team number
    # Otherwise, set all_teams to a list of every team in the match
    if len(team) > 0:
        all_teams: List[str] = [team]
    else:
        all_teams: List[str] = match.alliances.red.team_keys + match.alliances.blue.team_keys
        all_teams = [team.strip("frc") for team in all_teams]

    # List of match keys for every single entry we expect to find in the MongoDB for that match based on TBA match data
    expected_entries: List[str] = [f"{match.key}_frc{team}" for team in all_teams]
    # Mongo query that finds all items in the MongoDB with the match key and a team number in all_teams
    mongo_match_entries = collection.find({
        "_id": {"$regex": f"{match.key}(?=_)"},
        "team": {"$in": all_teams},
        "docType": cfg.DT_SCOUTING_MATCH
    })

    # Extracts all the entry keys/IDs from the mong_match_entries
    mongo_found_keys = [entry["_id"] for entry in mongo_match_entries]

    # Appends all entries in expected_entries not in mongo_found_keys to missing_entries
    for entry in expected_entries:
        if entry not in mongo_found_keys:
            missing_entries.append(entry)

    return missing_entries


###############################################################################
###############################################################################
def match_key_to_dict(match_key: str) -> dict:
    """
    Converts a string containing a match key (excluding event code) to a dictionary containing the event code, competition level, match number, and set number.

    Args:
        match_key (str): The match key to convert. Format should follow ``<comp level><set number>m<match number>`` eg ``qm1`` or ``f1m1``. For quals there is no set number.

    Returns:
        dict: Dictionary containing the competition level, match number, and set number. Keys are ``comp_level``, ``match_number``, and ``set``, respectively.
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


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":
    # To see coloring on Windows consoles you need to have this
    # colorama call BEFORE doing ANY output.
    init(autoreset=True, convert=True)

    eventCode: str = input("Enter the event code to check data for ('quit' to exit): ").strip()
    if eventCode.lower() == "quit":
        sys.exit(0)

    teamNumber: str = input("Enter the team number to check data for, or leave blank to check data for all teams ('quit' to exit): ").strip()
    if teamNumber.lower() == "quit":
        sys.exit(0)

    matchKey: str = input("Enter the match to check data through - formatted as the end of a match key. eg 'qm13' ('quit' to exit): ").strip()
    if matchKey.lower() == "quit":
        sys.exit(0)

    # Create required API configuration info
    configuration = Configuration( api_key={'X-TBA-Auth-Key': creds.TBA_AUTH_KEY} )

    # Enter a context with an instance of the API client to be used by all
    # other functions that call TBA for data.
    with ApiClient(configuration) as api_client:
        # Note the use of [0] below to force unpacking the first value
        # of the returned tuple.  Otherwise you will ALWAYS see a
        # 'truthy' value resulting in bogus behavior!
        if is_TBA_down(api_client)[0]:
            print(f"The TBA API is {Fore.RED}DOWN{Style.RESET_ALL}.")
            sys.exit(0)

        # Gets a list of all matches from TBA
        matches: Optional[List[MatchSimple]] = get_matches(api_client, eventCode, teamNumber)

        if matches is None:  # Check for None immediately after getting matches
            print(f"{Fore.RED}ERROR: Could not retrieve matches. Data not checked.{Style.RESET_ALL}")
            sys.exit(1)
        else:  # if matches is not None, proceed
            # Gets the match key as a dictionary with each individual element accessible
            matchKeyDict = match_key_to_dict(matchKey)
            # Gets all the data in the MongoDB match scouting colelction
            mongoData = mongo_collection()

            # Filters the matches to ensure all matches come before the specified match key
            filteredMatches: List[MatchSimple] = [match for match in matches if
                comp_level_order.index(match.comp_level) < comp_level_order.index(matchKeyDict["comp_level"])
                or (match.comp_level == "qm" and match.match_number <= matchKeyDict["match_number"])
                or (matchKeyDict["set_number"] is not None and match.comp_level in ("sf", "f") and match.set_number <= matchKeyDict["set_number"])
            ]

            if mongoData is None:  # Check for None immediately after getting MongoDB data
                print(f"{Fore.RED}ERROR: Could not retrieve MongoDB Collection. Data not checked.{Style.RESET_ALL}")
                sys.exit(1)

            # List of all missing entries
            missingEntries: List[str] = list()
            for match in filteredMatches:
                # List of invalid/missing entries found in the match data but not found in the MongoDB
                matchMissingEntries: List[str] = check_mongo_for_match(mongoData, match, teamNumber)

                # Add missing entries in the match to the missingEntries list, if there are any
                if len(matchMissingEntries) > 0:
                    missingEntries.extend(matchMissingEntries)

            # Log the output of this script.
            if len(missingEntries) == 0:
                print(f"{Fore.GREEN}No missing data.{Style.RESET_ALL}")
            else:
                for matchKey in missingEntries:
                    print(f"{Fore.RED}Missing data for {matchKey}.{Style.RESET_ALL}")
