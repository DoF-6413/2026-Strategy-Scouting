# This Python script will take scouting data from scanned QR codes (as JSON)
# and then do any touch up and data checking before putting it into a MongoDB
# database or two.
#
# This script combines the functionality of scouting_2026_v2.py and
# defense_scouting_2026_v2.py into a single entry point.  A "mo" key in the
# QR code JSON determines which inflate path to use:
#
#   mo = "s"  ->  match scouting
#   mo = "d"  ->  defense scouting
#   mo absent ->  invalid; data is rejected and not saved
#
# The "mo" key is stripped from the data before inflation and is never written
# to MongoDB.

import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from colorama import Fore, init
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
from pymongo.collection import Collection
from pymongo.database import Database
from tqdm import tqdm

_logger: Optional[logging.Logger] = None
eventCode: str = ""


###############################################################################
###############################################################################
def setup_logger() -> logging.Logger:
    """
    Sets up a logger that saves any log output to a file in the script's
    directory, with a filename based on the current date and time.
    """
    global _logger

    if _logger is None:
        _logger = logging.getLogger(__name__)
        _logger.setLevel(logging.WARNING)

        if not _logger.handlers:
            log_file = f"ScriptLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_file_path = os.path.join(script_dir, log_file)
            handler = logging.FileHandler(log_file_path)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)

    return _logger


###############################################################################
###############################################################################
def get_logger() -> logging.Logger:
    """
    Returns the script's logger, initializing it if it hasn't been already.
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
    logger = get_logger()

    for param_name in params:
        param_value = getattr(cfg, param_name, None)

        if not param_value:
            err_msg: str = f"ERROR: {param_name} is missing or empty!"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            badConfig = True

    return badConfig


###############################################################################
###############################################################################
def is_V5_configuration_bad() -> bool:
    """
    Tell the caller if any V5 schema specific configuration information is
        bad or missing.

    Returns:
        bool: True if any V5 schema values are missing or empty, False otherwise.
    """
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
        "PRESCOUTING_FIELDS",
    ]

    return check_config_params(cfg, v5_values_to_check)


###############################################################################
###############################################################################
def validate_configuration() -> None:
    """
    Validate that the necessary configuration and credential information exists.

    First do credential checks and then do schema specific checks.  We only
    check the current schema and not all possible schemas.
    """
    logger = get_logger()

    badConfig = False
    badV5Config = False

    if not (hasattr(creds, "PRIMARY_CONNECTION_STRING") and creds.PRIMARY_CONNECTION_STRING):
        err_msg: str = "ERROR: PRIMARY_CONNECTION_STRING is missing or empty!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        badConfig = True

    if not hasattr(creds, "SECONDARY_CONNECTION_STRING"):
        err_msg = "ERROR: SECONDARY_CONNECTION_STRING is missing!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        badConfig = True

    badV5Config = is_V5_configuration_bad()

    if badConfig or badV5Config:
        sys.exit(2)


###############################################################################
###############################################################################
def get_database(databaseURI: str, databaseName: str) -> Optional["Database"]:
    """
    Returns a MongoDB database to read/write the all your data from/into OR
        None if there was a problem accessing the database.

    The collection to use is pulled from the configuration data so we use
        the same one for all databases.

    Parameters:
        databaseURI (str): The database connection URL to use

        databaseName (str): The name of the database to access

    Returns:
        A Database if we connected successfully, None otherwise
    """
    from pymongo import MongoClient

    logger = get_logger()

    try:
        client: MongoClient = MongoClient(databaseURI, serverSelectionTimeoutMS=15000)
        client.admin.command("ping")
        return client[databaseName]
    except ConnectionError as e:
        err_msg = f"ERROR: Failed to connect to MongoDB server: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
    except Exception as e:
        err_msg = f"ERROR: Failed to access the database: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")

    return None


###############################################################################
###############################################################################
def inflate_match_data(matchData: Dict) -> Optional[Dict]:
    """
    "Inflate" the compact match scouting JSON keys to their full names and
    compute derived fields.

    Parameters:
        matchData: Already-parsed dict with "mo" already popped off.

    Returns:
        The inflated dict, or None if any expected key was missing.
    """
    logger = get_logger()

    key_mapping = {
        "cl": "compLevel",
        "mn": "matchNumber",
        "i": "scouter",
        "a1": "autoHub",
        "a2": "autoHubMiss",
        "t1": "teleHub",
        "t2": "teleHubMiss",
        "ns": "noShow",
        "r": "relayed",
        "h": "herded",
        "d": "died",
        "co": "comments",
    }

    for short_key, long_key in key_mapping.items():
        if short_key in matchData:
            matchData[long_key] = matchData.pop(short_key)
        else:
            err_msg: str = f"QR code key {short_key} was NOT found!"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            return None

    comments = matchData["comments"]
    matchData["comments"] = re.sub(r"\s+", " ", comments.replace("\n", " ")).strip()

    matchData["docType"] = cfg.DT_SCOUTING_MATCH
    matchData["team"] = str(matchData["key"])
    matchData["totalGamePieces"] = matchData["autoHub"] + matchData["teleHub"]

    id_to_use = (
        f"{eventCode}_"
        f"{matchData['compLevel']}"
        f"{matchData['matchNumber']}_frc"
        f"{matchData['team']}"
    )
    matchData["_id"] = id_to_use

    return matchData


###############################################################################
###############################################################################
def inflate_defense_data(matchData: Dict) -> Optional[Dict]:
    """
    "Inflate" the compact defense scouting JSON keys to their full names.

    Parameters:
        matchData: Already-parsed dict with "mo" already popped off.

    Returns:
        The inflated dict, or None if any expected key was missing.
        NOTE: _id is NOT generated here; it is generated per-team in the save loop.
    """
    logger = get_logger()

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

    for short_key, long_key in key_mapping.items():
        if short_key in matchData:
            matchData[long_key] = matchData.pop(short_key)
        else:
            err_msg: str = f"QR code key {short_key} was NOT found!"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            return None

    matchData["docType"] = cfg.DT_SCOUTING_MATCH

    return matchData


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":
    pass
