import config as cfg
import pandas as pd
import streamlit as st
import utils
from pandas import DataFrame


def write_niche_table (df: DataFrame, teams: list, stat_keys: list, accuracy_keys: list, calculation: int) -> None:
    """Writes a niche table, putting all ``teams`` on a separate row with columns according to ``stat_keys``

    Raw values are calculated with a normalization formula that is <team's calculated value> / <highest value in list of all team's calculated value>

    Values depend on the passed ``calculation``.

    If ``stat_keys`` has the same length as ``accuracy_keys``, it will also write "accuracy adjusted" colummns for each stat, which is just the product of the raw value and the corresponding accuracy

    Args:
        df (DataFrame): Match DataFrame to get data from.
        teams (list): List of all teams to show data for.
        stat_keys (list): List of selected stat_keys to calculate values for. Should correspond to columns in ``df``.
        accuracy_keys (list): List of selected accuracy_keys to calculate "accuracy adjusted" values for. Length should be equal to ``stat_keys` length if accuracy adjusted values are desired. Should correspond to columns in ``df``.
        calculation (int): The calculation method to perform to get the stat. 0: mean, 1: upper quartile, 2: max.

    Returns:
        None. Writes the table directly.
    """
    # List of all the best team's values for each stat
    best_vals: list = list()

    # Iterates over all stats and adds the highest values for each stat according to the calculation method
    for stat in stat_keys:
        if calculation == 0:
            # List of team's means for the stat
            team_stat_vals: list = [df[df["team"]==team][stat].mean() for team in teams]
        elif calculation == 1:
            # List of team's upper quartile for the stat
            team_stat_vals: list = [df[df["team"]==team][stat].quantile(0.75) for team in teams]
        if calculation == 2:
            # List of team's maxs for the stat
            team_stat_vals: list = [df[df["team"]==team][stat].max() for team in teams]

        # Append the highest value in the list of team's values for the stats to best_vals.
        stat_best = max(team_stat_vals)
        best_vals.append(stat_best)

    # Whether we should only include the "raw" value columns. If False, we will include the "accuracy adjusted" columns.
    raw_only = False
    if len(stat_keys) != len(accuracy_keys):
        raw_only = True

    # List of all table columns
    # Always includes "Team" - team number and "Total (Raw)" - The total of all the raw stat fields
    # Iterates over every stat key and adds a raw column value for it. Also adds an accuracy adjusted value if we aren't only using raw values.
    table_columns = (["Team"] +
                    ["Total (Raw)"] +
                    [f"{cfg.STAT_KEY_TO_TEXT[stat]} (Accuracy Adjusted)"
                            for stat in stat_keys if not raw_only] +
                    [f"{cfg.STAT_KEY_TO_TEXT[stat]} (Raw)"
                            for stat in stat_keys])
    # Adds the accuracy adjusted total if we aren't only using raw values
    if not raw_only:
        table_columns.insert(1, "Total (Accuracy Adjusted)")

    # The table DataFrame
    table_df: DataFrame = DataFrame(columns=table_columns)

    # Iterate over every team and add a row to the table for it
    for team in teams:
        # DataFrame filtered to the team's entries
        team_df: DataFrame = df[df["team"]==team]

        # Gets the team's values for each stat based on the given calculation method
        if calculation == 0:
            # List of team's means for the stat
            team_vals: list = [team_df[key].mean() for key in stat_keys]
        elif calculation == 1:
            # List of team's upper quartile for the stat
            team_vals: list = [team_df[key].quantile(0.75) for key in stat_keys]
        elif calculation == 2:
            # List of team's maxs for the stat
            team_vals: list = [team_df[key].max() for key in stat_keys]

        # Normalizes the values to convert them from unit-based metrics to unitless scores from 0-1
        scores: list = [float(val / best_vals[i]) for i, val in enumerate(team_vals)]

        # The row for the team's values
        row: dict = dict({
            "Team": team,
            "Total (Raw)": sum(scores) / len(scores),
        })
        # If we are using accuracy adjusted values, add those columns to the row
        if not raw_only:
            # List of team's accuracies from the accuracy_keys
            team_accuracies: list = [team_df[key].mean() for key in accuracy_keys]
            # List of scores adjusted to the corresponding accuracy (score * accuracy)
            scores_accuracy_adj: list = [score * team_accuracies[i] for i, score in enumerate(scores)]

            # Adds the accuracy adjusted total score to the row
            row.update({"Total (Accuracy Adjusted)": sum(scores_accuracy_adj) / len(scores_accuracy_adj)})
            # Adds the accuracy adjusted stats to the row
            row.update(dict((f"{cfg.STAT_KEY_TO_TEXT[stat_keys[i]]} (Accuracy Adjusted)", val) for i, val in enumerate(scores_accuracy_adj)))
        # Adds the raw stat columns to the row
        row.update(dict((f"{cfg.STAT_KEY_TO_TEXT[stat_keys[i]]} (Raw)", val) for i, val in enumerate(scores)))

        # Creates row_df, which is just the row as a DataFrame
        row_df: DataFrame = DataFrame(row, index=[1])

        # Adds the row_df to the table_Df
        table_df = pd.concat([table_df, row_df])

    def highlight_rows(val: DataFrame):
        """Highlight rows to indicate caution to user if the team doesn't fulfill niches

        Orange is used to indicate that the team fulfills some but not all niches. Red is used to indicate that the team fulfills none of the niches.

        Args:
            val (DataFrame): DataFrame row from the table_df

        Returns:
            list: List of styles to apply to the row's columns. List of empty strings to apply no styles
        """
        # row columns excluding the team number
        non_team_vals: DataFrame = val.drop("Team")

        # If max of non_team_vals is 0, none of the team's scores are above 0. The team hasn't demonstrated any of the niches
        if max(non_team_vals) == 0:
            return ['background-color: tomato'] * len(val)      # Multiplying the style by the length of val ensures every column in the row gets highlighted
        # If min of non_team_vals is 0, at least one of the team's scores is 0. The team hasn't demonstrated all of the niches
        elif min(non_team_vals) == 0:
            return ['background-color: lightsalmon'] * len(val) # Multiplying the style by the length of val ensures every column in the row gets highlighted
        # If neither of the previous checks are true, the team has demonstrated the ability to fulfill all of the niches.
        # No highlights will be applied
        else:
            return [""] * len(val)                              # Multiplying the style by the length of val ensures every column in the row gets highlighted

    # Sort the table by the the raw total if raw only, or the accuracy adjusted total otherwise
    table_df = table_df.sort_values(
                                    by=("Total (Raw)"
                                        if raw_only
                                        else "Total (Accuracy Adjusted)"),
                                        ascending=False)
    # Reset the table's index by generating new integers for each row (Necessary for styling)
    table_df = table_df.reset_index(drop=True)
    # A version of the table with row highlights applied based on the team's demonstrated ability to fulfill the desired niches
    # Also formats the DataFrame to round all values to two decimal points.
    styled_df = table_df.style.apply(highlight_rows, axis=1).format(precision=2)

    # Writes the styled DataFrame as a table
    st.dataframe(
        data=styled_df,             # DataFrame to write the table with
        height=1000,                # Height of the table. Set to large number so it fills the height of the page
        use_container_width=True,   # Use all the available width in the container
        hide_index=True,            # Hide the index of the table
    )


