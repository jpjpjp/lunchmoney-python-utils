"""find_duplicates.py

   This module provides a function for identifying duplicate transactions
   in two dataframes
"""

import pandas as pd


def filter_matches_by_account(matches, account, acct_field_name, acct_name_df):
    """ This function takes a dataframe of possible transaction the old_df
        passed to find_duplicates that match the date range and amount of the current
        transaction being analyzed in new_df

        It removes potential matches that don't have the same account name, or
        an account name listed as a synonym in account_name_map.csv
    """
    account = account.strip()
    if acct_name_df is not None and account in acct_name_df.columns:
        processed_matches = matches[acct_field_name].str.lower().str.strip()
        processed_acct_names = acct_name_df[account].str.lower().str.strip().unique()
        return matches[processed_matches.isin(processed_acct_names)]
    else:
        return matches[
            matches["Account Name"].str.lower().str.strip() == account.lower()
        ]


def find_duplicates(
    new_df,
    old_df,
    update_fn,
    acct_name_df=None,
    lookback_days=0,
    lookahead_days=7,
    old_type="lunchmoney",
):
    """
        This iterates through each transaction in the new_df and looks for
        potential matches in old_df.
        The initial test is to find transactions with the same amount and a date
        in a range of lookahead_days later or lookback_days earlier than the source
        The list of potential matches is then filtered to find matching account names,
        or account names in a list of synonyms defined in account_name_map.py
        If more than one potential match is found, the user is prompted in the terminal
        to select one.
        Once a single match is found, the update_fn is called which may write
        additional information into the new and old dataframes.
        If no potential match is found the word "Investigate" is written into the
        "action" colum for the row being examined.

        Required Parameters:
        new_df - a dataframe of LuncMoney transactions returned via the API
        old_df - a dataframe of LunchMoney or Mint exported transactions
        update_fn - a function that is called when a potential duplicate transaction
        is found.  This function is passed, the new and old dataframes, the indices
        to the rows of the potential matches, the transaction id of the row being
        evaluated, and the transation ID of the duplicate in old_df, or if old_df
        is mint data, the index of the matching row

        The updated new_df and old_df are returned, afer all rows in new_df have
        been examined
    """
    old_df_copy = old_df.copy()
    # Set the column names to check depending on if the old_df came from
    # lunchmoney or mint
    if old_type == "lunchmoney":
        old_date_field = "date"
        old_amount_field = "amount"
        old_description_field = "payee"
        old_account_field = "account_display_name"
    elif old_type == "mint":
        old_date_field = "Date"
        old_amount_field = "Amount"
        old_description_field = "Description"
        old_account_field = "Account Name"
    else:
        raise ValueError('old_type must be "lunchmoney" or "mint')

    # Iterate through each row in new_df to try to find a matching transaction in old_df
    # If found update the transaction info in both dataframes
    for index, row in new_df.iterrows():
        # Skip the row if a duplicate was already found
        if "action" in row and (row.action == "Delete" or row.action == "Duplicate"):
            continue
        # Find matches where the date in old_csv is within 7 days and amt matches
        if old_type == "lunchmoney":
            amount = row["amount"]
        else:
            amount = abs(row["amount"])
        matches = old_df_copy[
            (
                old_df_copy[old_date_field]
                <= row.date + pd.Timedelta(days=lookahead_days)
            )
            & (
                old_df_copy[old_date_field]
                >= row.date - pd.Timedelta(days=lookback_days)
            )
            & (old_df_copy[old_amount_field] == amount)
        ]
        if old_type == "mint":
            if row["amount"] > 0:
                matches = matches[matches["Transaction Type"] == "debit"]
            else:
                matches = matches[matches["Transaction Type"] == "credit"]

        if len(matches) > 0:
            # Filter matches on account name and possible synonyms
            matches = filter_matches_by_account(
                matches, row.account_display_name, old_account_field, acct_name_df
            )
            if len(matches) == 1:
                # Single match found, update the new and old dataframes
                update_fn(
                    new_df,
                    index,
                    old_df,
                    matches.index[0],
                )
            elif len(matches) > 1:
                # interactively check with the user
                new_date = row.date.strftime("%Y-%m-%d")
                print(
                    f"Found {len(matches)} candidates to match {new_date}: "
                    f"{row.amount} to {row.payee} from {row.account_display_name}:"
                )
                matches = matches.copy()
                # matches[old_date_field] = matches[old_date_field].dt.strftime(
                #     "%Y-%m-%d"
                # )
                need_user_input = True
                if old_type == "mint":
                    matches["source"] = "mint"
                print(
                    matches[
                        [
                            old_date_field,
                            old_amount_field,
                            old_description_field,
                            old_account_field,
                            "source",
                        ]
                    ].to_string(index=True)
                )
                while need_user_input:
                    last_ind = len(matches) - 1
                    user_response = input(
                        f"Please type in the index of the definition to use. "
                        f"'n' for none ({matches.index[last_ind]} default): "
                    )
                    try:
                        # If we got a numeric input update the action and related_id
                        if user_response == "":
                            old_index = matches.index[last_ind]
                        else:
                            old_index = int(user_response)
                        update_fn(
                            new_df,
                            index,
                            old_df,
                            old_index,
                            )
                        old_df_copy.drop(old_index, inplace=True)
                        need_user_input = False
                    except ValueError:
                        print("Will treat this as a transaction missing from Mint")
                        new_df.at[index, "action"] = "Investigate"
                        need_user_input = False
        if len(matches) <= 0:
            new_df.at[index, "action"] = "Investigate"

    return (new_df, old_df)
