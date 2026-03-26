# This Python script will take scouting data from scanned QR codes (as JSON)
# and then do any touch up and data checking before putting it into a MongoDB
# database or two.
#
# It is intended to collect the QR code data from a scout and compare it to the
# "ground truth" scouting data saved in the V5_COL_TRAINING collection.
#
# This is based on the training_collection_2025_v1.py script.

# NOTE: If the imports fail below, make sure you are using the venv environment
# where the TBA and PyMongo Python libraries are installed.  They are NOT
# installed in the base, scrapy, OR Anaconda environments!!

import logging
import json
import re
import sys
import os
from datetime import datetime
from typing import Dict, Union, List, Optional
from colorama import init, Fore, Style
from pymongo.database import Database
from pymongo.collection import Collection
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
    badConfig: bool = False
    logger: logging.Logger = get_logger()

    for param_name in params:
        param_value = getattr(cfg, param_name, None)

        if not param_value:  # Check for None or empty string
            err_msg: str = f"ERROR: {param_name} is missing or empty!"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
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
        "V5_COL_TRAINING",
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
    # Scan ALL configuration settings and report all bad ones before we exit
    # That way we do not make the user edit the configuration multiple times.

    badConfig = False
    badV5Config = False
    logger: logging.Logger = get_logger()

    # The PRIMARY_CONNECTION_STRING MUST exist and be non-NULL!

    if not ( hasattr( creds, "PRIMARY_CONNECTION_STRING" ) and creds.PRIMARY_CONNECTION_STRING ):
        err_msg: str = "ERROR: PRIMARY_CONNECTION_STRING is missing or empty!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
        badConfig = True

    # The SECONDARY_CONNECTION_STRING MUST exist but CAN be empty.

    if not ( hasattr( creds, "SECONDARY_CONNECTION_STRING" ) ):
        err_msg: str = "ERROR: SECONDARY_CONNECTION_STRING is missing!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
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
    ## from pymongo.errors import AuthenticationError

    logger: logging.Logger = get_logger()

    # Create a connection to the specified MongoDB server

    try:
        client: MongoClient = MongoClient(databaseURI)

        # Use/Create the database to hold our data
        return client[databaseName]
    except ConnectionError as e:
        err_msg: str = f"ERROR: Failed to connect to MongoDB server: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
    except AuthenticationError as e:
        err_msg: str = f"ERROR: Failed to authenticate with MongoDB: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
    except Exception as e:
        err_msg: str = f"ERROR: Failed to access the database {databaseName}: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")

    return None