def main ():
    # Write page title
    st.title("Niche Finder")

    # Writes three columns to hold inputs in
    # First for desired stats, second for corresponding accuracies, and third for calculation method
    cols = st.columns(3)
    with cols[0]:
        selected_stats: list = utils.stat_selector("niche_finder_stats", True, "I want a team that can...")
    with cols[1]:
        selected_accuracies: list = utils.stat_selector(selector_key="niche_finder_accuracies", multiselect=True, custom_label="(Opt.) Use the corresponding accuracies...", custom_options=cfg.SELECTABLE_ACCURACY_KEYS)
    with cols[2]:
        calculation_options: list = ["Mean", "Upper Quartile", "Max"]
        calculation_select: str = st.selectbox("Using the calculation...", ["Mean", "Upper Quartile", "Max"])
        calculation_index: int = calculation_options.index(calculation_select)

    # Require stats are selected to proceed
    if len(selected_stats) == 0:
        st.warning("Select at least one stat and accuracy to find a niche.")
        return

    # Gets the match DataFrame to use for data
    df: DataFrame = utils.get_match_data ()
    # Gets the teams list of teams to show data for
    event_teams = utils.get_event_teams(st.session_state["currentEventCode"])
    filtered_teams = [team for team in event_teams if len(df[df["team"]==team]) > 0]

    # Writes short explanation of what the row highlights mean
    st.write("ORANGE: Teams that haven't demonstrated the ability to fill all the specified niches.")
    st.write("RED: Teams that haven't demonstrated the ability to fill any of the specified niches.")

    # Writes the table, with one row per team
    write_niche_table(df, filtered_teams, selected_stats, selected_accuracies, calculation_index)

main()
