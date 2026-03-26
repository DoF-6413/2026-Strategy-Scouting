# A Python script to get the current years list ov event codes and print them to
# the console as a list of strings.
#
# This is an updated version of get_events_by_year_keys_2022.py.  Changes include:
#
# 1: Updated to use the 2025 configuration and credentials files
# 2: Removed Python 2.x legacy line:
#        from __future__ import print_function
# 3: PEP nag/warning cleanup
# 4: Made the script always use the current year
# 5: Removed the unused if-modified-since variable

#
# Example output:
# (venv) D:\Workspace\TBA-python>python get_events_by_year_keys_2025_v1.py
# ['2022alhu',
#  '2022arli',
#  '2022ausc',
#  '2022azfl',
#  ...
#   '2022xxmac',
#  '2022xxmel',
#  '2022zhha']

# NOTE: If the imports below fail, make sure you are using the venv environment
# where the TBA libraries are installed.  They are NOT installed in the base OR
# scrapy environments!!

import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Union, Tuple, Optional
import time
import tbaapiv3client
from tbaapiv3client.api import TBAApi, EventApi
from tbaapiv3client.api_client import ApiClient
from tbaapiv3client.configuration import Configuration
from tbaapiv3client.rest import ApiException
from colorama import init, Fore, Style
from urllib3.exceptions import MaxRetryError
from pprint import pprint
import config as cfg

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
            log_file = f"ToolLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
def is_TBA_down(api_client: ApiClient) -> Tuple[bool, int, int]:
    """
    Check if the TBA API is down.  It also returns the current_season and
        max_season values from the TBA API

    Args:
        api_client (ApiClient): An instance of the TBA API client.

    Returns:
        Tuple[bool, int, int]: A tuple containing:
            - A boolean indicating the TBA API is down.
            - The current_season value
            - The max_season value
    """
    logger: logging.Logger = get_logger()

    try:
        # Create an instance of the API class
        api_instance = TBAApi(api_client)

        # Perform the API status check
        api_response = api_instance.get_status()

        # Extract data from API response
        is_down = api_response.is_datafeed_down
        current_season = api_response.current_season
        max_season = api_response.max_season

        # Return the API status info
        return is_down, current_season, max_season
    except ApiException as e:
        err_msg: str = f"ERROR: Exception when calling TBAApi.get_status: {e}\n"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}\n")
        return True, None, None  # Treat any exception as API being down
    except MaxRetryError:
        # This can happen if there is no network connectivity such as no WiFi
        # or TBA is actually down!
        err_msg: str = "Unable to reach TBA.  Please check your network connection and try again!"
        logger.error(err_msg)
        print(f"\n{Fore.RED}{err_msg}\n")
        return True, None, None  # Treat any exception as API being down


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

    First do credential checks and then do schema specific checks.  We only check
    the current schema and not all possible schemas.
    '''
    import credentials as creds

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
def main() -> None:
    import credentials as creds

    logger: logging.Logger = get_logger()

    # Make sure the config data we need exists and is NOT empty.  Any failures
    # with the configuration will prevent the code from continuing on.
    validate_configuration()

    # Configure API key authorization: apiKey
    configuration = Configuration(api_key={'X-TBA-Auth-Key': creds.TBA_AUTH_KEY})

    # To see coloring on Win10 consoles I found I needed to have this
    # colorama call before doing any output.  We use autoreset=True so
    # we do not need to include Style.RESET_ALL all over.
    init(autoreset=True, convert=True)

    # Enter a context with an instance of the API client
    with ApiClient(configuration) as api_client:
        # Note the use of [0] below to force unpacking the first value
        # of the returned tuple.  Otherwise you will ALWAYS see a
        # 'truthy' value resulting in bogus behavior!
        if is_TBA_down(api_client)[0]:
            print(f"The TBA API is {Fore.RED}DOWN{Style.RESET_ALL}.")
            sys.exit(0)

        api_instance = EventApi(api_client)
        year: int = datetime.now().year

        try:
            api_response = api_instance.get_events_by_year_keys(year)
            pprint(api_response)
        except ApiException as e:
            err_msg: str = f"ERROR: Exception when calling EventApi.get_events_by_year_keys: {e}"
            logger.error(err_msg)
            print(f"{Fore.RED}{err_msg}")
            return None


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":
    main()
