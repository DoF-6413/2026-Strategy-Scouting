# This script takes a random/test scouting data file (NDJSON, one JSON
# object per line, in the format produced by RandomData2026_v2.py) and an
# event code, and populates the V5_COL_MATCH and V5_COL_EVENTS collections
# so a fake test event has schedule and team-list data for the Dashboard to
# read, alongside the scouting data that RandomData2026_v2.py's output
# already feeds into via scouting_all_v2.py.
#
# It does NOT touch V5_COL_SCOUTING - that collection is populated
# separately by feeding the same random data file into scouting_all_v2.py.
#
# Only "mo":"s" (match scouting) lines are used. For each distinct match
# number, the first 3 "mo":"s" records encountered in the file (in file
# order) are treated as Red 1-3 and the next 3 as Blue 1-3. Each match MUST
# have exactly 6 such records or the run is aborted before anything is
# written to MongoDB.

import json
import logging
import os
import sys
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Optional

from colorama import Fore, init
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
from pymongo.collection import Collection
from pymongo.database import Database
from tqdm import tqdm

_logger: Optional[logging.Logger] = None

USAGE: str = """
random_data_to_mongo_v1.py - Load matches/events data for a test event.

Reads a random scouting data file (NDJSON, one JSON object per line, in the
format produced by RandomData2026_v2.py) and generates the corresponding
V5_COL_MATCH and V5_COL_EVENTS documents for the given event code, so a fake
test event has schedule and team-list data for the Dashboard.

It does NOT touch V5_COL_SCOUTING - feed the same file into
scouting_all_v2.py separately to populate scouting data.

Usage:
    python random_data_to_mongo_v1.py <random_data_file> <event_code>

Arguments:
    random_data_file   Path to the NDJSON random data file to read.
    event_code         The event code to tag the generated data with
                        (e.g. 2026test6).
"""


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
            log_file = f"ToolLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
    Check if multiple configuration parameters exist and are non-empty
    strings in the given cfg object.

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
        "V5_COL_EVENTS",
        "V5_COL_MATCH",
        "DT_EVENTS_TEAMS",
        "MATCHLEVEL_QUALIFIERS",
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
    logger: logging.Logger = get_logger()

    badConfig: bool = False

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

    Parameters:
        databaseURI (str): The database connection URL to use

        databaseName (str): The name of the database to access

    Returns:
        A Database if we connected successfully, None otherwise
    """
    from pymongo import MongoClient

    logger: logging.Logger = get_logger()

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
def parse_args(argv: List[str]) -> Optional[Dict[str, str]]:
    """
    Parse and validate the command line arguments.

    Parameters:
        argv: sys.argv (including the script name at index 0).

    Returns:
        A dict with "random_data_file" and "event_code" keys, or None if
        the arguments were missing/invalid/a help request (in which case
        the usage message has already been printed).
    """
    help_flags = {"?", "-help", "--help"}

    if len(argv) != 3 or any(arg in help_flags for arg in argv[1:]):
        print(USAGE)
        return None

    return {"random_data_file": argv[1], "event_code": argv[2]}


###############################################################################
###############################################################################
def load_match_scouting_records(random_data_file: str) -> Optional[List[Dict]]:
    """
    Read the given NDJSON random data file and return only the "mo":"s"
    (match scouting) records, in file order.

    Parameters:
        random_data_file: Path to the NDJSON random data file.

    Returns:
        A list of parsed dicts, or None if the file could not be read or
        contained invalid JSON.
    """
    logger: logging.Logger = get_logger()
    records: List[Dict] = []

    try:
        with open(random_data_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()

                if not line:
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError as e:
                    err_msg = f"ERROR: {random_data_file} line {line_num} is not valid JSON: {e}"
                    logger.error(err_msg)
                    print(f"{Fore.RED}{err_msg}")
                    return None

                if record.get("mo") == "s":
                    records.append(record)
    except FileNotFoundError:
        err_msg = f"ERROR: Random data file not found: {random_data_file}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        return None

    return records


###############################################################################
###############################################################################
def build_matches_and_events(
    records: List[Dict], event_code: str
) -> Optional[Dict[str, List[Dict]]]:
    """
    Group the given match scouting records by match number (preserving file
    order within each group) and build the V5_COL_MATCH and V5_COL_EVENTS
    documents for them.

    Parameters:
        records: Parsed "mo":"s" records, in file order.

        event_code: The event code to tag the generated data with.

    Returns:
        A dict with "matches" and "events" lists of documents, or None if
        any match did not have exactly 6 records (Red 1-3, Blue 1-3).
    """
    logger: logging.Logger = get_logger()

    # Group by match number, preserving the file order the records were
    # seen in (needed since 1st-3rd = Red, 4th-6th = Blue for each match).
    matches_by_number: "OrderedDict[int, List[Dict]]" = OrderedDict()

    for record in records:
        match_number = record["mn"]
        matches_by_number.setdefault(match_number, []).append(record)

    match_docs: List[Dict] = []
    all_teams: "OrderedDict[int, None]" = OrderedDict()

    for match_number, group in matches_by_number.items():
        if len(group) != 6:
            err_msg = (
                f"ERROR: Match {match_number} has {len(group)} scouting record(s), "
                f"expected exactly 6 (Red 1-3, Blue 1-3). Aborting - no data written."
            )
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            return None

        red_teams = [group[i]["key"] for i in range(0, 3)]
        blue_teams = [group[i]["key"] for i in range(3, 6)]

        for team in red_teams + blue_teams:
            all_teams.setdefault(team, None)

        match_key = f"{event_code}_{cfg.MATCHLEVEL_QUALIFIERS}{match_number}"

        match_docs.append(
            {
                "_id": match_key,
                "key": match_key,
                "event_key": event_code,
                "comp_level": cfg.MATCHLEVEL_QUALIFIERS,
                "match_number": match_number,
                "set_number": 1,
                "alliances": {
                    "red": {"team_keys": [f"frc{team}" for team in red_teams]},
                    "blue": {"team_keys": [f"frc{team}" for team in blue_teams]},
                },
            }
        )

    events_docs: List[Dict] = [
        {
            "_id": f"{event_code}_frc{team}",
            "docType": cfg.DT_EVENTS_TEAMS,
            "event_key": event_code,
            "team_number": team,
        }
        for team in all_teams
    ]

    return {"matches": match_docs, "events": events_docs}


###############################################################################
###############################################################################
def saveDataToMongo(data: List[Dict], db_collection: Collection, db_identifier: str) -> None:
    """
    Saves the given data to the given MongoDB collection. If some data
    already exists then it will get updated (replaced), so reruns of this
    tool against the same event code are safe.

    Args:
        data: A list of dictionaries with data to save

        db_collection: The MongoDB collection to save to.

        db_identifier: An identifier string for identifying which MongoDB is
                      being used.
    """
    logger: logging.Logger = get_logger()

    try:
        if data:
            for doc in tqdm(data, desc=f"Saving to {db_collection.name} ({db_identifier})"):
                db_collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)
    except Exception as e:
        collection_name = db_collection.name
        err_msg: str = f"Error saving to {collection_name} ({db_identifier}): {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
def main() -> None:
    # To see coloring on Windows consoles you need to have this colorama
    # call BEFORE doing ANY output.
    init(autoreset=True, convert=True)

    args = parse_args(sys.argv)

    if args is None:
        sys.exit(0)

    random_data_file = args["random_data_file"]
    event_code = args["event_code"]

    # Make sure the config data we need exists and is NOT empty.  Any
    # failures with the configuration will prevent the code from
    # continuing on.
    validate_configuration()

    records = load_match_scouting_records(random_data_file)

    if records is None:
        sys.exit(1)

    if not records:
        err_msg = f'ERROR: No "mo":"s" records found in {random_data_file}.'
        get_logger().error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        sys.exit(1)

    built = build_matches_and_events(records, event_code)

    if built is None:
        sys.exit(1)

    match_docs = built["matches"]
    events_docs = built["events"]

    status_msg = (
        f"Built {len(match_docs)} match doc(s) and {len(events_docs)} team doc(s) "
        f"for event {event_code}."
    )
    get_logger().info(status_msg)
    print(status_msg)

    # Get the MongoDB database to save the data into.  Abort if we fail on
    # the primary server but NOT on the secondary since it is 100% optional.

    db: Database = get_database(creds.PRIMARY_CONNECTION_STRING, cfg.DB_NAME)

    if db is None:
        err_msg: str = "ERROR: Failed to connect to the primary database. Exiting!"
        get_logger().error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        err_msg = "Did you start the MongoDB server or use the wrong URL?!"
        get_logger().error(err_msg)
        print(f"{Fore.YELLOW}{err_msg}")
        sys.exit(1)

    matchCollection: Collection = db[cfg.V5_COL_MATCH]
    eventsCollection: Collection = db[cfg.V5_COL_EVENTS]

    # A secondary database is optional.  If we have one then get its
    # collections set up too.

    matchCollection2: Optional[Collection] = None
    eventsCollection2: Optional[Collection] = None

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

        matchCollection2 = db2[cfg.V5_COL_MATCH]
        eventsCollection2 = db2[cfg.V5_COL_EVENTS]

    saveDataToMongo(match_docs, matchCollection, "Primary")
    saveDataToMongo(events_docs, eventsCollection, "Primary")

    if matchCollection2 is not None:
        saveDataToMongo(match_docs, matchCollection2, "Secondary")

    if eventsCollection2 is not None:
        saveDataToMongo(events_docs, eventsCollection2, "Secondary")


if __name__ == "__main__":
    main()
