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
    CACHE_DIR,
    LM_FETCHED_TRANSACTIONS_CACHE,
)

sys.path.append("..")

private_lunch = None


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
    transactions = lunch.get_transactions(start_date.date(), end_date.date())

    # Convert transactions to dictionaries and then to a DataFrame
    transactions_data = [transaction.model_dump() for transaction in transactions]
    return ensure_consistent_types(pd.DataFrame(transactions_data), source="api")


# Custom function to coerce Lunch Money IDs to strings or None
def id_to_str_or_none(x):
    if pd.isna(x):
        return None
    else:
        return str(int(x)) if x.is_integer() else str(x)


# Custom function to coerce excel True/False strings to bool
def str_to_bool(x):
    if x == "True" or x == "TRUE" or x == "true":
        return True
    else:
        return False


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
        CACHE_DIR,
        (
            f"{LM_FETCHED_TRANSACTIONS_CACHE}-"
            f"{start_date.strftime('%Y_%m_%d')}-"
            f"{end_date.strftime('%Y_%m_%d')}.csv"
        ),
    )
    if os.path.isfile(csv_file):
        # We have a cached version of the same transaction request written as a CSV
        # Read it in from the CSV normalizing the data as if it had come from the API
        df = read_lm_transactions_csv(csv_file)
        print(f"Read {len(df)} transactions from {csv_file}.")
        print("Just delete this file if you want to re-fetch them again in the future.")

    else:

        print("Attempting to fetch your lunch money transactions via the API...")
        df = lunchmoney_transactions_to_df(start_date, end_date, lunch)
        print(f"Got all {len(df)} of them.")
        print(f"Will write them to {csv_file} for faster future access.")
        print("Just delete this file if you want to re-fetch them again in the future.")

        try:
            df.to_csv(csv_file, index=False)
        except Exception as e:
            print(f"Failed to write to {csv_file}. Reason: {e}")
            print(
                "Consider modifying CACHE_DIR and/or LM_FETCHED_TRANSACTIONS_CACHE "
                "in the config file."
            )

    if remove_pending:
        df = remove_pending_transactions(df)
    if remove_split_parents:
        df = remove_parents_of_split_transactions(df)

    return df


def ensure_consistent_types(df, source):
    """There are some subtle differences in the types in the dataframes created from an
    API call vs. reading a CSV of lunchmoney transaction data. Ensure consistent
    behavior by typing objects using the rules below
    """
    if source != "api" and source != "csv":
        print(
            "Warning, don't know if transaction data came from API or CSV so "
            "cannot normalize it."
        )
        return df
    if source == "csv":
        # Values read directly from the API treat empty as None, match it for CSV files
        df = df.where(pd.notnull(df), None)  # df.fillna("", inplace=True)
        # All Dates are pandas timestamp objects:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        df["update_at"] = pd.to_datetime(df["updated_at"], errors="coerce")
        # Convert amounts to floats:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df["to_base"] = pd.to_numeric(df["to_base"], errors="coerce")
        # Convert True/False strings to Boolean
        df["is_pending"] = df["is_pending"].apply(str_to_bool)
        df["is_income"] = df["is_income"].apply(str_to_bool)
        df["exclude_from_budget"] = df["exclude_from_budget"].apply(str_to_bool)
        df["exclude_from_totals"] = df["exclude_from_totals"].apply(str_to_bool)
        df["has_children"] = df["has_children"].apply(str_to_bool)
        df["is_group"] = df["is_group"].apply(str_to_bool)
        # Restore the Objects:
        df["tags"] = df["tags"].apply(
            lambda val: ast.literal_eval(val) if isinstance(val, str) else val
        )
        df["plaid_metadata"] = df["plaid_metadata"].apply(
            lambda val: (
                ast.literal_eval(val)
                if isinstance(val, str) and val.startswith(("{", "["))
                else {}
            )
        )
    else:
        # ID fields from lunchable API are inconsistently treated as numeric
        # We never do math on them, so treat them as strings
        df["id"] = df["id"].apply(id_to_str_or_none)
        df["recurring_id"] = df["recurring_id"].apply(id_to_str_or_none)
        df["category_id"] = df["category_id"].apply(id_to_str_or_none)
        df["parent_id"] = df["parent_id"].apply(id_to_str_or_none)
        df["plaid_account_id"] = df["plaid_account_id"].apply(id_to_str_or_none)
        # Massage out any newlines or leading/trailing spaces in any of the fields
        df = df.applymap(clean_up_white_space_from_api)
        # Since data has no timestamp info it became a python datetime.date object
        # Convert it to a pandas timestamp so we can be consistent in how we
        # operate on all date/time like objects
        df["date"] = pd.to_datetime(df["date"])

    # Boolean columns

    return df


