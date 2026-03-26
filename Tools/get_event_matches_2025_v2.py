# A sample Python script to get the list of event matches at a selected
# Regional from TBA. The results of that are then stored into the MongoDB
# database(s).
#
# This is an updated version of the get_event_matches_2025_v1.py
# script.  It has the following changes:
#
# 1: Added tqdm to show progress saving data to MongoDB
#
# NOTE: If the imports below fail, make sure you are using the venv environment
# where the TBA libraries are installed.  They are NOT installed in the base OR
# scrapy environments!!

import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Union, Tuple, Optional
# import tbaapiv3client
from tbaapiv3client.api import TBAApi, EventApi
from tbaapiv3client.api_client import ApiClient
from tbaapiv3client.configuration import Configuration
from tbaapiv3client.rest import ApiException
from pymongo.database import Database
from pymongo.collection import Collection
from colorama import init, Fore, Style
from urllib3.exceptions import MaxRetryError
from tqdm import tqdm
import config as cfg
import credentials as creds

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
            log_file = f"ToolLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
        err_msg: str = f"ERROR: Exception when calling TBAApi.get_status: {e}\n"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}\n")
        return True, None, None  # Treat any exception as API being down
    except MaxRetryError:
        # This can happen if there is no network connectivity such as no WiFi
        # or TBA is actually down!
        err_msg: str = "Unable to reach TBA.  Please check your network connection and try again!"
        logger.error(err_msg)
        print(f"\n{Fore.RED}{err_msg}\n")
        return True, None, None  # Treat any exception as API being down


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
    # Scan ALL configuration settings and report all bad ones before we exit
    # That way we do not make the user edit the configuration multiple times.

    badConfig: bool = False
    badV5Config: bool = False
    logger: logging.Logger = get_logger()

    # The PRIMARY_CONNECTION_STRING MUST exist and be non-NULL!

    if not ( hasattr( creds, "PRIMARY_CONNECTION_STRING" ) and creds.PRIMARY_CONNECTION_STRING ):
        err_msg: str = "ERROR: PRIMARY_CONNECTION_STRING is missing or empty!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        badConfig = True

    # The SECONDARY_CONNECTION_STRING MUST exist but CAN be empty.

    if not ( hasattr( creds, "SECONDARY_CONNECTION_STRING" ) ):
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
def get_database( databaseURI: str, databaseName: str ) -> Optional["Database"]:
    '''
    Returns a MongoDB database to read/write the all your data from/into OR
        None if there was a problem accessing the database.

    The collection to use is pulled from the configuration data so we use
        the same one for all databases.

    Parameters:
        databaseURI (str): The database connection URL to use

        databaseName (str): The name of the database to access

    Returns:
        A Database if we connected successfully, None if we failed for any reason!
    '''
    from pymongo import MongoClient

    logger: logging.Logger = get_logger()

    # Create a connection to the specified MongoDB server

    try:
        client: MongoClient = MongoClient( databaseURI )

        # Use/Create the database to hold our data
        return client[ databaseName ]
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
def convertMatchToSchedule(schedule: Dict[str, Union[str, int]]) -> Dict[str, Union[str, int]]:
    '''
    Trim down the given schedule dict to just be the data we want from the
    Match data and not all the "extra stuff" that is not useful when just
    referencing the schedule!

    Parameters:
        schedule (dict): A dict copy of Match data to prune down

    Returns:
        dict: A pruned dict containing only the desired data.
    '''
    schedule.pop('actual_time', None)
    schedule.pop('post_result_time', None)
    schedule.pop('predicted_time', None)
    schedule.pop('score_breakdown', None)
    schedule.pop('time', None)
    schedule.pop('videos', None)
    schedule.pop('winning_alliance', None)

    # Cleaning out nested dicts isn't easy unless you use some special libs like python-benedict.
    # See https://stackoverflow.com/questions/43491287/elegant-way-to-check-if-a-nested-key-exists-in-a-dict
    # We could scan the keys down all the way like in keys_exists() which we
    # used to do or we can make slightly cleaner code and use for loops.
    # How grok the following code:
    #  - schedule.get('alliances', {}) retrieves the 'alliances' dictionary if
    #        it exists, otherwise, it returns an empty dictionary.
    #  - .values() accesses the values of the 'alliances' dictionary, which are
    #        the nested dictionaries ('blue' and 'red').
    #  - The outer loop iterates over each nested dictionary ('blue' and 'red').
    #  - The inner loop iterates over each key in keys_to_remove, and pop() is
    #        used to remove the key if it exists in the nested dictionary. The
    #        second argument of pop() (None in this case) ensures that if the
    #        key doesn't exist, no error will be raised.

    keys_to_remove = ['dq_team_keys', 'score', 'surrogate_team_keys']

    for alliance in schedule.get('alliances', {}).values():
        for key in keys_to_remove:
            alliance.pop(key, None)

    # We are not going to try and improve the data by moving the 'blue' and
    # 'red' nested dictionaries to the root at this time.  We already have
    # code that looks for team codes inside the alliances dictionary
    # (e.g. alliances.blue.team_keys) so leave that alone for now.

    return schedule


