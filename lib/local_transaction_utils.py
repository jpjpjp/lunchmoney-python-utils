""" local_transaction_utils

    A set of convenience functions for reading and writing local transaction
    files.
"""

import numpy as np
from datetime import datetime
import sys
import os
from config.lunchmoney_config import (
    CACHE_DIR,
    COLS_TO_VALIDATE,
    DATE,
)
from lib.transactions import read_lm_transactions_csv

sys.path.append("..")


def validate_transactions(df, required_columns):
    """Ensure that required columns all have data in them"""
    bad_col = None
    for column in required_columns:
        if column in df.index.names:
            if np.isnan(df.index.get_level_values(column)).any():
                bad_col = column
                break
        else:
            if df[column].isnull().values.any():
                bad_col = column
                break
    if bad_col is None:
        return True
    else:
        print(f"Column {bad_col} is missing data")
        return False


def output_new_transaction_data(
    df, outfile, prefix="", sort_by_date=True, verbose=False
):
    if prefix != "":
        outfile = f"{prefix}-{outfile}"
    if os.path.isfile(outfile):
        # Create a temp version of the transactions with today's data
        dir_name = os.path.dirname(outfile)
        file_name = (
            os.path.splitext(os.path.basename(outfile))[0]
            + f"-{datetime.today().date():%Y-%m-%d}.csv"
        )
        outfile = os.path.join(dir_name, file_name)

    write_dated_df_to_csv(df, outfile, sort_by_date=sort_by_date)
    if verbose:
        print(f"Wrote updated transactions data to {outfile}")


def write_dated_df_to_csv(df, outfile, date_col=DATE, sort_by_date=True, index=False):
    if sort_by_date:
        df = df.copy()
        df.sort_values(by=date_col, ascending=False, inplace=True)
    df.to_csv(outfile, index=index)


def get_latest_transaction_file(path_to_data, query_user=True):
    """Returns the filename with most recent local copy of transaction.
    If a temporory copy of this file that was generated today is detected
    the user is interactively queried to see if they prefer to use that one
    """
    file_name = (
        os.path.splitext(os.path.basename(path_to_data))[0]
        + f"-{datetime.today().date():%Y-%m-%d}.csv"
    )
    file_path = os.path.join(CACHE_DIR, file_name)
    if os.path.exists(file_path):
        if query_user:
            # Prompt the user to choose whether to use the existing file or the
            # original file specified by path_to_data
            choice = input(
                f"A file named {file_path} was found. Would you like to use "
                f"this file instead of {path_to_data}? (y/n): "
            )
            if choice.lower() == "y":
                path_to_data = file_path
        else:
            path_to_data = file_path

    return path_to_data


def read_local_transaction_csv(path_to_data, index_on_date=True, validate_data=True):
    # See if we have an updated transaction data file from a previous run today
    path_to_data = get_latest_transaction_file(path_to_data)
    if not os.path.exists(path_to_data):
        return None
    # Read the local transaction data into a dataframe
    df = read_lm_transactions_csv(path_to_data)
    if validate_data:
        if not validate_transactions(df, COLS_TO_VALIDATE):
            print(f"Invalid data found. Fix {path_to_data} and try again.")
            sys.exit(-1)

    if index_on_date:
        df.set_index([DATE], inplace=True)

    return df
