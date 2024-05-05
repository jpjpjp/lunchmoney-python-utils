""" update_local_transactions.py

    This file updates (or creates) a local csv file of transaction data based
    on transactions fetched from the lunchmoney API

    If a local transaction file already exists it determines the date of the
    most recent transaction and then fetches all transactions newer than that
    as well as a configurable amount of older transactions that may have been
    updated since the last data pull

    The new transactions that were fetched from LunchMoney are then analyzed
    for duplicates amongst themselves.   If duplicates are found they are
    tagged in LunchMoney and the user is instructed to go there to clean up.
    Likewise, if unreviewed transactions are found, the user is asked to process
    those transactions prior to running this script.

    Otherwise, the newly imported transactions are combined with any existing local
    transactions.   Newly feteched transactions that exist in the local file are
    ignored unless the category, payee, notes or tags fields are different in which
    case the user is interactively asked how to handle the descrepency.

    In cases where the user prefers the local copy,
    the transaction in Lunch Money is updated.

    The updated local transaction list is written to a temporary file so as
    to preserve the last known good working local transaction list.
"""

# Import necessary modules
# import shutil
import pandas as pd
import sys
import os
from datetime import datetime


# Import configuration file and shared methods
import config.lunchmoney_config as lmc
from lib.transactions import (
    read_or_fetch_lm_transactions,
    lunchmoney_update_transaction,
)
from lib.local_transaction_utils import (
    output_new_transaction_data,
    read_local_transaction_csv,
    write_dated_df_to_csv,
)
from lib.find_and_process_dups import find_duplicate_transactions


def main():
    # Read in the local transaction data file
    local_df = read_local_transaction_csv(
        lmc.PATH_TO_LOCAL_TRANSACTIONS, index_on_date=False
    )
    # Fetch the new(ish) transactions from LunchMoney and exit if any need review
    new_df = get_new_lunchmoney_transactions(local_df, lmc.LOOKBACK_TRANSACTION_DAYS)

    # Validate that the new transaction data is good to go...
    exit_if_transactions_not_ready(new_df)
    exit_if_duplicates_found(new_df)

    # Add the new transactions without duplicates to the local file
    if local_df is not None:
        # Find potential overlap in the two dbs and resolve any discrepencies
        overlap_df = find_overlap_transactions(new_df, local_df)
        # Merge any new non overlapping transactions with the existing backup
        new_df = new_df[~new_df.index.isin(overlap_df.index)]
        if len(new_df):
            local_df = pd.concat([local_df, new_df])
            # Update the local transaction data backup
            output_new_transaction_data(
                local_df, lmc.PATH_TO_LOCAL_TRANSACTIONS, verbose=True
            )
        else:
            print('No new transactions found since last update.')
    else:
        # Ouptut the primary user's transaction file.
        write_dated_df_to_csv(new_df, lmc.PATH_TO_LOCAL_TRANSACTIONS)


def exit_if_duplicates_found(df):
    # Check if there are duplicates within the processed data
    if hasattr(lmc, "LOOKBACK_LM_DUP_DAYS"):
        print("Analyzing the imported transactions for duplicates...")
        dup_ids = find_duplicate_transactions(
            df, lookback_days=lmc.LOOKBACK_LM_DUP_DAYS
        )
    if len(dup_ids):
        # We found duplicates, write them to a CSV file to be examined
        dup_df = df[df["id"].isin(dup_ids)]
        today_date_str = datetime.now().strftime("%Y-%m-%d")
        output_file_path = os.path.join(
            "output", f"marked_as_duplicate_{today_date_str}.csv"
        )
        dup_df.to_csv(output_file_path, index=False)
        print(f"Found {len(dup_df)} duplicates. Details written to: {output_file_path}")
        # TODO provide a link that will show all files tagged with 'Duplicate' that
        # a user could click on.  This requires figuring out what the category_id is
        # for duplicate which will be unique for each lunchmoney user


