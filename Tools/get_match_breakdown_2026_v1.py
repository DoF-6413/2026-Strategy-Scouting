# A Python script that retrieves alliance and opponent pre-scouting notes
# from MongoDB for a specific match, giving the strategy team a quick
# breakdown before a match.
#
# Usage:
#   uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v1.py
#   uv run --package frc-6413-scouting-tools python Tools/get_match_breakdown_2026_v1.py \
#       -e 2026nvlv -t frc6413 -m qm5

import argparse
import logging
import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from colorama import Fore, init
from frc_6413_common import config as cfg
from frc_6413_common import credentials as creds
from pymongo.collection import Collection
from pymongo.database import Database

_logger: Optional[logging.Logger] = None


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

    First do credential checks and then do schema specific checks.  We only check
    the current schema and not all possible schemas.
    """
    badConfig: bool = False
    badV5Config: bool = False
    logger: logging.Logger = get_logger()
    if not (hasattr(creds, "PRIMARY_CONNECTION_STRING") and creds.PRIMARY_CONNECTION_STRING):
        err_msg: str = "ERROR: PRIMARY_CONNECTION_STRING is missing or empty!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        badConfig = True
    if not hasattr(creds, "SECONDARY_CONNECTION_STRING"):
        err_msg: str = "ERROR: SECONDARY_CONNECTION_STRING is missing!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        badConfig = True
    badV5Config = is_V5_configuration_bad()
    if badConfig or badV5Config:
        sys.exit(2)


###############################################################################
###############################################################################
def get_database(database_uri: str, database_name: str) -> Optional["Database"]:
    """
    Returns a MongoDB database to read/write the all your data from/into OR
        None if there was a problem accessing the database.

    Parameters:
        database_uri (str): The database connection URL to use

        database_name (str): The name of the database to access

    Returns:
        A Database if we connected successfully, None if we failed for any reason!
    """
    from pymongo import MongoClient

    logger: logging.Logger = get_logger()
    try:
        client: MongoClient = MongoClient(database_uri)
        return client[database_name]
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
def parse_match_key(match_key: str) -> Tuple[str, int, int]:
    """
    Parse a TBA match key into (comp_level, set_number, match_number).

    Supported formats:
        qm5    -> ('qm', 1, 5)
        sf2m1  -> ('sf', 2, 1)
        f1m2   -> ('f', 1, 2)
        qf1m1  -> ('qf', 1, 1)

    Raises ValueError on unrecognized format.
    """
    key = match_key.lower().strip()

    m = re.match(r"^(qm)(\d+)$", key)
    if m:
        return "qm", 1, int(m.group(2))

    m = re.match(r"^(sf|qf|f)(\d+)m(\d+)$", key)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3))

    raise ValueError(
        f"Unrecognized match key format: '{match_key}'. Expected formats: qm5, sf2m1, f1m2, qf1m1"
    )


###############################################################################
###############################################################################
def get_match(
    db: Database,
    event_code: str,
    comp_level: str,
    set_number: int,
    match_number: int,
) -> Optional[Dict]:
    """
    Retrieve a specific match document from the matches collection.
    Returns the document dict or None if not found.
    """
    logger: logging.Logger = get_logger()
    match_collection: Collection = db[cfg.V5_COL_MATCH]
    try:
        return match_collection.find_one(
            {
                "event_key": event_code,
                "comp_level": comp_level,
                "set_number": set_number,
                "match_number": match_number,
            }
        )
    except Exception as e:
        err_msg: str = f"ERROR: Failed to query matches collection: {e}"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        return None


###############################################################################
###############################################################################
def main() -> None:
    """
    Parse CLI args (or prompt interactively) for event code, team key, and
    match number, then display pre-scouting breakdown from MongoDB.
    """
    logger: logging.Logger = get_logger()
    init(autoreset=True, convert=True)
    validate_configuration()

    parser = argparse.ArgumentParser(
        description="Show pre-scouting breakdown for a match from MongoDB."
    )
    parser.add_argument("-e", "--event", help="TBA event code (e.g. 2026nvlv)")
    parser.add_argument("-t", "--team", help="Full TBA team key (e.g. frc6413)")
    parser.add_argument("-m", "--match", help="Match number in TBA format (e.g. qm5, sf2m1, f1m2)")
    args = parser.parse_args()

    event_code: str = args.event.strip() if args.event else ""
    if not event_code:
        event_code = input("Enter the event code (or 'quit' to exit): ").strip()
        if event_code.lower() == "quit":
            logger.info("Session aborted at event code prompt")
            sys.exit(0)

    team_key: str = args.team.strip() if args.team else ""
    if not team_key:
        team_key = input("Enter the full TBA team key (e.g. frc6413) (or 'quit' to exit): ").strip()
        if team_key.lower() == "quit":
            logger.info("Session aborted at team key prompt")
            sys.exit(0)

    match_key: str = args.match.strip() if args.match else ""
    if not match_key:
        match_key = input(
            "Enter the match number in TBA format (e.g. qm5, sf2m1) (or 'quit' to exit): "
        ).strip()
        if match_key.lower() == "quit":
            logger.info("Session aborted at match key prompt")
            sys.exit(0)

    # Validate team key format
    if not team_key.lower().startswith("frc"):
        print(f"{Fore.RED}ERROR: Team key must be in TBA format (e.g frc6413). Got: '{team_key}'")
        sys.exit(1)

    logger.info(f"event={event_code} team={team_key} match={match_key}")

    # Parse the match key into query components
    try:
        comp_level, set_number, match_number = parse_match_key(match_key)
    except ValueError as e:
        print(f"{Fore.RED}ERROR: {e}")
        sys.exit(1)

    # Connect to primary MongoDB
    db: Database = get_database(creds.PRIMARY_CONNECTION_STRING, cfg.DB_NAME)
    if db is None:
        err_msg: str = "Failed to connect to the primary database. Exiting!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        sys.exit(1)

    # Look up the match document
    match_doc = get_match(db, event_code, comp_level, set_number, match_number)
    if match_doc is None:
        err_msg: str = (
            f"Match '{match_key}' not found for event '{event_code}' in MongoDB. "
            "Make sure match data has been downloaded with get_event_matches_2026_v2.py."
        )
        logger.error(err_msg)
        print(f"{Fore.RED}ERROR: {err_msg}")
        sys.exit(1)

    # Determine which alliance the team is on
    try:
        blue_teams: List[str] = match_doc["alliances"]["blue"]["team_keys"]
        red_teams: List[str] = match_doc["alliances"]["red"]["team_keys"]
    except KeyError:
        err_msg: str = (
            f"Match '{match_key}' for event '{event_code}' has unexpected data "
            "structure (missing alliance team keys)."
        )
        logger.error(err_msg)
        print(f"{Fore.RED}ERROR: {err_msg}")
        sys.exit(1)

    if team_key in blue_teams:
        alliance_teams = blue_teams
        opponent_teams = red_teams
    elif team_key in red_teams:
        alliance_teams = red_teams
        opponent_teams = blue_teams
    else:
        err_msg: str = (
            f"Team '{team_key}' is not listed in match '{match_key}' for event '{event_code}'."
        )
        logger.error(err_msg)
        print(f"{Fore.RED}ERROR: {err_msg}")
        sys.exit(1)

    partners: List[str] = [t for t in alliance_teams if t != team_key]


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":
    main()
