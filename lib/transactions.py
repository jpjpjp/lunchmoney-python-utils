"""transactions.py

   This module provides functions for managing lunchmoney transaction via the
   /transactions API accessed by the lunchable client

   For apps that manipulate only transactions, this module can completely encapsulate
   access to the lunchable client and only requires that the LunchMoney API token
   be set in lunchmoney_config.py.

   Apps that access multiple lunchmoney APIs can pass in a pre-intialized lunchable
   client for API access.
"""

import ast
import os
import pandas as pd
import sys
from lunchable import LunchMoney
from lunchable.models import TransactionUpdateObject
from config.lunchmoney_config import (
    LUNCHMONEY_API_TOKEN,
    PATH_TO_TRANSACTIONS_CACHE
)

sys.path.append("..")

private_lunch = None
categories = None


def init_lunchable(token=None):
    global private_lunch
    if private_lunch is None:
        if token is None:
            private_lunch = LunchMoney(access_token=LUNCHMONEY_API_TOKEN)
        else:
            private_lunch = LunchMoney(access_token=token)
    return private_lunch


def lunchmoney_transactions_to_df(start_date, end_date, lunch=None):
    """Returns a dataframe with the transactions obtained via the
    lunchable.get_transactions API for the specified data range
    """
    if lunch is None:
        lunch = init_lunchable()

    # Fetch transactions from the last three months
    transactions = lunch.get_transactions(start_date, end_date)

    # Convert transactions to dictionaries and then to a DataFrame
    transactions_data = [transaction.model_dump() for transaction in transactions]
    return pd.DataFrame(transactions_data)


def lunchmoney_update_transaction(id, transaction_fields, lunch=None):
    """Updated the transaction with id, to have whatever new values are
    in set in the transaction_fields object
    """
    if lunch is None:
        lunch = init_lunchable()
    update_object = TransactionUpdateObject(**transaction_fields)
    return lunch.update_transaction(id, update_object)


def read_or_fetch_lm_transactions(
    start_date,
    end_date,
    remove_pending=False,
    remove_split_parents=False,
    lunch=None,
):
    """Returns a dataframe of transactions from lunchmoney

    If the file csv_file_base-start_date-end_date.csv exists they
    are read from there, otherwise the are pulled via the lunchmoney
    GET /transactions API.

    For the API to work the environment variable LUNCHMONEY_API_TOKEN must
    be set to a token aquired from https://my.lunchmoney.app/developers
    """
    csv_file = os.path.join(
        f"{PATH_TO_TRANSACTIONS_CACHE}-{start_date.strftime('%Y_%m_%d')}-{end_date.strftime('%Y_%m_%d')}.csv",
    )
    if os.path.isfile(csv_file):
        # We have a cached version of the same transaction request written as a CSV
        # Read it in from the CSV converting the tags field to an array of objects and
        # the date field to a datatime object, just as they'd be returned by the API
        converters = {
            "tags": lambda val: ast.literal_eval(val) if isinstance(val, str) else val
        }
        df = pd.read_csv(
            csv_file,
            parse_dates=["date"],
            date_format="%Y-%m-%d",
            converters=converters,
        )
        print(f"Read {len(df)} transactions from {csv_file}.")
        print("Just delete this file if you want to re-fetch them again in the future.")
    else:
        print("Attempting to fetch your lunch money transactions via the API...")
        df = lunchmoney_transactions_to_df(start_date, end_date, lunch)
        print(f"Got all {len(df)} of them.")
        print(f"Will write them to {csv_file} for faster future access.")
        print("Just delete this file if you want to re-fetch them again in the future.")
        try:
            # Massage out any newlines in any of the fields
            df = df.map(lambda x: x.replace('\n', ' ') if isinstance(x, str) else x)
            df.to_csv(csv_file, index=False)
        except Exception as e:
            print(f"Failed to write to {csv_file}. Reason: {e}")
            print("Please consider changing the value of PATH_TO_TRANSACTIONS_CACHE in the config file.")

    # Ensure a workable datetime format, and clean up extra spaces LM puts in act names
    df["date"] = pd.to_datetime(df["date"])
    df["account_display_name"] = df["account_display_name"].str.strip()

    if remove_pending:
        df = remove_pending_transactions(df)
    if remove_split_parents:
        # remove any parents of split transactions
        df = remove_parents_of_split_transactions(df)

    return df


def remove_parents_of_split_transactions(df):
    """ remove any parents of split transactions """
    parents = df[df["has_children"]]
    for parent_id in parents["id"]:
        if parent_id not in df["parent_id"].values:
            print(f"Parent id {parent_id} does not exist in the dataframe.")
            sys.exit(1)
    print(f"Removing {len(parents)} parents of transactions that were split")
    return df[~df["has_children"]]


def remove_pending_transactions(df):
    """ remove any pending transactions """
    all_trans = len(df)
    df = df[~df.is_pending]
    num_pending = all_trans - len(df)
    print(f"Removing {num_pending} new transactions that are pending.")
    return df


def lunchmoney_delete_transaction(id, existing_tag_names):
    """ Ideally this would removes the transactions with the id passed in
        Since the LM API does not support the ability to delete transactions instead
        we'll add a Duplicate tag that the user can filter on for manual deletion
    """
    # TODO Change this to really delete it when API becomes available
    update_obj = {}
    if existing_tag_names:
        existing_tag_names += ",Duplicate"
        update_obj["tags"] = existing_tag_names.split(",")
    else:
        update_obj["tags"] = ["Duplicate"]

    lunchmoney_update_transaction(id, update_obj)
