# This Python script will take the DEFENSE scouting data from scanned QR codes
# (as JSON), reinflate and expand it before putting it into a MongoDB
# database or two.
#
# This is the initial 2026 version of the defense_scouting_2026_v# script.  It
# starts as a copy of the last defense_scouting_2025_v#.py script.
#

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import config as cfg
from colorama import Fore, init
from pymongo.collection import Collection
from pymongo.database import Database
from tqdm import tqdm

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
            log_file = f"ScriptLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
    badConfig = False
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

    First do credential checks and then do schema specific checks.  We only
    check the current schema and not all possible schemas.
    '''
    import credentials as creds

    # Scan ALL configuration settings and report all bad ones before we exit
    # That way we do not make the user edit the configuration multiple times.

    badConfig = False
    badV5Config = False
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
        A Database if we connected successfully, None otherwise
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
    except Exception as e:
        err_msg: str = f"ERROR: Failed to access the database: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")

    return None


###############################################################################
###############################################################################
def inflate_tablet_data(tabletData: str) -> Optional[Dict[str, Union[str, int]]]:
    '''
    Parse and "inflate" the given tablet JSON data into a dictionary that we
    then process further before returning to our caller.

    Parameters:
        tabletData (str): The match scouting data from a tablet (a JSON
            dictionary string)

    Returns:
        A dictionary with the tablet data in it OR nothing if it was not JSON
            data.
    '''
    logger: logging.Logger = get_logger()

    # Make sure we can parse the data into JSON data before we try to do anything else

    try:
        matchData = json.loads(tabletData)

    except json.JSONDecodeError:
        err_msg: str = "ERROR: NOT a valid JSON string!  Try again."
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        return

    # We got JSON so lets do any touch up we need to.
    # "Reinflate" the key names before we save them into the database.
    #
    # We reinflate the encoded red and blue defense and team number values
    # since it makes it easier to iterate over them when we go to save the
    # data into MongoDB

    key_mapping = {
        "cl": "compLevel",
        "mn": "matchNumber",
        "i": "scouter",
        "r1": "r1defense",
        "r2": "r2defense",
        "r3": "r3defense",
        "r4": "r1teamNum",
        "r5": "r2teamNum",
        "r6": "r3teamNum",
        "b1": "b1defense",
        "b2": "b2defense",
        "b3": "b3defense",
        "b4": "b1teamNum",
        "b5": "b2teamNum",
        "b6": "b3teamNum",
    }

    # Inflate all the keys we expect.  If one is missing, DO NOT continue or
    # return any data to avoid corrupting the database.  Leave it to an admin
    # to look into this error report and resolve the issue based on the saved
    # raw data.
    for short_key, long_key in key_mapping.items():
        if short_key in matchData:  # Check if the short key exists
            matchData[long_key] = matchData.pop(short_key)
        else:
            err_msg: str = f"QR code key {short_key} was NOT found!"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            return

    # Add the correct docType to the data
    matchData['docType'] = cfg.DT_SCOUTING_MATCH

    # NOTE: We CANNOT do this _id generation here because we have the data for
    # 6 teams.  We will need to do this generation as we prepare to insert the
    # data into the database(s)

    return matchData


###############################################################################
###############################################################################
def main() -> None:
    import credentials as creds

    logger: logging.Logger = get_logger()

    # To see coloring on Windows consoles you need to have this
    # colorama call BEFORE doing ANY output.
    init(autoreset=True, convert=True)

    # Make sure the config data we need exists and is NOT empty.  Any failures
    # with the configuration will prevent the code from continuing on.
    validate_configuration()

    # Construct the replay log file for the tablet data for this run
    replayFile = f"DefenseScoutingData_{datetime.now().strftime('%Y%m%d_%H%M%S')}.data"

    status_msg: str = f"The data log for this session is {replayFile}"
    logger.info(status_msg)
    print(status_msg)

    while True:
        eventCode: str = input("Enter the event code for the event you are DEFENSE scouting (or 'quit' to exit): ").strip()

        if eventCode.lower() == "quit":
            logger.info("The session was aborted at the event code prompt")
            sys.exit(0)

        # Make sure we get an event code that begins with a '2'
        if eventCode.startswith('2'):
            break

        print("\n\nHEY!  That is not a valid event code!  Try again...\n")

    logger.info(f"The event code for this session is {eventCode}")

    # Get the MongoDB database to save the data into.  Abort if we fail
    # on the primary server but NOT on the secondary since it is 100%
    # optional.

    db: Database = get_database(creds.PRIMARY_CONNECTION_STRING, cfg.DB_NAME)

    if db is None:
        err_msg: str = "ERROR: Failed to connect to the database. Exiting..."
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        sys.exit(1)

    # ALL scouting data goes into the scouting collection.

    scoutingCollection: Collection = db[cfg.V5_COL_SCOUTING]

    # A secondary database and collection are optional.  If we have them then
    # get the MongoDB database and collection set up as well.

    scoutingCollection2: Collection = None

    if creds.SECONDARY_CONNECTION_STRING:
        db2: Database = get_database(creds.SECONDARY_CONNECTION_STRING, cfg.DB_NAME)

        if db2 is None:
            err_msg: str = "ERROR: Failed to connect to the secondary database. Exiting..."
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            sys.exit(1)

        # ALL scouting data goes into the scouting collection.

        scoutingCollection2: Collection = db2[cfg.V5_COL_SCOUTING]

    # The team suffixes we use during our main saving loop to do one team at a time
    teams = ["r1", "r2", "r3", "b1", "b2", "b3"]

    while True:
        tabletData: str = input("Scan a DEFENSE tablet now (or 'quit' to exit): ").strip()

        if tabletData.lower() == "quit":
            break

        logger.debug(f"The tablet data: {tabletData}")

        matchData = inflate_tablet_data(tabletData)

        # Only do additional work if we got back a dictionary.  Any other
        # return values should be ignored and we just try again!

        if isinstance(matchData, dict):
            # First off, the tablet data was ok so save a copy to our replay
            # file before we do anything else.

            with open(replayFile, "a", encoding="utf-8") as file:
                file.write(tabletData + "\n")

            # Now we loop over the data and do an update/insert for each team

            for team_prefix in tqdm(teams, desc="Processing Teams"):
                team_num: str = str(matchData[f"{team_prefix}teamNum"])

                id_to_use = f"{eventCode}_{matchData['compLevel']}{str(matchData['matchNumber'])}_frc{team_num}"

                team_data: Dict[str, Any] = {
                    "defense": matchData[f"{team_prefix}defense"],
                    "defenseScouter": matchData['scouter'],
                    "eventCode": eventCode,
                    "docType": matchData['docType']
                }

                result = scoutingCollection.update_one({"_id": id_to_use}, {"$set": team_data}, upsert=True)

                if result.upserted_id:
                    logger.debug(f"Inserted data into {id_to_use} (Primary)")
                elif result.modified_count > 0:
                    logger.debug(f"Updated data for {id_to_use} (Primary)")
                else:
                    logger.debug(f"No changes made to {id_to_use} (Primary)")

                if scoutingCollection2 is not None:
                    result = scoutingCollection2.update_one({'_id': id_to_use}, {"$set": team_data}, upsert=True)

                    if result.upserted_id:
                        logger.debug(f"Inserted data into {id_to_use} (Secondary)")
                    elif result.modified_count > 0:
                        logger.debug(f"Updated data for {id_to_use} (Secondary)")
                    else:
                        logger.debug(f"No changes made to {id_to_use} (Secondary)")


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":
    main()
