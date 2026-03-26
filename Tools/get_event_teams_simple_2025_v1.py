# A Python script to get an events teams from the TBA and store it into our
# MongoDB in the V3 data format.  It's primary use is to reading an events list
# of teams and storing it into the V5 data format for use by our scouting
# system.
#
# This is an updated of get_event_teams_simple_2023_pymongo_v3.py.  Changes
# include:
#
# 1: Upgraded to the V5 configuration
# 2: Removed Python 2.x legacy line:
#        from __future__ import print_function
# 3: PEP warning cleanup
# 4: Upgraded V3/V4 functions to their V5 equivalent.
# 5: Replaced eval(team.to_str()) with team.to_dict()
# 6: Redeisgned to separate TBA reading from MongoDB writing
# 7: Added tqdm to show progress saving data to MongoDB
# 8: Added new doc type to the V5_COL_EVENTS for simple team entries
#
# NOTE: If the imports fail below, make sure you are using the venv environment
# where the TBA libraries are installed.  They are NOT installed in the base OR
# scrapy environments!!

import logging
import sys
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional
from colorama import init, Fore
from tbaapiv3client.api import TBAApi, TeamApi
from tbaapiv3client.api_client import ApiClient
from tbaapiv3client.configuration import Configuration
from tbaapiv3client.rest import ApiException
from pymongo.database import Database
from pymongo.collection import Collection
from tqdm import tqdm
# from pprint import pprint
import config as cfg

_logger: Optional[logging.Logger] = None  # Module-level variable for logging


###############################################################################
###############################################################################
def setup_logger() -> logging.Logger:
    """
    Sets up a logger that saves any log output to a file in the script's
    directory, with a filename based on the current date and time.
    """

    global _logger

    # Only set up the logger once
    if _logger is None:
        # Create a logger and set it to WARNING or higher
        _logger = logging.getLogger(__name__)
        _logger.setLevel(logging.WARNING)

        # Check if a handler already exists (important to do this!!)
        if not _logger.handlers:
            # Construct the log file name using the current date and time
            log_file = f"UtilLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            # Get the script's directory
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # Create the full log file path
            log_file_path = os.path.join(script_dir, log_file)

            # Create a FileHandler to output thru
            handler = logging.FileHandler(log_file_path)

            # Create a formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)

            # Add the handler to the logger
            _logger.addHandler(handler)

    return _logger


###############################################################################
###############################################################################
def get_logger() -> logging.Logger:
    """
    Returns the scripts logger, initializing it if it hasn't been already.
    """
    global _logger

    if _logger is None:
        _logger = setup_logger()

    return _logger


###############################################################################
###############################################################################
def check_config_params(cfg: object, params: List[str]) -> bool:
    """
    Check if multiple configuration parameters exist and are non-empty strings
    in the given cfg object.

    Parameters:
        cfg: The configuration module (e.g., the imported 'config' module).

        params: A list of parameter names to check for (strings).

    Returns:
        True if any parameter is missing or empty, False otherwise.
    """
    badConfig: bool = False
    logger: logging.Logger = get_logger()

    for param_name in params:
        param_value = getattr(cfg, param_name, None)

        if not param_value:  # Check for None or empty string
            err_msg: str = f"ERROR: {param_name} is missing or empty!"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            badConfig = True

    return badConfig


###############################################################################
###############################################################################
def is_V5_configuration_bad() -> bool:
    '''
    Tell the caller if any V5 schema specific configuration information is
        bad or missing.

    Returns:
        bool: True if any V5 schema values are missing or empty, False otherwise.
    '''
    #
    # Scan ALL V5 schema values and report all bad ones
    v5_values_to_check = [
        "DB_NAME",
        "V5_COL_DATA",
        "V5_COL_EVENTS",
        "V5_COL_MATCH",
        "V5_COL_SCHEDULE",
        "V5_COL_SCOUTING",
        "V5_COL_STATISTICS",
        "V5_COL_TEAMS",
        "DT_EVENTS_EVENT",
        "DT_EVENTS_DISTRICT",
        "DT_EVENTS_TEAMS",
        "DT_SCOUTING_PIT",
        "DT_SCOUTING_PRESCOUT",
        "DT_SCOUTING_MATCH",
        "DT_STATISTICS_OPR",
        "DT_STATISTICS_DPR",
        "DT_STATISTICS_CCWM",
        "DT_STATISTICS_EPA",
        "MATCHLEVEL_QUALIFIERS",
        "MATCHLEVEL_QUARTERS",
        "MATCHLEVEL_SEMIS",
        "MATCHLEVEL_FINALS",
        "ALL_TEAMS",
        "ALL_TEAMS_DETAILED",
        "PRESCOUTING_FIELDS"
    ]

    badV5Config = check_config_params(cfg, v5_values_to_check)

    return badV5Config


