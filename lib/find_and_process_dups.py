""" find_and_process_dups.py

    This file provides the functions used to check a set of lunchmoney transactions
    for potential duplicates.   When candidates are found they are presented 
    interactively to the user
"""
import pandas as pd
from lib.transactions import (
    lunchmoney_update_transaction,
    lunchmoney_delete_transaction,
)


def find_duplicate_transactions(
    df,
    lookback_days=0,
):
    """Accepts a dataframe of lunchmoney transactions as input.

    Breaks the dataframe of transactions into sets of transactions for the same
    account.  Then pass that dataframe into a function to find duplicates

    This approach makes it easier to pull up the financial institutions website
    to validate suspected duplicate transactions
    """
    ids_to_delete = []
    # To facilitate checking break the df into chunks based on account name
    for account_name in df["account_display_name"].unique():
        # Sort all the rows for each account by date, and make a copy to check for dups
        df_to_search = df[df["account_display_name"] == account_name].sort_values(
            by="date", ascending=False
        )
        ids_to_delete = find_duplicates_for_one_account(
            df_to_search, lookback_days, ids_to_delete
        )

    return ids_to_delete


def find_duplicates_for_one_account(df, lookback_days, ids_to_delete):
    """Look for duplicates in a dataframe of transactions
    If found ask user to disambiguate, tagging non-duplicates, and
    deleting duplicates

    Note that it is assumed that all transactions are for the same account
    """  # Validate: len(df_to_search["account_display_name"].unique())
    deleted_indices = []
    df_copy = df.copy()
    for index, row in df.iterrows():
        # Skip analysis if the row was already declared a duplciate
        if index in deleted_indices:
            continue
        df_copy.drop(index, inplace=True)
        # Find transactions with the same amount in the same date window
        matches = df_copy[
            (df_copy["amount"] == row["amount"])
            # We assume that the data passed into this function is for a single acct
            # & (df_copy["account_display_name"] == row["account_display_name"])
            & (df_copy["date"] >= row.date - pd.Timedelta(days=lookback_days))
        ]

        # Drop matches that have already been marked Not-Duplicate
        if len(matches) > 0:
            not_duplicate_tags = {"Not-Duplicate", "SkipDupCheck"}
            if any(tag["name"] in not_duplicate_tags for tag in row["tags"]):
                matches = matches[
                    ~matches["tags"].apply(
                        lambda tags: any(
                            tag["name"] in not_duplicate_tags for tag in tags
                        )
                    )
                ]
                if len(matches) <= 0:
                    continue

            # Combine row and matches to interactively check with the user
            new_row = row.to_frame().T
            matches = pd.concat([new_row, matches])

            # Convert datetimes to printable date format
            matches["date"] = matches["date"].apply(lambda x: x.strftime("%Y-%m-%d"))
            # Convert list of tag objects to a string of comma seperated tag names
            matches["tags"] = matches["tags"].apply(
                lambda tags: ",".join([tag["name"] for tag in tags])
            )
            print("\nPotential duplicate transactions:")
            while len(matches) > 1:
                print(
                    matches[
                        [
                            "date",
                            "category_name",
                            "payee",
                            "amount",
                            "account_display_name",
                            "notes",
                            "tags",
                        ]
                    ].to_string(index=True)
                )
                need_user_input = True
                while need_user_input:
                    user_response = input(
                        "Please enter the index of any duplicate or hit enter if "
                        "there are no duplicates: "
                    )
                    try:
                        # If we got a numeric input delete the duplicate transaction
                        dup_index = int(user_response)
                        if dup_index != index and dup_index not in matches.index:
                            print("Invalid entry try again.")
                            continue
                        print("Will delete this duplicate")
                        id_to_delete = matches.loc[dup_index, "id"]
                        ids_to_delete.append(id_to_delete)
                        lunchmoney_delete_transaction(
                            id_to_delete, matches.loc[dup_index, "tags"]
                        )
                        if dup_index != index:
                            # Don't analyze this transaction when iterrate to it
                            deleted_indices.append(dup_index)
                            df_copy.drop(dup_index, inplace=True)
                        matches.drop(dup_index, inplace=True)
                        need_user_input = False
                    except ValueError:
                        # Add "Not-Duplicate" tag to transactions
                        (df, df_copy) = interactive_tag_non_dup(matches, df, df_copy)
                        matches = pd.DataFrame()
                        need_user_input = False
    return ids_to_delete


def interactive_tag_non_dup(matches, loc_df1, loc_df2):
    """Tags each transaction as the dataframe with "Not-Duplicate
    Interactively offers opportunity to update Payee or Notes field
    Updates transaction date in Lunch Money via API
    Updates in mem copies of transactions for further processing
    """
    for index, match in matches.iterrows():
        update_obj = {}
        resp = input(
            f"Tagging {index} as non duplicate.  Update Payee or Notes? (p/n/enter for no): "
        )
        if resp.lower() == "p":
            resp2 = input("Enter new Payee text: ")
            update_obj["payee"] = resp2
        elif resp.lower() == "n":
            resp2 = input("Enter new Notes text: ")
            update_obj["notes"] = resp2
        if "Not-Duplicate" not in match["tags"]:
            if match["tags"]:
                updated_tags = match["tags"] + ",Not-Duplicate"
                update_obj["tags"] = (
                    updated_tags.split(",") if "," in updated_tags else updated_tags
                )
                if "SkipDupCheck" in update_obj["tags"]:
                    update_obj["tags"] = [
                        tag for tag in update_obj["tags"] if tag != "SkipDupCheck"
                    ]
            else:
                update_obj["tags"] = ["Not-Duplicate"]
        if update_obj:
            lunchmoney_update_transaction(
                match["id"],
                update_obj,
            )

        # Update local data stores so we don't do these again
        if index in loc_df1.index:
            loc_df1.loc[index, "tags"].append({"name": "SkipDupCheck"})
        if index in loc_df2.index:
            loc_df2.loc[index, "tags"].append({"name": "SkipDupCheck"})

    return (loc_df1, loc_df2)
