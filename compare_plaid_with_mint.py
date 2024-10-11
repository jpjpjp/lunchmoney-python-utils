"""compare_plaid_with_mint.py

    This program compares a set of transactions from lunchmoney that were pulled from
    financial institutions via plaid, with a set of transactions that were exported
    from Mint.

    When I first started using LunchMoney I imported my initial set of transactions
    from Mint and then connected my accounts using Plaid.   I accidentally pulled
    transactions from the same timeframe as the mint transactions, but when I went to
    delete the duplicate I noticed that some of the transactions that were pulled via
    Plaid were missing from my Mint transactions.

    Given a csv file that contains the Mint transactions for the expected period, this
    program generates two csv files as output

    plaid_analyzed_transactions-start_date-end_date.csv
    contains details about all the lunchmoney transactions that have a
    "source" set to "plaid", along with three additional columns:
        - analysis: will be either "Duplicate" or "Investigate"
        - related_id: with be the index in the generated file of Mint transactions
                      which will contain a unique index for each transaction

        A value of "Investigate" indicates that the pulled transaction may be
        missing from the mint data.  Some investigation is generally warranted as
        there may be discrepancies due to transaction vs. settled date, transactions
        that were split in Mint before being exported, or other manual changes

    mint_analyzed_transactions.csv is a copy of the mint input file with two
    additional columns:
        - analysis: will be either "Match" or blank
        - related_id: with be the index in the plaid file that matches

        Transactions with an empty "analysis" field are good candidates to match up
        with Plaid transactions labeled "Investigate

    To facilitate manual analysis, the files are sorted in order of Account Name, and
    then descending date.  Note that different account names can stymie the analysis,
    see the documentation for the filter_matches_by_account function in the
    find_duplicates.py module for details on how to resolve this
"""

from datetime import datetime
import os
import pandas as pd
import sys

# Local modules
from lib import find_duplicates as fd
from lib import transactions as trans
from config import lunchmoney_config as lmc

# Check that API Token is set
if lmc.LUNCHMONEY_API_TOKEN == "":
    print("Ensure that LUNCHMONEY_API_TOKEN is set in lunchmoney_config.py")
    print("Obtain a token from a https://my.lunchmoney.app/developers")
    sys.exit()

START_DATE = datetime.strptime(lmc.START_DATE_STR, "%m/%d/%Y")
END_DATE = datetime.strptime(lmc.END_DATE_STR, "%m/%d/%Y")


def main():
    """ Read in the transactions from lunchmoney and mint and identify possible
        duplicates.   Write out csv files with all the lunchmoney and mint transactions
        with the following new information:

        plaid_analyzed_transactions - all transactions with a "source" of "plaid"
            "action" - "Duplicate" or "Investigate
            "related_id" - index of duplicate transaction in mint data

        mint_analyzed_transactions - all originally supplied mint transactions
            "action" - "Duplicate" or blank
            "related_id" - id of the lunchmoney transaction in the plaid CSV output
    """
    plaid_df = prepare_plaid_dataset(START_DATE, END_DATE)
    mint_df = prepare_mint_dataset(os.path.join(lmc.INPUT_FILES, lmc.MINT_CSV_FILE))

    # Read in the mapping of LM/Mint Account Name synonyms
    act_name_map_file = os.path.join(lmc.CONFIG_FILES, lmc.ACCOUNT_NAME_MAP_FILE)
    if os.path.isfile(act_name_map_file):
        acct_name_df = pd.read_csv(act_name_map_file)
    else:
        acct_name_df = None

    # Try to correlate each of the Plaid transactions with the ones from Mint
    print(f"Correlating {len(plaid_df)} transactions with mint data")
    (plaid_df, mint_df) = fd.find_duplicates(
        plaid_df,
        mint_df,
        update_fn=report_findings,
        acct_name_df=acct_name_df,
        lookback_days=lmc.LOOKBACK_DAYS,
        lookahead_days=lmc.LOOKAHEAD_DAYS,
        old_type="mint",
    )
    duplicate_count = (plaid_df["action"] == "Duplicate").sum()
    investigate_count = (plaid_df["action"] == "Investigate").sum()
    print(
        f"\n\nAfter comparing {len(plaid_df)} lunchmoney transactions with "
        f"{len(mint_df)} mint transactions:\n"
        f"Found {duplicate_count} duplicates with "
        f"{investigate_count} left to investigate\n"
    )
    print(
        "Look for plaid_analyzed_transactions.csv and mint_analyzed_transactions.csv "
        f"in the {lmc.OUTPUT_FILES} directory to begin the analysis"
    )
    plaid_df.to_csv(
        os.path.join(lmc.OUTPUT_FILES, "plaid_analyzed_transactions.csv"), index=False
    )
    mint_df["Date"] = mint_df["Date"].dt.strftime(lmc.MINT_DATE_FORMAT)
    mint_df.to_csv(
        os.path.join(lmc.OUTPUT_FILES, "mint_analyzed_transactions.csv"), index=True
    )