###############################################################################
###############################################################################
def validate_configuration() -> None:
    '''
    Validate that the necessary configuration and credential information exists.

    First do credential checks and then do schema specific checks.  We only check
    the current schema and not all possible schemas.
    '''
    import credentials as creds

    # Scan ALL configuration settings and report all bad ones before we exit
    # That way we do not make the user edit the configuration multiple times.

    badConfig: bool = False
    badV5Config: bool = False
    logger: logging.Logger = get_logger()

    # The PRIMARY_CONNECTION_STRING MUST exist and be non-NULL!

    if not (hasattr(creds, "PRIMARY_CONNECTION_STRING") and creds.PRIMARY_CONNECTION_STRING):
        err_msg: str = "ERROR: PRIMARY_CONNECTION_STRING is missing or empty!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        badConfig = True

    # The SECONDARY_CONNECTION_STRING MUST exist but CAN be empty.

    if not (hasattr(creds, "SECONDARY_CONNECTION_STRING")):
        err_msg: str = "ERROR: SECONDARY_CONNECTION_STRING is missing!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        badConfig = True

    # Make sure all V5 schema values exist.

    badV5Config = is_V5_configuration_bad()

    # Getting here with any bad configurations is grounds to exit

    if badConfig or badV5Config:
        sys.exit(2)


###############################################################################
###############################################################################
def get_database(databaseURI: str, databaseName: str) -> Optional["Database"]:
    '''
    Returns a MongoDB database to read/write the all your data from/into OR
        None if there was a problem accessing the database.

    The collection to use is pulled from the configuration data so we use
        the same one for all databases.

    Parameters:
        databaseURI (str): The database connection URL to use

        databaseName (str): The name of the database to access

    Returns:
        A Database if we connected successfully, None if we failed for any
        reason!
    '''
    from pymongo import MongoClient

    logger: logging.Logger = get_logger()

    # Create a connection to the specified MongoDB server

    try:
        client: MongoClient = MongoClient(databaseURI)

        # Use/Create the database to hold our data
        return client[databaseName]
    except ConnectionError as e:
        err_msg: str = f"ERROR: Failed to connect to MongoDB server: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
    except AuthenticationError as e:
        err_msg: str = f"ERROR: Failed to authenticate with MongoDB: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
    except Exception as e:
        err_msg: str = f"ERROR: Failed to access the database: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")

    return None


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
    logger: logging.Logger = get_logger()

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
        err_msg: str = f"ERROR: Exception when calling TBAApi.get_status: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}\n")
        return True, None, None  # Treat any exception as API being down


###############################################################################
###############################################################################
def get_event_teams(api_instance: TeamApi, eventCode: str) -> Optional[List[Dict]]:
    '''
    Get the teams attending the specified event.  This call only returns teams
    at the event and not any of their matches.

    Parameters:
        api_instance (TeamApi): A TeamApi instance to make the TBA call against

        eventCode (str): The TBA event code to get the teams for

    Returns:
        Optional[List[Dict]]: A list of team dictionaries if successful, None otherwise.
     '''
    logger: logging.Logger = get_logger()

    try:
        api_response = api_instance.get_event_teams_simple(eventCode)

        if api_response is None:
            # No data found, display error message with colorama
            err_msg: str = f"{Fore.RED}ERROR: Unable to get the list of teams for {eventCode}. Check your event code and try again!"
            logger.error(err_msg)
            print(err_msg)
            return None
        
        # Sort the list by team_number in ascending order
        sorted_teams = sorted(api_response, key=lambda team: team.team_number)

        status_msg: str = f"There are {len(api_response)} teams reported for {eventCode}"
        logger.info(status_msg)
        print(status_msg)

        team_data_list: List[Dict] = []

        # Lets iterate over the list of teams and trim off some of the info we
        # do not care about before we return it.

        for team in sorted_teams:
            # Convert the Team object to a dictionary we can tweak a little
            teamToSave = team.to_dict()

            # Remove the long winded "official name" of the team since we
            # NEVER use it.
            teamToSave.pop('name', None)

            # Add the doc type and event code to the data
            teamToSave['docType'] = cfg.DT_EVENTS_TEAMS
            teamToSave['event_key'] = eventCode

            # Set the _id value of the entry to be the event code and the team
            id_to_use = f"{eventCode}_{teamToSave['key']}"
            teamToSave['_id'] = id_to_use

            team_data_list.append(teamToSave)

        return team_data_list

    except ApiException as e:
        err_msg: str = f"ERROR: APIException when calling TeamApi.get_event_teams_simple: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        return None
