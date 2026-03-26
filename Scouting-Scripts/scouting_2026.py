# This Python script will take scouting data from scanned QR codes (as JSON)
# and then do any touch up and data checking before putting it into a MongoDB
# database or two.
#
# This is the updated version of the 2026 scouting script.  It started as the
# last 2025 version and then got a schema update for 2026.
#
# PLANNED updates to come eventually are:
#
# 1: Add TBA support so that we can sanity check the data.  For example,
#    make sure that Team 842 is actually playing in match 4 at the event by
#    checking the match info from TBA.
# 2: Add a GUI show what teams we have data for in the current match!  The
#    GUI should include a way to indicate if a QR code was good or not (e.g.
#    it flashes green if good or red if bad - yellow if thinking or waiting)
# 3: Add match level safety checks across alliances.  For instance, there is
#    no way for an alliance to score 15 Coral on L4 so make sure the scouts
#    did not get confused and give them all credit.

import json
import logging
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional, Union

import config as cfg
import credentials as creds
from pymongo.collection import Collection
from pymongo.database import Database

# Create and configure a logger for our script to use:
logging.basicConfig( level=logging.INFO )
DoFLogger = logging.getLogger( __name__ )


###############################################################################
###############################################################################
def check_config_params( cfg: object, params: List[str] ) -> bool:
    """
    Check if multiple configuration parameters exist and are non-empty strings in
    the given cfg object.

    Parameters:
        cfg: The configuration module (e.g., the imported 'config' module).

        params: A list of parameter names to check for (strings).

    Returns:
        True if any parameter is missing or empty, False otherwise.
    """
    badConfig = False

    for param_name in params:
        param_value = getattr( cfg, param_name, None )

        if not param_value:  # Check for None or empty string
            DoFLogger.error( f"ERROR: {param_name} is missing or empty!" )
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
        "ALL_TEAMS_DETAILED"
    ]

    badV5Config = check_config_params( cfg, v5_values_to_check )

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

    badConfig = False
    badV5Config = False

    # The PRIMARY_CONNECTION_STRING MUST exist and be non-NULL!

    if not ( hasattr( creds, "PRIMARY_CONNECTION_STRING" ) and creds.PRIMARY_CONNECTION_STRING ):
        DoFLogger.error( "ERROR: PRIMARY_CONNECTION_STRING is missing or empty!" )
        badConfig = True

    # The SECONDARY_CONNECTION_STRING MUST exist but CAN be empty.

    if not ( hasattr( creds, "SECONDARY_CONNECTION_STRING" ) ):
        DoFLogger.error( "ERROR: SECONDARY_CONNECTION_STRING is missing!" )
        badConfig = True

    # Make sure all V5 schema values exist.

    badV5Config = is_V5_configuration_bad()

    # Getting here with any bad configurations is grounds to exit

    if badConfig or badV5Config:
        sys.exit(2)


###############################################################################
###############################################################################
def get_database( databaseURI: str, databaseName: str ) -> Optional["Database"]:
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

    # Create a connection to the specified MongoDB server

    try:
        client: MongoClient = MongoClient( databaseURI )

        # Use/Create the database to hold our data
        return client[ databaseName ]
    except ConnectionError as e:
        DoFLogger.error( "Failed to connect to MongoDB server: %s", e )
    except Exception as e:
        DoFLogger.error( "Failed to access the database: %s", e )

    return None


