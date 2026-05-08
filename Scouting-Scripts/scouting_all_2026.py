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
from typing import Any, Dict, List, Optional

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
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
        f"{eventCode}_{matchData['compLevel']}{matchData['matchNumber']}_frc{matchData['team']}"
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
def main() -> None:
    global eventCode

    # To see coloring on Windows consoles you need to have this
    # colorama call BEFORE doing ANY output.
    init(autoreset=True, convert=True)

    # Make sure the config data we need exists and is NOT empty.  Any failures
    # with the configuration will prevent the code from continuing on.
    validate_configuration()

    # Construct the replay log file for the tablet data for this run
    replayFile = f"ScoutingAll_{datetime.now().strftime('%Y%m%d_%H%M%S')}.data"
    status_msg: str = f"The data log for this session is {replayFile}"
    get_logger().info(status_msg)
    print(status_msg)

    while True:
        eventCode = input(
            "Enter the event code for the event you are scouting (or 'quit' to exit): "
        ).strip()

        if eventCode.lower() == "quit":
            get_logger().info("The session was aborted at the event code prompt")
            sys.exit(0)

        # Make sure we get an event code that begins with a '2'
        if eventCode.startswith("2"):
            break

        print("\n\nHEY!  That is not a valid event code!  Try again...\n")

    get_logger().info(f"The event code for this session is {eventCode}")

    # Get the MongoDB database to save the data into.  Abort if we fail
    # on the primary server but NOT on the secondary since it is 100%
    # optional.

    db: Database = get_database(creds.PRIMARY_CONNECTION_STRING, cfg.DB_NAME)

    if db is None:
        err_msg: str = "ERROR: Failed to connect to the primary database. Exiting!"
        get_logger().error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        err_msg = "Did you start the MongoDB server or use the wrong URL?!"
        get_logger().error(err_msg)
        print(f"{Fore.YELLOW}{err_msg}")
        sys.exit(1)

    # ALL scouting data goes into the scouting collection.

    scoutingCollection: Collection = db[cfg.V5_COL_SCOUTING]

    # A secondary database and collection are optional.  If we have them then
    # get the MongoDB database and collection set up as well.

    scoutingCollection2: Optional[Collection] = None

    if creds.SECONDARY_CONNECTION_STRING:
        db2: Database = get_database(creds.SECONDARY_CONNECTION_STRING, cfg.DB_NAME)

        if db2 is None:
            err_msg = "ERROR: Failed to connect to the secondary database. Exiting!"
            get_logger().error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            err_msg = "Did you start the MongoDB server or use the wrong URL?!"
            get_logger().error(err_msg)
            print(f"{Fore.YELLOW}{err_msg}")
            sys.exit(1)

        scoutingCollection2 = db2[cfg.V5_COL_SCOUTING]

    while True:
        tabletData: str = input("Scan a tablet now (or 'quit' to exit): ").strip()

        if tabletData.lower() == "quit":
            break

        get_logger().debug(f"The tablet data: {tabletData}")

        # Step 1: Parse JSON
        try:
            matchData = json.loads(tabletData)
        except json.JSONDecodeError:
            err_msg = "ERROR: NOT a valid JSON string!  Try again."
            get_logger().error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            continue

        # Step 2: Read and strip the routing key
        mo = matchData.get("mo")

        if mo is None:
            err_msg = "ERROR: QR code is missing the 'mo' mode key. Data rejected."
            get_logger().error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            continue

        matchData.pop("mo")

        # Step 3: Dispatch to the correct inflate function
        if mo == "s":
            inflated = inflate_match_data(matchData)
        elif mo == "d":
            inflated = inflate_defense_data(matchData)
        else:
            err_msg = f"ERROR: Unknown mode '{mo}'. Data rejected."
            get_logger().error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            continue

        # Step 4: Only continue if inflate succeeded
        if inflated is None:
            continue

        # Step 5: Save raw scan to replay file
        with open(replayFile, "a", encoding="utf-8") as file:
            file.write(tabletData + "\n")

        # Step 6: Save to MongoDB
        if mo == "s":
            inflated["eventCode"] = eventCode
            matchID = inflated["_id"]

            scoutingCollection.update_one({"_id": matchID}, {"$set": inflated}, upsert=True)

            if scoutingCollection2 is not None:
                scoutingCollection2.update_one({"_id": matchID}, {"$set": inflated}, upsert=True)

        elif mo == "d":
            for team_prefix in tqdm(["r1", "r2", "r3", "b1", "b2", "b3"], desc="Processing Teams"):
                team_num: str = str(inflated[f"{team_prefix}teamNum"])
                id_to_use = (
                    f"{eventCode}_{inflated['compLevel']}{inflated['matchNumber']}_frc{team_num}"
                )
                team_data: Dict[str, Any] = {
                    "defense": inflated[f"{team_prefix}defense"],
                    "defenseScouter": inflated["scouter"],
                    "eventCode": eventCode,
                    "docType": inflated["docType"],
                }

                scoutingCollection.update_one({"_id": id_to_use}, {"$set": team_data}, upsert=True)

                if scoutingCollection2 is not None:
                    scoutingCollection2.update_one(
                        {"_id": id_to_use}, {"$set": team_data}, upsert=True
                    )


if __name__ == "__main__":
    main()