#    except pymongo.errors.InvalidDocument as invdoc:
#        print( "Invalid document: %s\n" % invdoc )


###############################################################################
###############################################################################
def saveDataToMongo(data: List[Dict], dbCollection: Collection, dbIdentifier: str) -> None:
    """
    Saves a given data to the given MongoDB collection.  If some data already
    exists then it will get updated.  The most likely cause for this is we
    get playoff or final match info after already getting just the qualifiers.

    Args:
        data: A list of dictionaries with data to save

        dbCollection: The MongoDB collection to save to.

        dbIdentifier: An identifier string for identifying which MongoDB is
                      being used.
    """
    logger: logging.Logger = get_logger()

    try:
        if data:
            for doc in tqdm(data, desc=f"Saving to {dbCollection.name} ({dbIdentifier})"):
                filter_criteria = {"_id": doc.get("_id")}
                if filter_criteria["_id"] is not None:
                    dbCollection.replace_one(filter_criteria, doc, upsert=True)
                else:
                    dbCollection.insert_one(doc)
    except Exception as e:
        collection_name = dbCollection.name
        err_msg: str = f"Error saving to {collection_name} ({dbIdentifier}): {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")


###############################################################################
###############################################################################
def main() -> None:
    import credentials as creds

    logger: logging.Logger = get_logger()

    # Make sure the config data we need exists and is NOT empty.  Any failures
    # with the configuration will prevent the code from continuing on.
    validate_configuration()

    # Configure API key authorization: apiKey
    configuration = Configuration(api_key={'X-TBA-Auth-Key': creds.TBA_AUTH_KEY})

    # To see coloring on Win10 consoles I found I needed to have this
    # colorama call before doing any output.  We use autoreset=True so
    # we do not need to include Style.RESET_ALL all over.
    init(autoreset=True, convert=True)

    eventCode: str = input("Enter the event code (or 'quit' to exit): ").strip()

    if eventCode.lower() == "quit":
        logger.info("The session was aborted at the event code prompt")
        sys.exit(0)

    logger.info(f"The event code for this session is {eventCode}")

    # TODO: Add an event code check here to make sure the code is legit

    # Get the MongoDB database to read the data from.  Abort if we fail
    # on the primary server.  We wont try to also read from the secondary
    # since it is 100% optional and not needed in this version of the script.

    db: Database = get_database(creds.PRIMARY_CONNECTION_STRING, cfg.DB_NAME)

    if db is None:
        err_msg: str = "Failed to connect to the primary database.  Exiting!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        sys.exit(1)

    # ALL team data goes into the V5_COL_TEAMS collection

    eventCollection: Collection = db[cfg.V5_COL_EVENTS]

    # A secondary database and collection are optional.  If we have them then
    # get the MongoDB database and collection set up as well.

    eventCollection2: Collection = None

    if creds.SECONDARY_CONNECTION_STRING:
        db2: Database = get_database(creds.SECONDARY_CONNECTION_STRING, cfg.DB_NAME)

        if db2 is None:
            err_msg: str = "Failed to connect to the secondary database.  Exiting!"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            sys.exit(1)

        # ALL team data goes into the V5_COL_TEAMS collection.

        eventCollection2: Collection = db2[cfg.V5_COL_EVENTS]

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Note the use of [0] below to force unpacking the first value
        # of the returned tuple.  Otherwise you will ALWAYS see a
        # 'truthy' value resulting in bogus behavior!
        if is_TBA_down(api_client)[0]:
            print(f"The TBA API is {Fore.RED}DOWN{Style.RESET_ALL}.")
            sys.exit(0)

        # Create an instance of the API class
        teamAPI = TeamApi(api_client)

        # Get the registered team list from TBA
        team_data = get_event_teams(teamAPI, eventCode)

        if team_data:
            saveDataToMongo(team_data, eventCollection, "Primary")

            if eventCollection2 is not None:
                saveDataToMongo(team_data, eventCollection2, "Secondary")


###############################################################################
###############################################################################
#   Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":
    main()
