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

from colorama import Fore, Style, init
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
def main() -> None:
    logger: logging.Logger = get_logger()
    init(autoreset=True, convert=True)
    validate_configuration()

    parser = argparse.ArgumentParser(
        description="Show pre-scouting breakdown for a match from MongoDB."
    )
    parser.add_argument("-e", "--event", help="TBA event code (e.g. 2026nvlv)")
    parser.add_argument("-t", "--team", help="Full TBA team key (e.g. frc6413)")
    parser.add_argument(
        "-m", "--match", help="Match number in TBA format (e.g. qm5, sf2m1, f1m2)"
    )
    args = parser.parse_args()

    event_code: str = args.event.strip() if args.event else ""
    if not event_code:
        event_code = input("Enter the event code (or 'quit' to exit): ").strip()
        if event_code.lower() == "quit":
            logger.info("Session aborted at event code prompt")
            sys.exit(0)

    team_key: str = args.team.strip() if args.team else ""
    if not team_key:
        team_key = input(
            "Enter the full TBA team key (e.g. frc6413) (or 'quit' to exit): "
        ).strip()
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

    logger.info(f"event={event_code} team={team_key} match={match_key}")


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":
    main()
