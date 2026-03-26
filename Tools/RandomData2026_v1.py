# This is the initial version of the random scouting data creator for 2026s
# game.
#
# The script DOES use some weighting to generate score increases/decreases
# between matches so we can see likely trends in Tableau or Plotly.

from random import randint, uniform, shuffle

# 2026 Scouting Data item indexes.  0 - 5 will NEVER change because they
# are NOT game dependent.  Game specific values start at 6.  I use names
# to make the code easier to follow.
#
# The teams array is made up of several lists that encode match data and other
# info we need to create trending data to visualize.  Each list is made up of
# the following data values:

TEAMNUM = 0                 # The team number
TEAMNAME = 1                # The team name (UNUSED)
AUTOSCORECHANGEFACTOR = 2   # The auto scoring change over time factor
AUTORANDOMIZEFACTOR = 3     # The auto randomization factor for each change
TELESCORECHANGEFACTOR = 4   # The teleop scoring change over time factor
TELERANDOMIZEFACTOR = 5     # The teleop randomization factor for each change
CANAUTOHUB = 6              # (Auto) The robot can score in the Hub (True/False)
CANTELEHUB = 7              # (Teleop) The robot can score in the Hub (True/False)
                            # NOTE: There is only 1 scoring location in 2026 so if
                            # a robot cannot score in the Hub they are effectively
                            # a framebot that can only do defense.  So far there have
                            # not been any framebots at events so for 2026 EVERY robot
                            # should have this set to True!  That may not be true for 2027...
MATCHCOUNT = 8              # The number of matches we have created data for
HUB = 9                     # (Teleop) Processor score count
HUBMISS = 10                # (Teleop) Processor miss count
                            # NOTE: For 2026 we are NOT tracking misses due to the volume of
                            # game pieces used.  However to keep the tool reusable it will
                            # still create a miss count even though live data will NEVER have
                            # a non-0 miss count.

# The maximum number of game pices that can get scored in a match.  Keep this
# at a reasonable number for TYPICAL teams.  Do NOT try to use Top 1% teams as
# the benchmark.
MAXGAMEPIECES = 150

# This years game piece preload limit
MAXPRELOAD = 8

# The actual team array
a_Teams = [
    # num  name                  ASCF    ARF     TSCF    TRF     CAN...        MATCH...
    [60,   "Bulldogs",           -0.2,   0.1,    0.3,    0.4,    False, True,  1, 0, 0],
    [498,  "Cobra Commanders",   0.7,    0.5,    2.1,    1.5,    True, True,   1, 0, 0],
    [698,  "Hamilton Microbots", 2,      6,      -0.2,   0.3,    False, True,  1, 0, 0],
    [991,  "BroncoBots",         -1,     0,      -1,     3,      False, True,  1, 0, 0],
    [1165, "Team Paradise",      0.8,    2,      0.8,    1.1,    False, True,  1, 0, 0],
    [1212, "Sentinels",          -2,     1.5,    0.5,    1.6,    False, True,  1, 0, 0],
    [1726, "N.E.R.D.S.",         0.5,    2.1,    0.9,    4,      False, True,  1, 0, 0],
    [2262, "RoboKrew",           0.4,    0.5,    0.76,   0.8,    False, True,  1, 0, 0],
    [2403, "Plasma",             0.5,    0.3,    1.8,    1.1,    True, True,   1, 0, 0],
    [2478, "Westwood",           1.2,    1,      1.2,    0.8,    False, True,  1, 0, 0],
    [2486, "CocoNuts",           1,      0,      2,      1.3,    True, True,   1, 0, 0],
    [3944, "All Knights",        0,      1,      0,      1.9,    False, True,  1, 0, 0],
    [4146, "Sabercats",          0.1,    4,      0.1,    0.7,    False, True,  1, 0, 0],
    [4183, "Bit Buckets",        0.2,    3,      0.2,    1.1,    False, True,  1, 0, 0],
    [5539, "DVHS Cyborgs",       0.2,    0.8,    -0.2,   0.8,    False, True,  1, 0, 0],
    [6352, "LAUNCH TEAM",        0.5,    0.2,    0.5,    0.2,    False, True,  1, 0, 0],
    [6413, "Degrees of Freedom", 2,      1,      1.8,    2,      True, True,   1, 0, 0],
    [6479, "AZTECH",             0.5,    0.6,    1.5,    0.6,    False, True,  1, 0, 0],
    [6656, "Ryu Botics",         0.76,   1.2,    0.75,   1,      False, True,  1, 0, 0],
    [6833, "Phoenix",            -0.5,   0,      -0.5,   0.4,    False, True,  1, 0, 0],
    [8021, "Panther Robotics",   0.4,    2,      0.4,    0.8,    False, True,  1, 0, 0],
    [8087, "Cougar Pride",       0,      1,      0,      1,      False, True,  1, 0, 0],
    [8848, "Blu CREW",           0.8,    2,      0.8,    0.7,    False, True,  1, 0, 0],
    [9059, "COLTech",            0.6,    0.4,    0.7,    1,      False, True,  1, 0, 0]
    ]


