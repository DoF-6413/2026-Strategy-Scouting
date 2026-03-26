# This Python script is used to copy scouting data from a file to a MongoDB.
# It can be expanded later to handle other collections as well (or be used as
# a model for making a more comprehensive script/GUI that can do more).
#

# NOTE: If the imports below fail, make sure you are running this script via uv:
#
# uv run --package frc-6413-scouting-scripts python Scouting-Scripts/file_to_MongoDB_v1.py
#
# NOTE: There was a change between Python 3.11 and 3.12 regarding where to
# import the Logging for type annoations.
# In Python 3.12 and later, logging.Logger is the correct type to use. You can
# also import it from the typing module, but it's redundant.
# In Python 3.11 and earlier, the Logger class is only available within the
# logging module.  You MUST use logging.Logger directly.
# So, for compatibility with Python 3.11 and later (including 3.12), the most
# robust approach is to always use logging.Logger directly and not import it
# from typing.

import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, Union, List, Tuple, Optional, TextIO
from colorama import init, Fore, Style
from pymongo.database import Database
from pymongo.collection import Collection
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
        "ALL_TEAMS_DETAILED"
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
def copyScoutingDocuments(srcDocuments: List[dict], dstCollection: Collection, eventCode: str) -> None:
    """
    Copies scouting documents from a list of dictionaries to a MongoDB database,
    filtering by eventCode and using _id for uniqueness, with a progress bar.

    Args:
        srcDocuments (list): Source scouting data list of dictionaries.

        dstCollection (Collection): Destination MongoDB database object.

        eventCode (str): The TBA event code select the docs to copy
    """
    logger: logging.Logger = get_logger()

    try:
        # In the interest of having MUCH easier to read code we need to do
        # 2 network transactions to the source MongoDB server so we can give
        # a nice progress bar while it works.
        total_count = len(srcDocuments)

        logger.info(f"There are {total_count} documents to copy")

        with tqdm(total=total_count, desc=f"Copying {eventCode} documents") as pbar:
            for document in srcDocuments:
                print(document)
                dstCollection.replace_one({"_id": document["_id"]}, document, upsert=True)
                pbar.update(1)

        status_msg: str = f"Successfully copied {total_count} documents for eventCode '{eventCode}'"
        logger.info(status_msg)
        print(status_msg)

    except Exception as e:
        err_msg: str = f"An unexpected error occurred: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        return

###############################################################################
###############################################################################
def getEntriesFromFile(file_name: str) -> List[dict] | None:
    """
    Access a file and return the data from it as a list of objects,

    Args:
        file_name (str): The name of the local file to get entries from.
    """
    logger: logging.Logger = get_logger()

    try:
        with open(file_name, "r", encoding="utf8") as f:
            data: List[dict] = json.load(f)

            if len(data) == 0:
                err_msg: str = f"ERROR: No valid JSON scouting data was found in {file_name}"
                logger.error(err_msg)
                print(f"{Fore.RED}{err_msg}")
                sys.exit(0)
            
            status_msg: str = f"Found {len(data)} entries in {file_name}"
            logger.info(status_msg)
            print(status_msg)
            
            return data

    except Exception as e:
        err_msg: str = f"ERROR: An unexpected error occurred while reading the file: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        sys.exit(1)

###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
def main() -> None:
    logger: logging.Logger = get_logger()

    # To see coloring on Windows consoles you need to have this
    # colorama call BEFORE doing ANY output.
    init(autoreset=True, convert=True)

    # Make sure the config data we need exists and is NOT empty.  Any failures
    # with the configuration will prevent the code from continuing on.
    validate_configuration()

    # Alert the user as to what we plan to do so they do not get surprised!
    print(f"{Fore.RED}WARNING:")
    print("This script will copy ALL scouting data from a given file to your primary MongoDB server")
    print(f"{Fore.RED}Quit now if this is NOT what you want to happen!!\n")

    # Prompt user for event code
    eventCode: str = input("Enter the event code to copy scouting data for ('quit' to exit): ").strip()

    if eventCode.lower() == "quit":
        logger.info("The session was aborted at the event code prompt")
        sys.exit(0)

    logger.info(f"The event code for this session is {eventCode}")

    # Get the file to read the data from.  Abort if we fail to have one set.
    fileName: str = input("Enter the name of the file to read the data from ('quit' to exit): ").strip()

    if fileName.lower() == "quit":
        logger.info("The session was aborted at the file name prompt")
        sys.exit(0)

    srcDocuments: List[dict] = getEntriesFromFile(fileName)

    # Get the MongoDB database to copy the data into.  Abort if it is not
    # specified or we cannot connect to it.
    dstDb: Database = get_database(creds.PRIMARY_CONNECTION_STRING, cfg.DB_NAME)

    if dstDb is None:
        err_msg: str = "Failed to connect to the primary database.  Exiting!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        sys.exit(1)

    dstCollection: Collection = dstDb.get_collection(cfg.V5_COL_SCOUTING)

    # Ok, time to copy the scouting docs...
    copyScoutingDocuments(srcDocuments, dstCollection, eventCode)

###############################################################################
###############################################################################
if __name__ == "__main__":
    main()
