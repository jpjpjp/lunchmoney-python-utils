import os
import pandas as pd
from datetime import datetime, timedelta
import sys
from lib.transactions import (
    read_or_fetch_lm_transactions,
    lunchmoney_update_transaction,
    get_category_id_by_name,
)
from lib.find_duplicates import find_duplicates
from config.lunchmoney_config import (
    MINT_CSV_FILE,
    MINT_DATE_FORMAT,
    INPUT_FILES,
    OUTPUT_FILES,
    LOOKBACK_TRANSACTION_DAYS,
    LM_FETCHED_TRANSACTIONS_CACHE,
)


def main():
    """
    Fetches all transactions from lunchmoney that are newer than
    LOOKBACK_TRANSACTION_DAYS from the most recent transaction in MINT_CSV_FILE

    If there are transactions that have not yet been classified in LunchMoney, exit
    and tell user to finish classifying.

    Once all are classified, remove duplicates that
    are already in MINT_CSV_FILE, and then add the remaining transactions
    to MINT_CSV_FILE in OUPUT_FILES
    """
    existing_df = get_existing_transactions(
        INPUT_FILES, MINT_CSV_FILE, MINT_DATE_FORMAT
    )
    new_transactions_df = get_new_lunchmoney_transactions(
        existing_df, LOOKBACK_TRANSACTION_DAYS
    )

    # Exit if there are any transactions that still need to be cleared or categorized
    exit_if_transactions_not_ready(new_transactions_df)

    # Remove or update any duplicate transactions
    to_add_df, existing_df = find_duplicates(
        new_transactions_df.copy(),
        existing_df,
        process_duplicate,  # defined below
        lookahead_days=0,
        lookback_days=0,
        old_type="mint",
    )

    print(f"Found {len(new_transactions_df) - len(to_add_df)} duplicates")
    # Merge the new transactions with the existing ones and output the file
    merge_and_output(existing_df, to_add_df, OUTPUT_FILES, MINT_CSV_FILE)


def process_duplicate(new_df, new_index, existing_df, existing_index):
    """This function is called by the find_duplicates function after it
    has identified a lunchmoney transaction with a counterpart in the mint data.

    We check additional fields to see if they match.  If so the duplicate transaction
    is removed from the set to be added to the mint transactions file.

    If differences are detected we check with the user which one is correct and update
    the legacy transactions either in Lunchmoney or in the mint transactions file.
    """

    # Date, account, and amount match.
    # Let's check if payee, category, tags and notes do also
    new_values = new_df.loc[new_index, ["payee", "category_name", "notes"]].tolist()
    new_values.append(
        f'{" ".join([tag["name"] for tag in new_df.loc[new_index, "tags"]])}'
    )
    existing_values = existing_df.loc[
        existing_index, ["Description", "Category", "Notes", "Labels"]
    ].tolist()

    # Replace NaN, None, and empty lists with an empty string
    new_values = normalize_empty_values(new_values)
    existing_values = normalize_empty_values(existing_values)

    # Check if the values are the same
    if new_values == existing_values:
        print("Ignoring Existing Transaction:")
        print(
            f'{new_df.loc[new_index, "date"]}: '
            f'{new_df.loc[new_index, "category_name"]}, '
            f'{new_df.loc[new_index, "payee"]}, '
            f'{new_df.loc[new_index, "amount"]}, '
            f'{new_df.loc[new_index, "notes"]}, '
            f"{new_values[-1]}"
        )
    else:
        print("Existing Transaction has been updated since last import:")
        print(
            f'Old: {existing_df.loc[existing_index, "Date"]}: '
            f'{existing_df.loc[existing_index, "Category"]}, '
            f'{existing_df.loc[existing_index, "Description"]}, '
            f'{existing_df.loc[existing_index, "Amount"]}, '
            f'{existing_df.loc[existing_index, "Notes"]}, '
            f'{existing_df.loc[existing_index, "Labels"]}'
        )
        print(
            f'New: {new_df.loc[new_index, "date"]}: '
            f'{new_df.loc[new_index, "category_name"]}, '
            f'{new_df.loc[new_index, "payee"]}, '
            f'{new_df.loc[new_index, "amount"]}, '
            f'{new_df.loc[new_index, "notes"]}, '
            f"{new_values[-1]}"
        )
        response = ""
        while response.lower() != "n" and response.lower() != "o":
            response = input("Which one is right (o/n): ")
        if response == "n":
            # update the existing data with new values
            existing_df.at[existing_index, "Description"] = new_values[0]
            existing_df.at[existing_index, "Category"] = new_values[1]
            existing_df.at[existing_index, "Notes"] = new_values[2]
            existing_df.at[existing_index, "Labels"] = new_values[3]
        else:
            # update the lunchmoney transaction with the new values
            lunchmoney_update_transaction(
                new_df.loc[new_index, "id"],
                {
                    "payee": existing_values[0],
                    "category_id": get_category_id_by_name(existing_values[1]),
                    "notes": existing_values[2],
                    "tags": existing_values[3].split(" "),
                },
            )

    # Drop the duplicate from the dataframe of new transactions
    new_df.drop(new_index, inplace=True)