def clean_up_white_space_from_api(x):
    """Removes embedded new lines, leading/trailing white space from strings"""
    if not isinstance(x, str):
        return x
    else:
        return x.replace("\n", " ").strip()


def read_lm_transactions_csv(path_to_data):
    try:
        # TODO Delete this comment once I'm confident ensure_consistent_types works
        # Instead of using converters we'll converting everything to
        # objects so the types more closely align what we get when we
        # read the transactions from the API
        # converters = {
        #     # "id": string_converter,
        #     "amount": float_converter,
        #     "to_base": float_converter,
        #     "recurring_amount": float_converter,
        #     "date": date_converter,
        #     "created_at": date_time_converter,
        #     "updated_at": date_time_converter,
        #     # "category_id": string_converter,
        #     # "category_name": string_converter,
        #     # "category_group_id": string_converter,
        #     # "category_group_name": string_converter,
        #     # "notes": string_converter,
        #     # "recurring_id": string_converter,
        #     # "recurring_payee": string_converter,
        #     # "recurring_description": string_converter,
        #     # "recurring_cadence": string_converter,
        #     # "recurring_type": string_converter,
        #     # "recurring_currency": string_converter,
        #     # "parent_id": string_converter,
        #     # "group_id": string_converter,
        #     # "asset_id": string_converter,
        #     # "asset_institution_name": string_converter,
        #     # "asset_name": string_converter,
        #     # "asset_display_name": string_converter,
        #     # "asset_status": string_converter,
        #     # "plaid_account_id": string_converter,
        #     # "plaid_account_name": string_converter,
        #     # "plaid_account_mask": string_converter,
        #     # "institution_name": string_converter,
        #     # "plaid_account_display_name": string_converter,
        #     # "display_notes": string_converter,
        #     # "external_id": string_converter,
        #     # "asset_institution_name": string_converter,
        #     # TODO children
        #     # Strip unecessary spaces that sneak into account names
        #     "account_display_name": lambda x: x.strip() if isinstance(x, str) else x,
        #     # "is_income": bool_converter,
        #     # "exclude_from_budget": bool_converter,
        #     # "exclude_from_totals": bool_converter,
        #     # "is_pending": bool_converter,
        #     # "has_children": bool_converter,
        #     # "is_group": bool_converter,
        #     "tags": lambda val: ast.literal_eval(val) if isinstance(val, str) else val,
        #     "plaid_metadata": lambda val: (
        #         ast.literal_eval(val)
        #         if isinstance(val, str) and val.startswith(("{", "["))
        #         else {}
        #     ),
        # }
        #        df = pd.read_csv(path_to_data, converters=converters)
        #        df = pd.read_csv(path_to_data, converters=converters, dtype=object, keep_default_na=True, na_values=[''])
        df = pd.read_csv(
            path_to_data, dtype=object, keep_default_na=True, na_values=[""]
        )
        df = ensure_consistent_types(df, source="csv")

    except BaseException as e:
        # TODO - print a warning and return an empty df?
        # Maybe add a parameter for this
        print(
            "Failed to read existing local transaction data file "
            f"'{path_to_data}': {e}"
        )
        print(
            "Either fix the local file or delete it "
            "to pull everything fresh from LunchMoney"
        )
        sys.exit(-1)

    return df


def remove_parents_of_split_transactions(df):
    """remove any parents of split transactions"""
    parents = df[df["has_children"]]
    for parent_id in parents["id"]:
        if parent_id not in df["parent_id"].values:
            print(f"Parent id {parent_id} does not exist in the dataframe.")
            sys.exit(1)
    print(f"Removing {len(parents)} parents of transactions that were split")
    return df[~df["has_children"]]


def remove_pending_transactions(df):
    """remove any pending transactions"""
    all_trans = len(df)
    df = df[~df["is_pending"]]
    num_pending = all_trans - len(df)
    print(f"Removing {num_pending} new transactions that are pending.")
    return df


def lunchmoney_delete_transaction(id, existing_tag_names):
    """Ideally this would removes the transactions with the id passed in
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
