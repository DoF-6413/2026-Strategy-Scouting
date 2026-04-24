# This is a "configuration" file and NOT any actual Python script.
#
# It holds an ever changing and expanding set of constant values used
# by our various Python scripts to store and retrieve FRC related data.
# The values in this file are SHAREABLE and NON-PRIVATE.  ANYTHING that was
# in this file that can be considered private (e.g. passwords or URLs with
# sensitive data in them), can be found in the credentials.py file instead!
#
# Note: With the shift to using a separate credentials (credentials.py) and
# data configuration/schema (this file), all pre-2024 scripts will need some
# love to update them to the V3 schema with 2 files instead of 1 (and to use
# the new V5 values.
#
# Our data organization has changed over time with 2025 resulting in a V5 data
# schema which is essentially the V3 schema but with ALL events mixed into a
# single database and differentiated from each other by the event code (and
# possibly a doc type code) on each record.
#
# The V4 data schema was created solely for the benefit of Tableau use because
# Tableau could not handle the data in the V3 schema.  It could not handle
# mixing data from multiple databases (e.g. 2023azva and 2023azgl) and it
# expected data in collections to be homogeneous as it did not provide any
# means of data filtering within a collection (at least not that we could
# discover).
#
# With our shifting away from Tableau due to its super steep learning curve and
# the very limited FRC team license (1 per FRC team and only valid Jan to Aug)
# we no longer need the V4 schema just for scouting data.
#
# We had discussed making a V5 schema that was essentially fully "inverting"
# the V3 schema to be the same as the V4 schema for scouting; databases would
# be named over what they hold (e.g. matches) and collections would be year
# based to keep each different games data separate from one another.  This
# seemed like a logical thing to do at first but it made finding the data we
# want a little more complicated as it involved multiple databases.  Handling
# them all in a script just makes it more complicated than necessary.
#
# Since we switched to Streamlit starting in 2025, we no longer need the
# somewhat inverted data model necessary for Tableau.  As such, instead of
# making the data and database schema more obtuse by "V4-ifying" the remaining
# parts of the V3 schema we are going to take the best parts of both V3 and V4
# to make the V5 schema.  In V5 we have 1 database for ALL FRC data and a
# series of collections to hold all related data.  Where there are multiple
# related but functionally different records in a collection we will use a
# document type specifier which can easily be used on all searches to only
# process the data we need.
#
# Changes:
#   02-Mar-25:
#       Added new V5_COL_TRAINING for holding "ground truth" training data
#       Fixed several PEP nags about whitespace and line length by reflowing
#           or reloacting comments.
#
#   29-Jan-25:
#       Revised the V5 schema design for easier use
#       Removed all but the V5 schema fields in favor of avoiding any
#           confusion with older schema stuff.  Go look at the config.py used
#           with 2024 scripts if you need that history or you are working to
#           update old scripts for use now.
#       Removed unnecessary TBAURL value; it is defaulted in the TBA class
#           methods.
#
#   08-Oct-24:
#       Split all credentials info to a separate file (credentials.py)
#
#   23-Mar-24:
#       Removed unnecessary EVENTS_IN_2024 and DISTRICT_EVENTS_IN_2024
#       Renamed DT_ORP_EPA to DT_OPR_EPA
#

# Mongo database names.
#
# Staring with the V5 schema (2025), the DB_NAME database below is the ONLY
# database we will use to hold ALL FRC related data in various collections.

DB_NAME = "frc_data"            # This dB holds all the FIRST / FRC / TBA data

#
# The V5 collection names.
#
# Data in each collection is indexed using either the relevant event code (e.g.
# 2025azgl) or the team key (e.g. frc6413), depending on the collection being
# used.  For collections that have different kinds of data we will also include
# a document type (aka docType) code.  All docType values are defined further
# down.
#
# It is also possible that data in a collection may be indexed by a compound
# key such as the event, competition level and match code.  For example,
# 2024azgl_sf4m1 is the key for the match data for match 1 of Semi-finals 4 at
# the 2024 Arizona East event.

# This collection is intended to hold misc kinds of data (e.g. POSSIBLY
# Last-Modified timestamps, etc)
V5_COL_DATA = "data"

# This collection holds all event related data (e.g. event or district info
# by year, etc)
V5_COL_EVENTS = "events"

# This collection holds all match data reported by FMS/TBA keyed off the event
# code and match key.  For example, "2024azgl_f1m1" would be match data for
# Finals 1, Match 1 at the 2024 Arizona East Regional.
V5_COL_MATCH = "matches"

# This collection holds all schedule data keyed off the event code and match
# key.  For example, "2024azgl_f1m1" would be schedule data for Finals 1, Match
# 1 at the 2024 Arizona East Regional.
V5_COL_SCHEDULE = "schedule"

# This collection holds our collected prescout, pit and match scouting data
V5_COL_SCOUTING = "scouting"

# This collection is intended to hold any calculated stats we want to serve up
# (MAY NOT actually be used if we go with dynamic stat calculations)
V5_COL_STATISTICS = "statistics"

# This collection holds team registration and historical data
V5_COL_TEAMS = "teams"