def normalize_empty_values(values_list):
    # Replace NaN, None, and empty lists with an empty string
    empty = ""
    return [
        (
            empty
            if (isinstance(value, list) and len(value) == 0)
            or pd.isna(value)
            or value is None
            else value
        )
        for value in values_list
    ]


def get_existing_transactions(input_path, input_file, date_format):
    """
    Reads the data from MINT_CSV_FILE and returns the dataframe.
    """
    mint_csv_path = os.path.join(input_path, input_file)
    # mint_df = pd.read_csv(mint_csv_path, parse_dates=["Date"], date_format=date_format)
    mint_df = pd.read_csv(mint_csv_path, parse_dates=["Date"])
    mint_df["Date"] = mint_df["Date"].dt.date
    return mint_df


def validate_splits(df):
    parents = df[df["has_children"]]
    for parent_id in parents["id"]:
        if parent_id not in df["parent_id"].values:
            print(f"Parent id {parent_id} does not exist in the dataframe.")
            sys.exit(1)
    print(f"Removing {len(parents)} transactions that were split")
    return df[~df["has_children"]]


def get_new_lunchmoney_transactions(existing_df, lookback_days):
    """
    Fetches new transactions from LunchMoney for the specified date range.
    """
    # Calculate the start date as 7 days before the most recent transaction date
    most_recent_date = existing_df["Date"].max()
    start_date = most_recent_date - timedelta(days=lookback_days)
    end_date = datetime.now().date()  # Set the end date to today

    # Initialize the LunchMoney client

    # Fetch transactions from LunchMoney for the specified date range
    # new_transactions_df = lunchmoney_transactions_to_df(start_date, end_date)
    new_transactions_df = read_or_fetch_lm_transactions(
        start_date, end_date, LM_FETCHED_TRANSACTIONS_CACHE
    )
    print(f"Fetched {len(new_transactions_df)} new transactions from LunchMoney.")

    # remove any pending transactions
    not_pending_df = new_transactions_df[~new_transactions_df.is_pending]
    num_pending = len(new_transactions_df) - len(not_pending_df)
    print(f"Removing {num_pending} new transactions that are pending.")

    # remove any parents of split transactions
    not_pending_df = validate_splits(not_pending_df)

    return not_pending_df


def exit_if_transactions_not_ready(df):
    """Exits if there are any transactions that still need to be cleared or categorized"""
    unreviewed = df[df.status == "uncleared"]
    if len(unreviewed) > 0:
        print(f"There are {len(unreviewed)} transactions that need to be reviewed.")
        print(
            "Please visit\n"
            "https://my.lunchmoney.app/transactions/2024/02?match=all&status=unreviewed&time=all\n"
            "to classify them, and then rerun this script."
        )
        sys.exit(1)
    uncategorized = df["category_id"].isna().sum()
    if uncategorized:
        print(f"There are {uncategorized} transactions that need to be reviewed.")
        print(
            "Please visit\n"
            "https://my.lunchmoney.app/transactions/2024/02?match=all&time=all&uncategorized=true\n"
            "to classify them, and then rerun this script."
        )
        sys.exit(1)


def merge_and_output(existing_df, to_add_df, output_path, output_file):
    if len(to_add_df) == 0:
        print("No new transactions to add.")
        return
    print(f"Will add {len(to_add_df)} new transactions to {output_path}/{output_file}")
    # Convert the lunchmoney transactions to mint format
    to_add_mint_format = to_add_df[
        [
            "date",
            "payee",
            "amount",
            "category_name",
            "account_display_name",
            "tags",
            "notes",
        ]
    ].rename(
        columns={
            "date": "Date",
            "payee": "Description",
            "amount": "Amount",
            "category_name": "Category",
            "account_display_name": "Account Name",
            "tags": "Labels",
            "notes": "Notes",
        }
    )
    to_add_mint_format.insert(2, "Original Description", "")
    to_add_mint_format.insert(
        4,
        "Transaction Type",
        to_add_mint_format["Amount"].apply(lambda x: "debit" if x > 0 else "credit"),
    )
    to_add_mint_format["Amount"] = to_add_mint_format["Amount"].abs()
    to_add_mint_format["Labels"] = to_add_mint_format["Labels"].apply(
        lambda x: " ".join([tag["name"] for tag in x]) if x else ""
    )

    # Merge the dbs and write out the new total transactions file
    new_total_df = pd.concat([existing_df, to_add_mint_format])
    new_total_df = new_total_df.sort_values(by="Date", ascending=False)
    new_total_df.to_csv(
        os.path.join(output_path, output_file),
        index=False,
        date_format=MINT_DATE_FORMAT,
    )


if __name__ == "__main__":
    main()