###############################################################################
###############################################################################
def get_event_matches(api_client: ApiClient, eventCode: str) -> Optional[List[Dict]]:
    '''
    Get the match list for the specified event.  It uses the EventApi
    call get_event_matches() so it MAY NOT function for Districts...

    Parameters:
        api_client (ApiClient): An instance of the TBA API client.

        eventCode (str): The event code to get the matches for
    '''
    logger: logging.Logger = get_logger()

    # Create an instance of the EventApi class
    eventAPI = EventApi(api_client)

    try:
        api_response = eventAPI.get_event_matches(eventCode)

        status_msg: str = f"There are {len(api_response)} matches reported for {eventCode}"
        logger.info(status_msg)
        print(status_msg)

        # Iterate over all the matches in the response and do any needed data
        # transformations.
        #
        # NOTE: Not all events in all years have match data for various reasons.
        # For instance the first couple years events such as 1993cmp and 1994cmp
        # have NO match data so TBA simply returns "[]"

        match_list = []

        for match in api_response:
            # We will now use to_dict() to safely convert the object to a dict.
            matchToSave = match.to_dict()

            # Do ourselves a favor and set the _id value of the entry to be the
            # same as the TBA match code.
            matchToSave['_id'] = matchToSave['key']

            match_list.append(matchToSave)

        # If you want to see the blue & red team numbers, use code like this:
        # for alliance_color in ['blue', 'red']:
        #     print(f"{alliance_color.upper()} Team:")
        #     for team in schedule[alliance_color]:
        #         print(f"\t- {team}")

        # pprint(scheduleToSave)

        return match_list

    except ApiException as e:
        err_msg: str = f"ERROR: APIException when calling EventApi.get_event_matches: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        return None
    except Exception as e:
        err_msg: str = f"ERROR: An unexpected error occurred: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        return None


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

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Note the use of [0] below to force unpacking the first value
        # of the returned tuple.  Otherwise you will ALWAYS see a
        # 'truthy' value resulting in bogus behavior!
        if is_TBA_down(api_client)[0]:
            print(f"The TBA API is {Fore.RED}DOWN{Style.RESET_ALL}.")
            sys.exit(0)

        eventCode: str = input("Enter the event code for the event to get data for (or 'quit' to exit): ").strip()

        if eventCode.lower() == "quit":
            logger.info("The session was aborted at the event code prompt")
            sys.exit(0)

        logger.info(f"The event code for this session is {eventCode}")

        # TODO: Add an event code check here to make sure the code is legit

        # Get the MongoDB database to save the events data into.  Abort if we
        # fail on the primary server but NOT on the secondary since it is 100%
        # optional.

        db: Database = get_database(creds.PRIMARY_CONNECTION_STRING, cfg.DB_NAME)

        if db is None:
            err_msg: str = "Failed to connect to the primary database.  Exiting!"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            sys.exit(1)

        # ALL match data goes into the V5_COL_MATCH collection and all schedule data
        # goes into the V5_COL_SCHEDULE collection

        matchCollection: Collection = db[cfg.V5_COL_MATCH]
        scheduleCollection: Collection = db[cfg.V5_COL_SCHEDULE]

        # A secondary database and collection are optional.  If we have them then
        # get the MongoDB database and collection set up as well.

        matchCollection2: Collection = None
        scheduleCollection2: Collection = None

        if creds.SECONDARY_CONNECTION_STRING:
            db2: Database = get_database(creds.SECONDARY_CONNECTION_STRING, cfg.DB_NAME)

            if db2 is None:
                err_msg: str = "Failed to connect to the secondary database.  Exiting!"
                logger.error(err_msg)
                print(f"{Fore.RED}{err_msg}")
                sys.exit(1)

            # ALL scouting data goes into the scouting collection.

            matchCollection2: Collection = db2[cfg.V5_COL_MATCH]
            scheduleCollection2: Collection = db2[cfg.V5_COL_SCHEDULE]

        # Go get the event match data from TBA
        matchData: Optional[List[Dict]] = get_event_matches(api_client, eventCode)

        # If we got match info then lets create a schedule from it before we
        # save both into MongoDB.

        if matchData:
            scheduleData: List[Dict] = []

            for match in matchData:
                # Copy the match data and trim it down to just what we need for
                # making a schedule
                scheduleToSave = convertMatchToSchedule(match.copy())

                # Lets tidy up the format of the schedule to be a little easier
                # to handle.
                # First off, remove 'alliances'
                alliances = scheduleToSave.pop('alliances')

                # Next, add just the teams back by color
                for alliance_color, team_data in alliances.items():
                    scheduleToSave[alliance_color] = team_data['team_keys']

                scheduleData.append(scheduleToSave)

            # Time to save the data.  Start with the match data
            saveDataToMongo(matchData, matchCollection, "Primary")

            if matchCollection2 is not None:
                saveDataToMongo(matchData, matchCollection2, "Secondary")

            # followed by the schedule data.
            saveDataToMongo(scheduleData, scheduleCollection, "Primary")

            if scheduleCollection2 is not None:
                saveDataToMongo(scheduleData, scheduleCollection2, "Secondary")


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":
    main()
