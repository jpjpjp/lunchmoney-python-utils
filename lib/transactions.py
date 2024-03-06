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
from config import lunchmoney_config as lmc

sys.path.append("..")

private_lunch = None
categories = None


def init_lunchable(token):
    global private_lunch
    if private_lunch is None:
        private_lunch = LunchMoney(access_token=token)
    return private_lunch


def lunchmoney_transactions_to_df(start_date, end_date, lunch=None):
    """Returns a dataframe with the transactions obtained via the
    lunchable.get_transactions API for the specified data range
    """
    if lunch is None:
        lunch = init_lunchable(lmc.LUNCHMONEY_API_TOKEN)

    # Fetch transactions from the last three months
    transactions = lunch.get_transactions(start_date, end_date)

    # Convert transactions to dictionaries and then to a DataFrame
    transactions_data = [transaction.model_dump() for transaction in transactions]
    return pd.DataFrame(transactions_data)


def lunchmoney_update_transaction(id, transaction_fields, lunch=None):
    """ Updated the transaction with id, to have whatever new values are
        in set in the transaction_fields object
    """
    if lunch is None:
        lunch = init_lunchable(lmc.LUNCHMONEY_API_TOKEN)
    update_object = TransactionUpdateObject(**transaction_fields)
    return lunch.update_transaction(id, update_object)


def read_or_fetch_lm_transactions(start_date, end_date, csv_file_base, lunch=None):
    """Returns a dataframe of transactions from lunchmoney

    If the file csv_file_base-start_date-end_date.csv exists they
    are read from there, otherwise the are pulled via the lunchmoney
    GET /transactions API.

    For the API to work the environment variable LUNCHMONEY_API_TOKEN must
    be set to a token aquired from https://my.lunchmoney.app/developers
    """
    csv_file = os.path.join(
        lmc.INPUT_FILES,
        f"{csv_file_base}-{start_date.strftime('%Y_%m_%d')}-{end_date.strftime('%Y_%m_%d')}.csv",
    )
    if os.path.isfile(csv_file):
        # We have a cached version of the same transaction request written as a CSV
        # Read it in from the CSV converting the tags field to an array of objects and
        # the date field to a datatime object, just as they'd be returned by the API
        converters = {'tags': lambda val: ast.literal_eval(val) if isinstance(val, str) else val}
        df = pd.read_csv(csv_file, parse_dates=["date"], date_format="%Y-%m-%d", converters=converters)
        df["date"] = pd.to_datetime(df["date"])
        print(f"Read {len(df)} transactions from {csv_file}.")
        print("Just delete this file if you want to re-fetch them again in the future.")
    else:
        print("Attempting to fetch your lunch money transactions via the API...")
        df = lunchmoney_transactions_to_df(start_date, end_date, lunch)
        df["date"] = pd.to_datetime(df["date"])
        print(f"Got all {len(df)} of them.")
        print(f"Will write them to {csv_file} for faster future access.")
        print("Just delete this file if you want to re-fetch them again in the future.")
        df.to_csv(csv_file, index=False)

    return df
