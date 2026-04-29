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


def setup_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = logging.getLogger(__name__)
        _logger.setLevel(logging.WARNING)
        if not _logger.handlers:
            log_file = f"ToolLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            script_dir = os.path.dirname(os.path.abspath(__file__))
            log_file_path = os.path.join(script_dir, log_file)
            handler = logging.FileHandler(log_file_path)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
    return _logger


def get_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


def check_config_params(cfg: object, params: List[str]) -> bool:
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


def is_V5_configuration_bad() -> bool:
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


def validate_configuration() -> None:
    badConfig: bool = False
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


def get_database(database_uri: str, database_name: str) -> Optional[Database]:
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


if __name__ == "__main__":
    pass
