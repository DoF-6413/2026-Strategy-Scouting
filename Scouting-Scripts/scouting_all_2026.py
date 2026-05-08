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
#                  Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":
    pass