def report_findings(lm_df, lm_index, mint_df, mint_index):
    """This function is called by the find_duplicates function after it
    has identified a plaid transaction has a counterpart in the mint data.

    We update the lunchmoney transaction row with the "action" of "Duplicate" and
    set the "related_id" cell to the index of the matching row in the mint data
    (since Mint transactions do not have a unique transaction ID)

    We update the matching mint transaction row with an "action" of "Match and
    set the "related_id" cell the transaction id of matching lunchmoney transaction
    """
    lm_df.loc[lm_index, ["action", "related_id"]] = [
        "Duplicate",
        mint_index,
    ]
    mint_df.loc[mint_index, ["action", "related_id"]] = [
        "Match",
        lm_df.loc[lm_index, "id"],
    ]


def sort_by_account_date(df, acct_name, date):
    sorted_df = df.sort_values(by=[acct_name, date], ascending=[True, False])
    return sorted_df


def prepare_plaid_dataset(start_date, end_date):
    """This function reads or fetches a set of lunchmoney transactions in the
    specified date range and transforms it into
    a dataframe, reducing low value columns while adding
    the new "analysis" and "related_id" columns.  Finally it discards any
    transactions that do not have a "source" of "plaid"

    Returns: dataframe of lunchmoney transactions that were pulled via the plaid
             integration, sorted by account and descending date of transactions

    A side effect of this function is to write a csv file 'ignored_transactions.csv'
    which contains any transactions with a "source" value other than "plaid"
    """
    df = trans.read_or_fetch_lm_transactions(start_date, end_date)
    if "action" not in df.columns and "related_id" not in df.columns:
        # This a previously unprocessed data pull from LunchMoney,
        # Thin out the columns, add our analysis columns, and sort
        df = df[
            [
                "id",
                "date",
                "payee",
                "amount",
                "category_name",
                "plaid_account_id",
                "account_display_name",
                "source",
            ]
        ].copy()
        df["action"] = None
        df["related_id"] = None
        plaid_df = df[df.source == "plaid"]
        plaid_df = sort_by_account_date(plaid_df, "account_display_name", "date")
    else:
        plaid_df = df

    other_df = df[~df.source.isin(["plaid"])]
    if len(other_df):
        print(
            f"Found {len(other_df)} transactions with a source other than plaid.\n"
            "These are ignored and in ignored_transactions.csv"
        )
        other_df.to_csv(os.path.join(lmc.OUTPUT_FILES, "ignored_transactions.csv"))

    return plaid_df


def prepare_mint_dataset(mint_csv_file):
    """This function reads a set of transactions exported from Mint into
    a dataframe while adding the new "analysis" and "related_id" columns

    Returns: dataframe of mint transactions with the new empty columns
    """
    df = pd.read_csv(
        mint_csv_file, parse_dates=["Date"], date_format=lmc.MINT_DATE_FORMAT
    )

    if "action" not in df.columns and "related_id" not in df.columns:
        # This a previously unprocessed export from Mint,
        # Add our analysis columns, sort and reindex
        df["action"] = None
        df["related_id"] = None
        df = sort_by_account_date(df, "Account Name", "Date")

        # Since Mint transactions don't include a unique ID we'll use the index
        df.reset_index(drop=True, inplace=True)
    else:
        # Reread the file, using the existing indexes from a previous analysis
        df = pd.read_csv(
            mint_csv_file, parse_dates=["Date"], index_col=0, date_format="%m/%d/%y"
        )

    return df


