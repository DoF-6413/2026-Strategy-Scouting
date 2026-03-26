# A Python script to get an events schedule from our primary MongoDB.  It's
# primary use is to test how to read a schedule and display it nicely.  The
# eventual goal is to make such logic part of my Slackbot that can retrieve
# data and post to Slack as needed/requested.
#
# This is a 2025 V5 configuration update to get_event_schedule_from_mongodb_v3.py.
# Changes include:
#
# 1: Removed Python 2.x legacy line:
#        from __future__ import print_function
# 2: Updated to the 2025 configuration schema
# 3: Some PEP cleanup
# 4: Updated the logger
# 5: Added autoreset=True to colorama init() so we can reduce the use of
#    {Style.RESET_ALL} in all error output which is typically just 1 line
#    long anyway.
# 6: Reworked some of the script startup logic to be more like current
#    code standards.
# 7: Improved the imports
# 8: Added new V5 and TBA checks/functions
# 9: Upgraded get_database_for_event() to get_database()
# 10: Upgraded get_our_event_schedule() to get_team_event_schedule() to be
#     more generic
# 11: Changed from using cfg.V5_COL_SCHEDULE to cfg.V5_COL_MATCH to avoid
#     needing to rework the dictionary parsing done later in the code.  If
#     you swap to V5_COL_SCHEDULE then you will need to adjust your dictionary
#     parsing from:
#        b1 = match["blue"][0][3:]
#     to:
#        b1 = match["alliances"]["blue"]["team_keys"][0][3:]
#     which matches the original data hierarchy.  You will also need to
#     change the find() inputs to match the schedule data hierarchy.
# 12: Adjusted the schedule formatting to be 5 digits wide instead of 4
#
# NOTE: If the imports below fail, make sure you are using the venv environment
# where the TBA libraries are installed.  They are NOT installed in the base OR
# scrapy environments!!

