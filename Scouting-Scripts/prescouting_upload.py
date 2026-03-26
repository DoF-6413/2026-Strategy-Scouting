# This script gets prescouting notes from a document specified at run. This
# file should be from a template generated with prescouting_make_template.py
# that is exported as markdown.
#
# It pulls the team numbers and notes for a team from H1s. Within team notes
# it pulls field names from H2s and the corresponding body of those headers.
#
# Data is exported to a MongoDB using the PRIMARY_CONNECTION_STRING credential URL
# This script currently does NOT support also exporting to any
# SECONDARY_CONNECTION_STRING URL!
#
# Each entry is one team
#
# Exported data keys:
# _id: "{eventCode}_frc{team}_prescouting"
# docType: always "prescout"
# eventCode: The eventcode the prescouting notes are used to prepare for (prompted on run)
# team: the team number

import sys
import re
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.results import DeleteResult, InsertManyResult
import config as cfg
import credentials as creds


def process_notes_file(input_file: str, event_code: str) -> Optional[List[Dict[str, Any]]]:
    """Processes the notes file and returns structured data.

    Args:
        input_file: The path to the input notes file.
        event_code: The event code associated with the notes.

    Returns:
        A list of dictionaries, where each dictionary represents a team's notes OR
        None if an error occurs during file processing.
    """
    try:
        with open(input_file, "r", encoding="utf8") as file:
            input_text: str = file.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return None

    try:
        raw_notes_list: List[str] = re.split(r"# \d+ ?.+", input_text)
        raw_notes_list.pop(0)
        teams: List[str] = re.findall(r"(?<=# )\d+(?= ?.+)", input_text)

        # Simple sanity check to catch bad Markdown
        if len(teams) != len(raw_notes_list):
            raise ValueError("Number of teams and note blocks do not match.")

        data: List[Dict[str, Any]] = []
        for team, raw_team_notes in zip(teams, raw_notes_list):
            headers_list: List[str] = re.findall(r"(?<=## ).+", raw_team_notes)
            team_notes_list: List[str] = re.split(r"## .+", raw_team_notes)
            team_notes_list.pop(0)
            team_notes_list = [note.strip() for note in team_notes_list]

            if len(headers_list) != len(team_notes_list):
                raise ValueError(f"Number of headers and notes for team {team} do not match")

            notes: Dict[str, str] = dict(zip(headers_list, team_notes_list))

            entry: Dict[str, Any] = {
                "_id": f"{event_code}_frc{team}_prescouting",
                "docType": cfg.DT_SCOUTING_PRESCOUT,
                "eventCode": event_code,
                "team": team,
                "notes": notes
            }

            data.append(entry)

        return data

    except (ValueError, IndexError) as e:
        print(f"Error processing notes: {e}")
        return None


def write_to_mongodb(data: Optional[List[Dict[str, Any]]], event_code: str) -> None:
    """Writes the processed data to MongoDB.

    Args:
        data: A list of dictionaries, where each dictionary represents a team's notes.
            Can be None if there was an error processing the notes file.
        event_code: The event code to save the data under.
    """
    try:
        with MongoClient(creds.PRIMARY_CONNECTION_STRING) as client:
            db = client[cfg.DB_NAME]
            collection = db[cfg.V5_COL_SCOUTING]

            # Clean out any preexisting prescouting notes for the event
            result: DeleteResult = collection.delete_many({
                "docType": cfg.DT_SCOUTING_PRESCOUT,
                "eventCode": event_code
            })

            # If we have prescouting data to import, do it.
            if data:
                result: InsertManyResult = collection.insert_many(data)
                if result.acknowledged:
                    print(f"Wrote prescouting data under {event_code}")
            else:
                print("No data was written to the database")

    except Exception as e:
        print(f"Error writing to MongoDB: {e}")


def main() -> None:
    """Main function to run the script."""
    event_code: str = input("Enter event code the notes are prescouting for ('quit' to exit): ").strip()

    if event_code.lower() == "quit":
        print("Script terminated by user.")
        sys.exit(0)

    while True:
        input_file: str = input("Enter the Markdown file to import ('quit' to exit): ").strip()

        if input_file.lower() == "quit":
            print("Script terminated by user.")
            sys.exit(0)

        data: Optional[List[Dict[str, Any]]] = process_notes_file(input_file, event_code)

        if data:
            write_to_mongodb(data, event_code)


if __name__ == "__main__":
    main()