def get_new_lunchmoney_transactions(existing_df, lookback_days):
    """
    Fetches all transactions from LunchMoney newer or lookback_days older
    than the transactions in existing_df

    If there are no existing transactions it pulls all the transaction data from
    LunchMoney
    """
    if existing_df is None:
        print(
            "No local transaction data found.  Will pull all transactions from "
            "Lunchmoney to create a new local transactions file"
        )
        start_date = pd.Timestamp("2000-01-01")
        end_date = (
            pd.Timestamp.today().normalize()
        )  # Set the end date to today, normalized to midnight
    else:
        # Calculate the start date as 7 days before the most recent transaction date
        most_recent_date = existing_df["date"].max()
        start_date = most_recent_date - pd.Timedelta(days=lookback_days)
        end_date = (
            pd.Timestamp.today().normalize()
        )  # Set the end date to today, normalized to midnight

    # Fetch transactions from LunchMoney for the specified date range
    new_transactions_df = read_or_fetch_lm_transactions(
        start_date, end_date, remove_pending=True, remove_split_parents=True
    )
    print(f"Fetched {len(new_transactions_df)} new transactions from LunchMoney.")

    return new_transactions_df


def exit_if_transactions_not_ready(df):
    """Exits if there are any transactions that still need to be reviewed"""
    unreviewed = df[df.status == "uncleared"]
    if len(unreviewed) > 0:
        print(f"There are {len(unreviewed)} transactions that need to be reviewed.")
        print(
            "Please visit\n"
            "https://my.lunchmoney.app/transactions?"
            "year=2024&month=02&match=all&status=unreviewed&time=all\n"
            "to classify them, and then rerun this script."
        )
        sys.exit(1)
    uncategorized = df["category_id"].isna().sum()
    if uncategorized:
        print(f"There are {uncategorized} transactions that need to be reviewed.")
        print(
            "Please visit\n"
            "https://my.lunchmoney.app/transactions/2024/02?"
            "match=all&time=all&uncategorized=true\n"
            "to classify them, and then rerun this script."
        )
        sys.exit(1)


def find_overlap_transactions(new_df, local_df):
    """
    Find any transactions that exist both in the local and newly
    fetched data.
    For those that have differences in the user updatable fields,
    ask the user to identify which one is correct
    """
    # Define the fields to compare
    fields_to_compare = [
        "date",
        "amount",
        "payee",
        "category_name",
        "account_display_name",
        "notes",
        "tags",
    ]

    # Find instances of the same transaction in the imported and existing local data
    overlap_df = new_df[new_df["id"].isin(local_df["id"])]

    # Iterate through each transaction in overlap_df
    for _, row in overlap_df.iterrows():
        # Get the corresponding transaction in local_df
        corresponding_transaction = local_df[local_df["id"] == row["id"]]

        # Check if there is a corresponding transaction
        if not corresponding_transaction.empty:
            # Compare the specified fields
            differences = []
            for field in fields_to_compare:
                if row[field] != corresponding_transaction[field].values[0]:
                    differences.append(field)

            # If there are differences, print both transactions for the differing fields
            if differences:
                print(
                    f"\nFound differences in {differences} fields between "
                    "new and local transactions."
                )
                print(f"Newly imported Transaction:\n{format_transaction(row)}")
                print(
                    "Existing local Transactions:\n"
                    f"{format_transaction(corresponding_transaction.iloc[0])}"
                )
                print("\n")  # Add a newline for better readability
                response = ""
                while response.lower() != "n" and response.lower() != "e":
                    response = input("Which one is right (n/e): ")
                if response == "n":
                    existing_index = corresponding_transaction.index[0]
                    for field in differences:
                        local_df.at[existing_index, field] = row[field]
                else:
                    # update the lunchmoney transaction with the new values
                    lunchmoney_update_transaction(
                        row["id"],
                        {
                            field: corresponding_transaction[field].values[0]
                            for field in differences
                        },
                    )

        else:
            print("WARNING: Did not find existing transaction to match new trans:")
            print(row[fields_to_compare])

        return overlap_df


def format_transaction(transaction):
    """
    Format a transaction series into a string with specific fields formatted.
    - Date is converted to 'YYYY-MM-DD'.
    - Tags are converted from a list of objects to a comma-separated string of names.
    """
    # Extract and format the date
    formatted_date = transaction["date"].strftime("%Y-%m-%d")

    # Extract and format the tags
    if transaction["tags"] and isinstance(transaction["tags"], list):
        formatted_tags = ", ".join(
            tag["name"] for tag in transaction["tags"] if "name" in tag
        )
    else:
        formatted_tags = ""

    # Create the formatted string
    formatted_transaction = (
        f"Date: {formatted_date}, "
        f"Amount: {transaction['amount']}, "
        f"Payee: {transaction['payee']}, "
        f"Category Name: {transaction['category_name']}, "
        f"Account Display Name: {transaction['account_display_name']}, "
        f"Notes: {transaction['notes']}, "
        f"Tags: {formatted_tags}"
    )

    return formatted_transaction


main()