###############################################################################
###############################################################################
def inflate_tablet_data(tabletData: str)  -> Optional[Dict[str, Union[str, int]]]:
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

    # Make sure we can parse the data into JSON data before we try to do
    # anything else

    try:
        matchData = json.loads(tabletData)

    except json.JSONDecodeError:
        err_msg: str = "ERROR: NOT a valid JSON string!  Try again."
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
        return

    # We got JSON so lets do any touch up we need to.
    # "Reinflate" the key names before we save them into the database.

    key_mapping = {
        "cl": "compLevel",
        "mn": "matchNumber",
        "i": "scouter",
        "a1": "autoL4",
        "a2": "autoL4Miss",
        "a3": "autoL3",
        "a4": "autoL3Miss",
        "a5": "autoL2",
        "a6": "autoL2Miss",
        "a7": "autoL1",
        "a8": "autoL1Miss",
        "a9": "autoNet",
        "a10": "autoNetMiss",
        "a11": "autoProcessor",
        "a12": "autoProcessorMiss",
        "t1": "teleL4",
        "t2": "teleL4Miss",
        "t3": "teleL3",
        "t4": "teleL3Miss",
        "t5": "teleL2",
        "t6": "teleL2Miss",
        "t7": "teleL1",
        "t8": "teleL1Miss",
        "t9": "teleNet",
        "t10": "teleNetMiss",
        "t11": "teleProcessor",
        "t12": "teleProcessorMiss",
        "t13": "climb",
        "c": "card",
        "ns": "noShow",
        "d": "died",
        "r": "role",
        "co": "comments"
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
            print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
            return

    # Lets tidy up the comments value so it renders nicely wherever we show it:
    #
    # 1: Remove all embedded newlines
    # 2: Get rid of extra whitespace inside the comments.
    # 3: Trim off any leading or trailing whitespace while
    matchData[ "comments" ] = re.sub(r'\s+', ' ', matchData[ "comments" ].replace("\n", " ")).strip()

    # For Streamlits benefit we remove the TBA prefix.
    matchData[ "team" ] = str( matchData[ 'key' ] )

    # Set the _id value of the entry to be a combination of the event code,
    # match type & number plus the team number.

    id_to_use = eventCode + "_" + matchData[ 'compLevel' ] + str( matchData[ 'matchNumber' ] ) + "_frc" + matchData[ "team" ]

    matchData[ '_id' ] = id_to_use

    return matchData


###############################################################################
###############################################################################
def compare_to_mongo(trainingCollection: Collection, matchData: Dict[str, Union[str, int]]) -> None:
    """
    Compares a dictionary with a MongoDB record and prints mismatches

    Args:
        trainingCollection: The MongoDB training data collection
        matchData: The dictionary containing the data to compare, including the _id.
    """
    logger: logging.Logger = get_logger()

    recordKey = matchData.get("_id")

    if recordKey is None:
        err_msg: str = "ERROR: '_id' key not found in matchData."
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
        return

    mongo_record = trainingCollection.find_one({"_id": recordKey})

    if mongo_record is None:
        err_msg: str = f"ERROR: NO record with _id '{recordKey}' found!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
        return

    # We start with no mismatched values
    mismatch_found: bool = False

    # Keys we do not need to compare after post AZ East data change
    skip_keys = {"scouter", "comments", "_id", "autoL4Miss", "autoL3Miss", "autoL2Miss", "autoL1Miss", "autoNetMiss", "autoProcessorMiss", "teleL4Miss", "teleL3Miss", "teleL2Miss", "teleL1Miss", "teleNetMiss", "teleProcessorMiss"}

    # Check all keys in matchData against the MongoDB record
    for key, scout_value in matchData.items():
        if key in skip_keys:
            continue

        mongo_value = mongo_record.get(key)
        if mongo_value != scout_value:
            err_msg: str = f"Mismatch with {key}: {scout_value} (scout) vs {mongo_value} (MongoDB)"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
            mismatch_found = True

    if not mismatch_found:
        success_msg: str = "SUCCESS! All data matched."
        logger.error(success_msg)
        print(f"{Fore.GREEN}{success_msg}{Style.RESET_ALL}")


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
def main() -> None:
    global eventCode

    # To see coloring on Windows consoles you need to have this
    # colorama call BEFORE doing ANY output.
    init(autoreset=True, convert=True)

    # Make sure the config data we need exists and is NOT empty.  Any failures
    # with the configuration will prevent the code from continuing on.
    validate_configuration()

    logger: logging.Logger = get_logger()

    # Construct the replay log file for the tablet data for this run
    replayFile = f"ScoutTrainingData_{datetime.now().strftime('%Y%m%d_%H%M%S')}.data"
    logger.info(f"The data log for this session is {replayFile}")

    eventCode: str = input("Enter the event code for the event you are VALIDATING training for (or 'quit' to exit): ").strip()

    if eventCode.lower() == "quit":
        logger.info("The session was aborted at the event code prompt")
        sys.exit(0)

    logger.info(f"The event code for this training session is {eventCode}")

    # Get the MongoDB database to save the data into.  Abort if we fail
    # on the primary server.

    db: Database = get_database(creds.PRIMARY_CONNECTION_STRING, cfg.DB_NAME)

    if db is None:
        err_msg: str = "Failed to connect to the database.  Exiting!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}{Style.RESET_ALL}")
        sys.exit(1)

    # ALL scout training data goes is in the training collection.

    trainingCollection: Collection = db[cfg.V5_COL_TRAINING]

    while True:
        tabletData: str = input("Scan a tablet now (or 'quit' to exit): ").strip()

        logger.debug(f"The tablet data: {tabletData}")

        if tabletData.lower() == "quit":
            break

        matchData = inflate_tablet_data(tabletData)

        # Only do additional work if we got back a dictionary.  Any other
        # return values should be ignored and we just try again!

        if isinstance(matchData, dict):
            # Add the TBA eventCode to the dictionary we have before we go on.

            matchData[ "eventCode" ] = eventCode

            # The tablet data was ok so lets save a copy to our replay file
            # before we do anything else.

            with open(replayFile, "a", encoding="utf-8") as file:
                file.write(tabletData + "\n")

            # Time to save the re-inflated data to a MongoDB (or two)

            matchID = matchData[ "_id" ]

            compare_to_mongo(trainingCollection, matchData)


if __name__ == "__main__":
    main()