import logging
import sys
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from colorama import init, Fore
# from ast import expr_context
from pprint import pprint
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
            log_file = f"UtilLog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

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
        A Database if we connected successfully, None if we failed for any reason!
    '''
    from pymongo import MongoClient

    logger: logging.Logger = get_logger()

    # Create a connection to the specified MongoDB server

    try:
        client: MongoClient = MongoClient( databaseURI )

        # Use/Create the database to hold our data
        return client[ databaseName ]
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
def get_event_schedule(db: Database, eventCode: str, compLevel: str) -> Cursor[Dict[str, Any]]:
    '''
    Get the full event schedule from the MongoDB.

    Parameters:
        db (Database): The MongodB database to read the schedule data from

        eventCode (str): The event code to get the scheduled matches for

        compLevel (str): The competition level we want the schedule for
                         (cfg.MATCHLEVEL_...)

    Returns:
        (Cursor): A MongodB Cursor for scheduled matches for the specified
                  event and competition level
    '''
    matchCollection: Collection = db[cfg.V5_COL_MATCH]

    # Determine the sorting key based on compLevel
    sort_key: str = "set_number" if compLevel == cfg.MATCHLEVEL_SEMIS else "match_number"

    matches: Cursor[Dict[str, Any]] = matchCollection.find({"event_key": eventCode, "comp_level": compLevel}).sort(sort_key)

    return matches


###############################################################################
###############################################################################
def get_team_event_schedule(db: Database, eventCode: str, compLevel: str, teamKey: str) -> Cursor[Dict[str, Any]]:
    '''
    Get the event schedule for the event for just our team from the MongoDB.

    Parameters:
        db (Database): The MongodB database to read the schedule data from

        eventCode (str): The event code to get the scheduled matches for

        compLevel (str): The competition level we want the scheduled for
                         (cfg.MATCHLEVEL_...)

        teamKey (str): The TBA team key (e.g. frc6413) to get the schedule for

    Returns:
        (Cursor): A MongodB Cursor for a team scheduled matches for the
                  specified event and competition level
    '''
    matchCollection: Collection = db[cfg.V5_COL_MATCH]

    # Determine the sorting key based on compLevel
    sort_key: str = "set_number" if compLevel == cfg.MATCHLEVEL_SEMIS else "match_number"

    matches = matchCollection.find({"event_key": eventCode, "comp_level": compLevel, "$or": [{"alliances.blue.team_keys": teamKey}, {"alliances.red.team_keys": teamKey}]}).sort(sort_key)

    return matches


###############################################################################
###############################################################################
def show_the_full_schedule(db: Database, eventCode: str) -> None:
    '''
    Get and show the event schedule for the entire event from the MongoDB.

    Parameters:
        db (Database): The MongodB database to read the schedule data from

        eventCode (str): The event code to get the scheduled matches for
    '''
    logger: logging.Logger = get_logger()

    # Get all possible schedules from the database first.

    qual_matches = get_event_schedule(db, eventCode, cfg.MATCHLEVEL_QUALIFIERS)
    # As of 2024, we no longer have Quarter Finals but they do exist
    # for years prior to 2024 so check for them in all cases to be safe
    quarter_matches = get_event_schedule(db, eventCode, cfg.MATCHLEVEL_QUARTERS)
    semi_matches = get_event_schedule(db, eventCode, cfg.MATCHLEVEL_SEMIS)
    final_matches = get_event_schedule(db, eventCode, cfg.MATCHLEVEL_FINALS)

    # If we have no qualifier matches then we can do nothing further here
    try:
        next(qual_matches)
        # If next() succeeds, there is at least one document
        qual_matches = qual_matches.rewind()
    except StopIteration:
        status_msg: str = f"No match data is available for {eventCode}"
        logger.info(status_msg)
        print(f"{Fore.RED}{status_msg}")
        return

    # If we got here, we have at least the Qualifier schedule to show

    print(f"The following is the current schedule for {eventCode}")
    print("Qualification matches:")
    print("### -    B1     B2     B3      R1     R2     R3")
    for match in qual_matches:
        b1 = match["alliances"]["blue"]["team_keys"][0][3:]
        b2 = match["alliances"]["blue"]["team_keys"][1][3:]
        b3 = match["alliances"]["blue"]["team_keys"][2][3:]
        blue_teams = f'{Fore.BLUE}{b1:>6} {b2:>6} {b3:>6}'
        r1 = match["alliances"]["red"]["team_keys"][0][3:]
        r2 = match["alliances"]["red"]["team_keys"][1][3:]
        r3 = match["alliances"]["red"]["team_keys"][2][3:]
        red_teams = f'{Fore.RED}{r1:>6} {r2:>6} {r3:>6}'
        print(f"{match['match_number']:>3} -  {blue_teams}  {red_teams}")
    print()

    # Only print out the Quarter Finals header and data if we have some
    try:
        next(quarter_matches)
        quarter_matches = quarter_matches.rewind()
        print("Quarter final matches:")
        print("#.# -    B1     B2     B3      R1     R2     R3")
        for match in quarter_matches:
            b1 = match["alliances"]["blue"]["team_keys"][0][3:]
            b2 = match["alliances"]["blue"]["team_keys"][1][3:]
            b3 = match["alliances"]["blue"]["team_keys"][2][3:]
            blue_teams = f'{Fore.BLUE}{b1:>6} {b2:>6} {b3:>6}'
            r1 = match["alliances"]["red"]["team_keys"][0][3:]
            r2 = match["alliances"]["red"]["team_keys"][1][3:]
            r3 = match["alliances"]["red"]["team_keys"][2][3:]
            red_teams = f'{Fore.RED}{r1:>6} {r2:>6} {r3:>6}'
            print(f"{match['set_number']}.{match['match_number']} -  {blue_teams}  {red_teams}")
        print()
    except StopIteration:
        pass  # do nothing because there are no quarter matches.

    # Only print out the Semi Finals header and data if we have some
    try:
        next(semi_matches)
        semi_matches = semi_matches.rewind()
        print("Semi final matches:")
        print("#.# -    B1     B2     B3      R1     R2     R3")
        for match in semi_matches:
            b1 = match["alliances"]["blue"]["team_keys"][0][3:]
            b2 = match["alliances"]["blue"]["team_keys"][1][3:]
            b3 = match["alliances"]["blue"]["team_keys"][2][3:]
            blue_teams = f'{Fore.BLUE}{b1:>6} {b2:>6} {b3:>6}'
            r1 = match["alliances"]["red"]["team_keys"][0][3:]
            r2 = match["alliances"]["red"]["team_keys"][1][3:]
            r3 = match["alliances"]["red"]["team_keys"][2][3:]
            red_teams = f'{Fore.RED}{r1:>6} {r2:>6} {r3:>6}'
            print(f"{match['set_number']}.{match['match_number']} -  {blue_teams}  {red_teams}")
        print()
    except StopIteration:
        pass  # do nothing because there are no semi final matches.

    # Only print out the Finals header and data if we have some
    try:
        next(final_matches)
        final_matches = final_matches.rewind()
        print("Final matches:")
        print("#.# -    B1     B2     B3      R1     R2     R3")
        for match in final_matches:
            b1 = match["alliances"]["blue"]["team_keys"][0][3:]
            b2 = match["alliances"]["blue"]["team_keys"][1][3:]
            b3 = match["alliances"]["blue"]["team_keys"][2][3:]
            blue_teams = f'{Fore.BLUE}{b1:>6} {b2:>6} {b3:>6}'
            r1 = match["alliances"]["red"]["team_keys"][0][3:]
            r2 = match["alliances"]["red"]["team_keys"][1][3:]
            r3 = match["alliances"]["red"]["team_keys"][2][3:]
            red_teams = f'{Fore.RED}{r1:>6} {r2:>6} {r3:>6}'
            print(f"{match['set_number']}.{match['match_number']} -  {blue_teams}  {red_teams}")
        print()
    except StopIteration:
        pass  # do nothing because there are no final matches.


###########################################################################################
###########################################################################################
def show_team_schedule(db: Database, eventCode: str, teamKey: str) -> None:
    '''
    Get and show the event schedule for the entire event from the MongoDB.

    Parameters:
        db (Database): The MongodB database to read the schedule data from

        eventCode (str): The event code to get the scheduled matches at

        teamKey (str): The TBA team code to get the schedule for
    '''
    logger: logging.Logger = get_logger()

    # Get all possible schedules from the database first.

    qual_matches = get_team_event_schedule(db, eventCode, cfg.MATCHLEVEL_QUALIFIERS, teamKey)
    quarter_matches = get_team_event_schedule(db, eventCode, cfg.MATCHLEVEL_QUARTERS, teamKey)
    semi_matches = get_team_event_schedule(db, eventCode, cfg.MATCHLEVEL_SEMIS, teamKey)
    final_matches = get_team_event_schedule(db, eventCode, cfg.MATCHLEVEL_FINALS, teamKey)

    # If we have no qualifier matches then we can do nothing further here
    try:
        next(qual_matches)
        # If next() succeeds, there is at least one document
        qual_matches = qual_matches.rewind()
    except StopIteration:
        status_msg: str = f"No match data is available for team {teamKey[3:]} at {eventCode}"
        logger.info(status_msg)
        print(f"{Fore.RED}{status_msg}")
        return

    # If we got here, we have at least one set of schedules to show (the qualifiers)

    print(f"The following is the match schedule for team {teamKey[3:]} at {eventCode}")
    print("Qualification matches:")
    print("### -    B1     B2     B3      R1     R2     R3")
    for match in qual_matches:
        b1 = match["alliances"]["blue"]["team_keys"][0][3:]
        b2 = match["alliances"]["blue"]["team_keys"][1][3:]
        b3 = match["alliances"]["blue"]["team_keys"][2][3:]
        blue_teams = f'{Fore.BLUE}{b1:>6} {b2:>6} {b3:>6}'
        r1 = match["alliances"]["red"]["team_keys"][0][3:]
        r2 = match["alliances"]["red"]["team_keys"][1][3:]
        r3 = match["alliances"]["red"]["team_keys"][2][3:]
        red_teams = f'{Fore.RED}{r1:>6} {r2:>6} {r3:>6}'
        print(f"{match['match_number']:>3} -  {blue_teams}  {red_teams}")
    print()

    # Only print out the Quarter Finals header and data if we have some
    try:
        next(quarter_matches)
        quarter_matches = quarter_matches.rewind()
        print("Quarter final matches:")
        print("#.# -    B1     B2     B3      R1     R2     R3")
        for match in quarter_matches:
            b1 = match["alliances"]["blue"]["team_keys"][0][3:]
            b2 = match["alliances"]["blue"]["team_keys"][1][3:]
            b3 = match["alliances"]["blue"]["team_keys"][2][3:]
            blue_teams = f'{Fore.BLUE}{b1:>6} {b2:>6} {b3:>6}'
            r1 = match["alliances"]["red"]["team_keys"][0][3:]
            r2 = match["alliances"]["red"]["team_keys"][1][3:]
            r3 = match["alliances"]["red"]["team_keys"][2][3:]
            red_teams = f'{Fore.RED}{r1:>6} {r2:>6} {r3:>6}'
            print(f"{match['set_number']}.{match['match_number']} -  {blue_teams}  {red_teams}")
        print()
    except StopIteration:
        pass  # do nothing because there are no quarter matches.

    # Only print out the Semi Finals header and data if we have some
    try:
        next(semi_matches)
        semi_matches = semi_matches.rewind()
        print("Semi final matches:")
        print("#.# -    B1     B2     B3      R1     R2     R3")
        for match in semi_matches:
            b1 = match["alliances"]["blue"]["team_keys"][0][3:]
            b2 = match["alliances"]["blue"]["team_keys"][1][3:]
            b3 = match["alliances"]["blue"]["team_keys"][2][3:]
            blue_teams = f'{Fore.BLUE}{b1:>6} {b2:>6} {b3:>6}'
            r1 = match["alliances"]["red"]["team_keys"][0][3:]
            r2 = match["alliances"]["red"]["team_keys"][1][3:]
            r3 = match["alliances"]["red"]["team_keys"][2][3:]
            red_teams = f'{Fore.RED}{r1:>6} {r2:>6} {r3:>6}'
            print(f"{match['set_number']}.{match['match_number']} -  {blue_teams}  {red_teams}")
        print()
    except StopIteration:
        pass  # do nothing because there are no semi final matches.

    # Only print out the Finals header and data if we have some
    try:
        next(final_matches)
        final_matches = final_matches.rewind()
        print("Final matches:")
        print("#.# -    B1     B2     B3      R1     R2     R3")
        for match in final_matches:
            b1 = match["alliances"]["blue"]["team_keys"][0][3:]
            b2 = match["alliances"]["blue"]["team_keys"][1][3:]
            b3 = match["alliances"]["blue"]["team_keys"][2][3:]
            blue_teams = f'{Fore.BLUE}{b1:>6} {b2:>6} {b3:>6}'
            r1 = match["alliances"]["red"]["team_keys"][0][3:]
            r2 = match["alliances"]["red"]["team_keys"][1][3:]
            r3 = match["alliances"]["red"]["team_keys"][2][3:]
            red_teams = f'{Fore.RED}{r1:>6} {r2:>6} {r3:>6}'
            print(f"{match['set_number']}.{match['match_number']} -  {blue_teams}  {red_teams}")
        print()
    except StopIteration:
        pass  # do nothing because there are no final matches.


###############################################################################
###############################################################################
def main() -> None:
    import credentials as creds

    logger: logging.Logger = get_logger()

    # Make sure the config data we need exists and is NOT empty.  Any failures
    # with the configuration will prevent the code from continuing on.
    validate_configuration()

    # To see coloring on Win10 consoles I found I needed to have this
    # colorama call before doing any output.  We use autoreset=True so
    # we do not need to include Style.RESET_ALL all over.
    init(autoreset=True, convert=True)

    eventCode: str = input("Enter the event code (or 'quit' to exit): ").strip()

    if eventCode.lower() == "quit":
        logger.info("The session was aborted at the event code prompt")
        sys.exit(0)

    logger.info(f"The event code for this session is {eventCode}")

    # TODO: Add an event code check here to make sure the code is legit

    teamKey: str = input("Enter the TBA team code you want the schedule for ('all'=all teams, 'quit' to exit): ").strip()

    if eventCode.lower() == "quit":
        logger.info("The session was aborted at the team code prompt")
        sys.exit(0)

    logger.info(f"The team code for this session is {teamKey}")

    # Get the MongoDB database to read the data from.  Abort if we fail
    # on the primary server.  We wont try to also read from the secondary
    # since it is 100% optional and not needed in this version of the script.

    db: Database = get_database(creds.PRIMARY_CONNECTION_STRING, cfg.DB_NAME)

    if db is None:
        err_msg: str = "Failed to connect to the primary database.  Exiting!"
        logger.error(err_msg)
        print(f"{Fore.RED}{err_msg}")
        sys.exit(1)

    if teamKey.lower() == "all":
        # Show the entire event schedule
        show_the_full_schedule(db, eventCode)
        print()
    else:
        # Show a specific teams schedule
        show_team_schedule(db, eventCode, teamKey)


###############################################################################
###############################################################################
#                    Main starting point for the script
###############################################################################
###############################################################################
if __name__ == "__main__":
    main()
