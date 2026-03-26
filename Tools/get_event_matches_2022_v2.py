# This is a sample Python script to geta list of matches for the given event
# from TBA and display it.
#
# NOTE: There is NO ordering to the match data!  In addition, you can get all
# levels of data when not using an if-modified-since value; depending on what
# has taken place from the beginning!
#
# This is a 2025 update to get_event_matches_2022.py.  Changes include:
#
# 1: Removed Python 2.x legacy line:
#        from __future__ import print_function
# 2: Added prompt for any event code
# 3: Added __name__ check
#
# NOTE: If the imports fail below, make sure you are using the venv environment
# where the TBA libraries are installed.  They are NOT installed in the base OR
# scrapy environments!!

import sys
import tbaapiv3client
from tbaapiv3client.rest import ApiException
from pprint import pprint
import credentials as creds

# Example output:
# (venv) D:\Workspace\TBA-python>python get_event_matches_2022_v2.py
# Enter the event code for the event to get data for (or 'quit' to exit): [{'actual_time': 1740876490,
#  'alliances': {'blue': {'dq_team_keys': [],
#                         'score': 136,
#                         'surrogate_team_keys': [],
#                         'team_keys': ['frc9408', 'frc3009', 'frc5199']},
#                'red': {'dq_team_keys': [],
#                        'score': 146,
#                        'surrogate_team_keys': [],
#                        'team_keys': ['frc4415', 'frc8871', 'frc6995']}},
#  'comp_level': 'f',
#  'event_key': '2025caoc',
#  'key': '2025caoc_f1m1',
#  'match_number': 1,
#  'post_result_time': 1740876696,
#  'predicted_time': 1740876481,
#  'score_breakdown': {'blue': {'adjustPoints': 0,
#                               'algaePoints': 0,
#                               'autoBonusAchieved': False,
#                               'autoCoralCount': 3,
#                               'autoCoralPoints': 21,
#                               'autoLineRobot1': 'Yes',
#                               'autoLineRobot2': 'Yes',
#                               'autoLineRobot3': 'Yes',
#                               'autoMobilityPoints': 9,
#                               'autoPoints': 30,
#                               'autoReef': {'botRow': {'nodeA': False,
#                                                       'nodeB': False,
#                                                       'nodeC': False,
#                                                       'nodeD': False,
#                                                       'nodeE': False,
#                                                       'nodeF': False,
#                                                       'nodeG': False,
#                                                       'nodeH': False,
#                                                       'nodeI': False,
#                                                       'nodeJ': False,
#                                                       'nodeK': False,
#                                                       'nodeL': False},
#                                            'midRow': {'nodeA': False,
#                                                       'nodeB': False,
#                                                       'nodeC': False,
#                                                       'nodeD': False,
#                                                       'nodeE': False,
#                                                       'nodeF': False,
#                                                       'nodeG': False,
#                                                       'nodeH': False,
#                                                       'nodeI': False,
#                                                       'nodeJ': False,
#                                                       'nodeK': False,
#                                                       'nodeL': False},
#                                            'tba_botRowCount': 0,
#                                            'tba_midRowCount': 0,
#                                            'tba_topRowCount': 3,
#                                            'topRow': {'nodeA': False,
#                                                       'nodeB': False,
#                                                       'nodeC': False,
#                                                       'nodeD': True,
#                                                       'nodeE': False,
#                                                       'nodeF': False,
#                                                       'nodeG': True,
#                                                       'nodeH': False,
#                                                       'nodeI': True,
#                                                       'nodeJ': False,
#                                                       'nodeK': False,
#                                                       'nodeL': False},
#                                            'trough': 0},
#                               'bargeBonusAchieved': False,
#                               'coopertitionCriteriaMet': False,
#                               'coralBonusAchieved': False,
#                               'endGameBargePoints': 26,
#                               'endGameRobot1': 'Parked',
#                               'endGameRobot2': 'DeepCage',
#                               'endGameRobot3': 'DeepCage',
#                               'foulCount': 0,
#                               'foulPoints': 0,
#                               'g206Penalty': False,
#                               'g410Penalty': False,
#                               'g418Penalty': False,
#                               'g428Penalty': False,
#                               'netAlgaeCount': 0,
#                               'rp': 0,
#                               'techFoulCount': 0,
#                               'teleopCoralCount': 18,
#                               'teleopCoralPoints': 80,
#                               'teleopPoints': 106,
#                               'teleopReef': {'botRow': {'nodeA': False,
#                                                         'nodeB': False,
#                                                         'nodeC': False,
#                                                         'nodeD': True,
#                                                         'nodeE': False,
#                                                         'nodeF': False,
#                                                         'nodeG': False,
#                                                         'nodeH': False,
#                                                         'nodeI': False,
#                                                         'nodeJ': False,
#                                                         'nodeK': False,
#                                                         'nodeL': False},
#                                              'midRow': {'nodeA': True,
#                                                         'nodeB': True,
#                                                         'nodeC': True,
#                                                         'nodeD': True,
#                                                         'nodeE': True,
#                                                         'nodeF': True,
#                                                         'nodeG': False,
#                                                         'nodeH': False,
#                                                         'nodeI': True,
#                                                         'nodeJ': True,
#                                                         'nodeK': False,
#                                                         'nodeL': False},
#                                              'tba_botRowCount': 1,
#                                              'tba_midRowCount': 8,
#                                              'tba_topRowCount': 12,
#                                              'topRow': {'nodeA': True,
#                                                         'nodeB': True,
#                                                         'nodeC': True,
#                                                         'nodeD': True,
#                                                         'nodeE': True,
#                                                         'nodeF': True,
#                                                         'nodeG': True,
#                                                         'nodeH': True,
#                                                         'nodeI': True,
#                                                         'nodeJ': True,
#                                                         'nodeK': True,
#                                                         'nodeL': True},
#                                              'trough': 0},
#                               'totalPoints': 136,
#                               'wallAlgaeCount': 0},
#                      'red': {'adjustPoints': 0,
...

if __name__ == "__main__":
    eventCode: str = input("Enter the event code for the event to get data for (or 'quit' to exit): ").strip()

    if eventCode.lower() == "quit":
        print("The session was aborted at the event code prompt")
        sys.exit(0)

    # Configure API key authorization: apiKey
    configuration = tbaapiv3client.Configuration(api_key={'X-TBA-Auth-Key': creds.TBA_AUTH_KEY})

    # Enter a context with an instance of the API client
    with tbaapiv3client.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = tbaapiv3client.EventApi(api_client)

        try:
            api_response = api_instance.get_event_matches(eventCode)
            pprint(api_response)
        except ApiException as e:
            print("Exception when calling EventApi.get_event_matches: %s\n" % e)