###############################################################################
###############################################################################
def inflate_tablet_data( tabletData: str )  -> Optional[Dict[str, Union[str, int]]]:
    '''
    Parse and "inflate" the given tablet JSON data into a dictionary that we then process
    further before returning to our caller.

    Parameters:
        tabletData (str): The match scouting data from a tablet (a JSON dictionary string)

    Returns:
        A dictionary with the tablet data in it OR nothing if it was not JSON data.
    '''

    # Make sure we can parse the data into JSON data before we try to do anything else

    try:
        matchData = json.loads( tabletData )

    except json.JSONDecodeError:
            print( "ERROR: NOT a valid JSON string!  Try again." )
            return

    # We got JSON so lets do any touch up we need to.
    # "Reinflate" the key names before we save the data into the database.

    key_mapping = {
        "cl": "compLevel",
        "mn": "matchNumber",
        "i": "scouter",
        "a1": "autoHub",
        "a2": "autoHubMiss",
        "t1": "teleHub",
        "t2": "teleHubMiss",
        "ns": "noShow",
        "d": "died",
        "r": "relayed",
        "h": "herded",
        "co": "comments"
    }

    # Inflate all the keys we expect.  If one is missing, DO NOT continue or
    # return any data to avoid corrupting the database.  Leave it to an admin
    # to look into this error report and resolve the issue based on the saved
    # raw data.
    for short_key, long_key in key_mapping.items():
        if short_key in matchData:  # Check if the short key exists
            matchData[ long_key ] = matchData.pop( short_key )
        else:
            DoFLogger.error( f"QR code key {short_key} was NOT found!" )
            return

    # Lets tidy up the comments value so it renders nicely wherever we show it:
    #
    # 1: Remove all embedded newlines
    # 2: Get rid of extra whitespace inside the comments.
    # 3: Trim off any leading or trailing whitespace
    matchData[ "comments" ] = re.sub(r'\s+', ' ', matchData[ "comments" ].replace("\n", " ") ).strip()

    # Add the correct docType to the data
    matchData[ "docType" ] = cfg.DT_SCOUTING_MATCH

    # For Streamlits benefit we remove the TBA prefix.
    matchData[ "team" ] = str( matchData[ 'key' ] )

    # For 2026 we only have 1 game piece and 1 way to score it but its not easily
    # tracked for misses so we have nothing really to do except "guestimate" their
    # overall scoring for the Dashboard.
    # Look to the 2025 script for an example of how to calculate stats before we
    # store the data.
    matchData[ "totalGamePieces" ] = matchData[ "autoHub" ] + matchData[ "teleHub" ]

    # Set the _id value of the entry to be a combination of the event code,
    # match type & number plus the team number.  TBA encodes matches as follows:
    #
    # eventCode + "_" + comp_level + [set_number + "m" + ] match_number
    #
    # Intially we are going to assume Qualifiers (qm) only until the web page
    # gets updated to scout elimiations (and to send that data back to here).
    #
    # The hard part will be to identify the "set" numbers to return...
    # Given FIRST has shifted to using a fixed double elimination bracket
    # instead of the "best of 3 per round" we may be able to map "matchNum"
    # to a set value.  Alternately TBA may adjust its encoding since there
    # is no longer a need for a set.  Or perhaps we simply tack it to the end
    # of the compLevel value on the web page side...

    id_to_use = eventCode + "_" + matchData[ 'compLevel' ] + str( matchData[ 'matchNumber' ] ) + "_frc" + matchData[ "team" ]

    matchData[ '_id' ] = id_to_use

    return matchData


###############################################################################
###############################################################################
#                  Main starting point for the script
###############################################################################
###############################################################################
def main() -> None:
    global eventCode

    # Make sure the config data we need exists and is NOT empty.  Any failures
    # with the configuration will prevent the code from continuing on.
    validate_configuration()

    # Construct the replay log file for the tablet data for this run
    replayFile = f"ScoutingData_{datetime.now().strftime('%Y%m%d_%H%M%S')}.data"
    DoFLogger.info( f"The data log for this session is {replayFile}" )

    while True:
        eventCode: str = input( "Enter the event code for the event you are scouting (or 'quit' to exit): " ).strip()

        if eventCode.lower() == "quit":
            DoFLogger.info( "The session was aborted at the event code prompt" )
            sys.exit(0)

        # Make sure we get an event code that begins with a '2'
        if eventCode.startswith('2'):
            break

        print("\n\nHEY!  That is not a valid event code!  Try again...\n")


    DoFLogger.info( f"The event code for this session is {eventCode}" )

    # Get the MongoDB database to save the data into.  Abort if we fail
    # on the primary server but NOT on the secondary since it is 100%
    # optional.

    db: Database = get_database( creds.PRIMARY_CONNECTION_STRING, cfg.DB_NAME )

    if db is None:
        DoFLogger.error( "Failed to connect to the database.  Exiting!" )
        print( "Failed to connect to the database. Exiting..." )
        sys.exit(1)

    # ALL scouting data goes into the scouting collection.

    scoutingCollection: Collection = db[ cfg.V5_COL_SCOUTING ]

    # A secondary database and collection are optional.  If we have them then
    # get the MongoDB database and collection set up as well.

    scoutingCollection2: Collection = None

    if creds.SECONDARY_CONNECTION_STRING:
        db2: Database = get_database( creds.SECONDARY_CONNECTION_STRING, cfg.DB_NAME )

        if db2 is None:
            DoFLogger.error( "Failed to connect to the secondary database.  Exiting!" )
            print( "Failed to connect to the secondary database. Exiting..." )
            sys.exit(1)

        # ALL scouting data goes into the scouting collection.

        scoutingCollection2: Collection = db2[ cfg.V5_COL_SCOUTING ]

    while True:
        tabletData: str = input( "Scan a tablet now (or 'quit' to exit): " ).strip()

        DoFLogger.debug( f"The tablet data: {tabletData}" )

        if tabletData.lower() == "quit":
            break

        matchData = inflate_tablet_data( tabletData )

        # Only do additional work if we got back a dictionary.  Any other
        # return values should be ignored and we just try again!

        if isinstance( matchData, dict ):
            # Add the TBA eventCode to the dictionary we have before we go on.

            matchData[ "eventCode" ] = eventCode

            # The tablet data was ok so lets save a copy to our replay file
            # before we do anything else.

            with open( replayFile, "a", encoding="utf-8" ) as file:
                file.write( tabletData + "\n" )

            # Time to save the re-inflated data to a MongoDB (or two)

            matchID = matchData[ "_id" ]

            scoutingCollection.update_one({'_id':matchID}, {"$set": matchData}, upsert=True)

            if scoutingCollection2 is not None:
                scoutingCollection2.update_one({'_id':matchID}, {"$set": matchData}, upsert=True)


if __name__ == "__main__":
    main()