# This collection holds scouter training data (to check training data against)
# The data in this collection is NEARLY IDENTICAL in format to the data in
# V5_COL_MATCH.  Docs in this collection will only contain data that would
# come from the scouting app; it will not contain any extra or calculated data.
# The reason it is separate is to avoid causing any mess on the strategy
# dashboard by showing data for random events or seemingly having partial
# random event data for only some robots at some events.
# The ONLY docTypes found in this collection should be DT_SCOUTING_MATCH.
V5_COL_TRAINING = "training"


#
# The V5 document types:
#
# The different kinds of data will be tagged with a docType item value that
# identifies the type of data the doc contains.  Index keys are normally
# constructed using the event code followed by a match code, a team code or a
# combination of both depending on the case.  See the descriptions below for
# examples.

#
# NOTE: We have yet to look at let alone settle on what kind of event data we
# pull from FIRST / TBA and save.  As such the following is subject to change
# as the 2025 season progresses!
#
# These are the document types for data stored in the event collection (V5_COL_EVENTS):
#

# The document holds data for an event (Regional OR District/District
# Championship).  The index key value is the event code.
# TODO: Should this be just keyed to year?  Need to revisit what kind of data
# we get from FIRST / TBA before we can decide...
DT_EVENTS_EVENT = "event"

# The document holds data for a District.  The index key value is the district
# code.
DT_EVENTS_DISTRICT = "district"

# The document holds data about teams at any event.  The index key value is the
# event and team code.
DT_EVENTS_TEAMS = "teams"


#
# These are the document types for data stored in the scouting collection (V5_COL_SCOUTING):
#

# Doc that holds pit scouting data.  The key value is a combination of the
# teams FRC key and the event code.   For example, "frc254_2024cada" would be
# for Team 254 at the 2024 Sacramento Regional.
DT_SCOUTING_PIT = "pit"

# Doc that holds prescouting scouting data.  The key value is a combination of
# the teams FRC key and the event code for the event being pre-scouted.  For
# example, "frc254_2024cabe" would be for prescouting Team 254 FOR the 2024
# East Bay Regional rather than AT the 2024 East Bay Regional.
DT_SCOUTING_PRESCOUT = "prescout"

# Doc that holds data collected by scouts.  The key value is constructed from
# the event code, the match key, and the team key.  For example,
# "2022azva_qm37_frc5933" is the key for Team 5933 in Qualifier 37 at the 2022
# Arizona Valley Regional.
# I MAY consider reformatting to a different format such as event_key + team
# key + comp_level + str(match_number) which would look like
# 2022azva_frc5933_qm37.  That MIGHT make it easier to find all of a teams
# matches (e.g. "_id contains 2022azva_frc5933_*").
DT_SCOUTING_MATCH = "match"

#
# NOTE: We have yet to really settle on a format for how all statistical data
# is retrieved or calculated and saved.  As such the following is subject to
# change as the 2025 season progresses!
#
# These are the document types for data stored in the statistics collection (V5_COL_STATISTICS):
#

# "Offensive Power Rating"  It is the calculated contribution by that team on
# average to all the matches they were involved in
DT_STATISTICS_OPR = "opr"

# "Defensive Power Rating"  Calculated just like OPR, except you use the
# opposing alliance’s score instead of your own alliance’s score
DT_STATISTICS_DPR = "dpr"

# “Calculated Contribution to Winning Margin”  It is similar to OPR but also
# gives credit to defensive robots
DT_STATISTICS_CCWM = "ccwm"

# The Statbotics stat which estimates a teams skill.  It is a measure of a
# teams on-field strength calculated using win margins.  It is NOT officially
# part of TBA data but we may still pull it.  Since there are TONS of stats
# already we MAY NOT actually use this...
DT_STATISTICS_EPA = "epa"
#
# Competition levels:
#   qm = Qualifiers
#   qf = Quarter finals (OBSOLETE as of 2024 when FIRST went to Double Elimination Playoffs)
#   sf = Semi finals
#   f = Finals

MATCHLEVEL_QUALIFIERS = "qm"
MATCHLEVEL_QUARTERS = "qf"
MATCHLEVEL_SEMIS = "sf"
MATCHLEVEL_FINALS = "f"

#
# Team specific info
#
# There are 2 sets of team data available from TBA:
#
#   The "teams" collection is mostly "high level" a brief bit of data of active
#       teams that contains some basic contact type data and team history.
#   The "teams_detailed" collection contains all the rich team details of
#       active teams including extra stuff not available in the "teams" data.
#       The plan is to collect ALL of a teams data (per active year) and put it
#       into their "detailed" record.  That means we will need to construct a
#       new array to hold the yearly data such as how they did each year (or
#       perhaps where they went and more)
#
# TODO: Should this be used as a docType for docs that get saved into the teams collection (V5_COL_TEAMS)??

ALL_TEAMS = "teams"
ALL_TEAMS_DETAILED = "teams_detailed"

#
# Fields to be used for prescouting templates
PRESCOUTING_FIELDS = [
    "Strengths",
    "Weaknesses",
    "Observations"                      # Important or useful observations
]
