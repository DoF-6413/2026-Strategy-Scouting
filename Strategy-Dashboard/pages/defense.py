
import config as cfg
import streamlit as st
import utils
from pandas import DataFrame, concat
from pymongo.database import Database


@st.cache_data(ttl=90)
def get_defense_data() -> DataFrame:
    db: Database = utils.get_mongo_db()
    collection = db[cfg.V5_COL_SCOUTING]

    # Convert the data to a DataFrame
    df: DataFrame = DataFrame(list(collection.find({
        "eventCode": {"$in": st.session_state["dataEventCodes"]},
        "defense": {"$exists": True}
    })))

    return df

def get_team_defense_entries(defense_df: DataFrame, team: str) -> DataFrame:
    team_df = defense_df[defense_df["_id"].str.split("_frc").str[1] == team]

    return team_df


def main():
    st.title("Defense ratings")

    defense_df: DataFrame = get_defense_data()

    event_teams = utils.get_event_teams(st.session_state["currentEventCode"])
    if len(event_teams)==0:
        st.write("No teams found for event.")
    #filtered_teams = [team for team in event_teams if len(defense_df[defense_df["team"]==team]) > 0]

    # Separate DataFrame which holds the information that will be written to the displayed table
    table_df = DataFrame()
    # Calculate the mean of the each of the table_keys for each team
    for team in event_teams:
        team_defense_df: DataFrame = get_team_defense_entries(defense_df, team)
        if len(team_defense_df) == 0:
            continue

        team_row = dict()
        # Sets the value of the Team column to the team number
        team_row["Team"] = str(team)
        mean = team_defense_df["defense"].mean().round(2)       # Gets the team's mean in the stat rounded to two decimal points
        team_row["Average Defense Rating"] = mean           # Adds a column to the row with the value of the mean.

        non_attempt_filtered_data = team_defense_df[team_defense_df["defense"]!=0]
        adj_mean = round(non_attempt_filtered_data["defense"].mean(), 2)       # Gets the team's mean defense rating rounded to two decimal points
        team_row["Average Defense on Attempt"] = adj_mean           # Adds a column to the row with the value of the mean.


        max = team_defense_df["defense"].max()       # Gets the team's max defense rating
        team_row["Best Defense Rating"] = max           # Adds a column to the row with the value of the max.


        # Add the team's row to the end of the table
        table_df = concat([table_df, DataFrame([team_row])], ignore_index=True)

    # Sort the table using the values in the first column
    table_df = table_df.sort_values(by="Average Defense Rating", ascending=False)

    # Write the table
    st.dataframe(
        data=table_df,                  # DataFrame to write the table with
        height=1000,                    # The height of the table. Here it's just a large number because the table should fill the rest of the page
        use_container_width=True,       # Use all the available width in the container
        hide_index=True,                # Hide the DataFrame's index
    )

main()
