"""process_duplicate.py

    This program analyzes a set of transactions from lunchmoney and indentifies
    potential duplicates, displaying them to the user interactively.

    If the user confirms that one or more of the transactions is a duplicate,
    the program deletes the duplicate transactions.

    *** NOTE THE API DOES NOT YET SUPPORT TRANSACTION DELETION.
        FOR NOW THE FUNCTION lunchmoney_delete_transaction() TAGS
        TRANSACTIONS AS "DUPLICATE" SO THEY CAN BE EASILY DELETED IN THE GUI ***

    If the user indicates that the transactions are each unique,
    the transactions are given a tag "Not-Duplicate" to prevent them from being
    flagged again in future runs

    If any transactions are deleted/tagged as duplciates, they are written to an
    output file for further examination
"""
import os
from datetime import datetime
from lib.transactions import read_or_fetch_lm_transactions
from lib.find_and_process_dups import find_duplicate_transactions
from config.lunchmoney_config import START_DATE_STR, END_DATE_STR, LOOKBACK_LM_DUP_DAYS


def find_lunchmoney_duplicates(df, lookback_days=0):
    """ Identifies potential duplicate transactions

    dup_ids = find_duplicate_transactions(df, lookback_days=LOOKBACK_LM_DUP_DAYS)

    if len(dup_ids):
        # We found duplicates, write them to a CSV file to be examined
        dup_df = df[df["id"].isin(dup_ids)]
        today_date_str = datetime.now().strftime("%Y-%m-%d")
        output_file_path = os.path.join(
            CACHE_DIR, f"marked_as_duplicate_{today_date_str}.csv"
        )
        dup_df.to_csv(output_file_path, index=False)
        print(f"Found {len(dup_df)} duplicates. Details written to: {output_file_path}")
        # TODO provide a link that will show all files tagged with 'Duplicate' that
        # a user could click on.  This requires figuring out what the category_id is
        # for duplicate which will be unique for each lunchmoney user

if __name__ == "__main__":
    from lib.transactions import (
        read_or_fetch_lm_transactions,
    )
    from config.lunchmoney_config import START_DATE_STR, END_DATE_STR

    # Fetch the transactions from LunchMoney
    df = read_or_fetch_lm_transactions(
        datetime.strptime(START_DATE_STR, "%m/%d/%Y"),
        datetime.strptime(END_DATE_STR, "%m/%d/%Y"),
        remove_pending=True,
        remove_split_parents=True,
    )

    dups_found = find_lunchmoney_duplicates(df, lookback_days=LOOKBACK_LM_DUP_DAYS)

    if not dups_found:
        print('No duplicates found!')
    else:
        print("Remove duplicate transactions in LunchMoney by filtering on the "
              "'Duplicate' tag.")