def calcNewScore(currentScore: float, scoreChangeFactor: float, randomizeFactor: float) -> int:
    """
    Calculate a new score based on the current score, score change factor,
    and randomize factor.

    Args:
        currentScore (float): The current score.
        scoreChangeFactor (float): The factor by which the score should change.
        randomizeFactor (float): The factor by which the score change should be
                randomized.

    Returns:
        float: The new score.
    """
    # Calculate a random decrease or increase amount for adjusting the score
    # using previous value as a starting point.
    increase = scoreChangeFactor + uniform(randomizeFactor * -1, randomizeFactor)

    # Update the score with the random increase/decrease amount
    newScore = round(currentScore + increase, 0)

    # Make sure there is no negative score
    if newScore < 0:
        newScore = 0

    return int(newScore)


# Preassign random scores to each team so we have a starting point for
# increases/decreases
for team in range(len(a_Teams)):
    gamePieces = randint(0, MAXGAMEPIECES)
    a_Teams[team][HUB] = 0 if not a_Teams[team][CANTELEHUB] else gamePieces
    a_Teams[team][HUBMISS] = 0 if not a_Teams[team][CANTELEHUB] else randint(0, MAXGAMEPIECES - gamePieces)

# Output the starting bounding JSON container
print("[")

# Lets generate 40 matches worth of random data for randomly selected teams.
# We will shuffle the a_Teams array each round and order them by the number of
# rounds played to try and make every team get the same number of matches.
# Once we have that list we can create some random results.
for matchNum in range(1, 41):
    # Shuffle the teams...
    shuffle(a_Teams)

    # Order them by the number of rounds...
    a_Teams.sort(key=lambda x: x[MATCHCOUNT])

    # Grab the first 6 teams from the results of all that
    for team in range(6):
        # Bump the teams completed match count.
        a_Teams[team][MATCHCOUNT] += 1

        # Autonomous phase values (NOT saved in the team array)

        if not a_Teams[team][CANAUTOHUB]:
            autoHub = 0
            autoHubMiss = 0
        else:
            autoHub = calcNewScore(
                randint(0, MAXPRELOAD),
                a_Teams[team][AUTOSCORECHANGEFACTOR],
                a_Teams[team][AUTORANDOMIZEFACTOR],
            )

            autoHubMiss = MAXPRELOAD - autoHub

        # The Pythonic way of doing the above is:
        # autoHub = 0 if not a_Teams[team][CANAUTOHUB] else calcNewScore(randint(0, MAXPRELOAD), a_Teams[team][AUTOSCORECHANGEFACTOR], a_Teams[team][AUTORANDOMIZEFACTOR])
        # autoHubMiss = 0 if not a_Teams[team][CANAUTOHUB] else MAXPRELOAD - autoHub

        # Teleop phase values (SAVED in the team array)

        if not a_Teams[team][CANTELEHUB]:
            a_Teams[team][HUB] = 0
            a_Teams[team][HUBMISS] = 0
        else:
            a_Teams[team][HUB] = calcNewScore(
                a_Teams[team][HUB],
                a_Teams[team][TELESCORECHANGEFACTOR],
                a_Teams[team][TELERANDOMIZEFACTOR],
            )

            a_Teams[team][HUBMISS] = calcNewScore(
                a_Teams[team][HUBMISS],
                a_Teams[team][TELESCORECHANGEFACTOR],
                a_Teams[team][TELERANDOMIZEFACTOR],
            )

        # The Pythonic way to the above is:
        # a_Teams[team][HUB] = 0 if not a_Teams[team][CANTELEHUB] else calcNewScore(a_Teams[team][HUB], a_Teams[team][TELESCORECHANGEFACTOR], a_Teams[team][TELERANDOMIZEFACTOR])
        # a_Teams[team][HUBMISS] = 0 if not a_Teams[team][CANTELEHUB] else calcNewScore(a_Teams[team][HUBMISS], a_Teams[team][TELESCORECHANGEFACTOR], a_Teams[team][TELERANDOMIZEFACTOR])

        # End game phase values (NOT saved in the team array)
        # For 2026 we will do the Teleop observation checks here instead since
        # there is no end game stuff we are tracking.

        teleRelay = randint(0, 1)
        teleHerd = randint(0, 1)

        comments = "There were " + str(randint(0, 20)) + " people yelling this match."

        # NOT going to try and get fancy with random secondary stats like stopping, no show, etc

        matchResults = (
            f'"key":{a_Teams[team][TEAMNUM]},"mn":{matchNum},"cl":"qm","i":"Python",'
            f'"a1":{autoHub},"a2":{autoHubMiss},'
            f'"t1":{a_Teams[team][HUB]},"t2":{a_Teams[team][HUBMISS]},'
            f'"ns":0,"d":0,"r":{teleRelay},"h":{teleHerd},'
            f'"co":"{comments}"'
            )

        # Output the record as a JSON object
        print("{")
        print(matchResults)
        print("},")

# Finish the bounding JSON container
print("]")
