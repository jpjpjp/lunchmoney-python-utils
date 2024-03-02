""" lunchmoney_config.py
    This file defines a set of configuration
    variables that will be used by the various scripts
    scripts to help analyze mint transaction data
"""
###################################
# API Key used by all utilities
###################################
# Lunchmoney API Token available here: https://my.lunchmoney.app/developers
LUNCHMONEY_API_TOKEN = "<YOUR_TOKEN_HERE>"

###################################
# Default location for input and output files
###################################
INPUT_FILES = "./input"
OUTPUT_FILES = "./output"

###################################
# Variables used by get_new_transaction.py
###################################
LOOKBACK_TRANSACTION_DAYS = 7
LM_FETCHED_TRANSACTIONS_CACHE = "lm_transactions"

###################################
# Variables used by compare_plaid_with_mint.py
###################################
# Start and End Dates to fetch transactions - in MM/DD/YYYY format
START_DATE_STR = "1/1/2021"
END_DATE_STR = "12/31/2023"
# The name of the csv file with your mint transactions, in the INPUT_FILES directory
MINT_CSV_FILE = "transactions.csv"
# The format of the date strings in your Mint data
MINT_DATE_FORMAT = "%Y-%m-%d"
# The name of the file to write lunchmoney transactions to that are fetched by the API
# If this file exists, the data here will be used instead of making an API call
# Delete this file, in the INPUT_FILES directory, to force an API call
LM_CSV_FILE_BASE = "plaid_analyzed_transactions"
# The date of plaid transactions in Lunchmoney is the transaction date
# Mint dates are typically the transaction settle date so can be some days later
# For at least one of my accounts I've seen the Mint dates be earlier than Plaid too.
# These variables control the date window to search for a duplicate in the Mint data
# Setting these to larger numbers will result in more duplicates found, and likely
# increase the number of times you will be prompted to manually disambigute multiple
# possible duplicates, when the program runs.
# Setting these to smaller number will result in more transations with an action of
# Investigate, requiring more post run manual analysis.
LOOKBACK_DAYS = 1
LOOKAHEAD_DAYS = 7

# An optional csv file that maps account names as they appear in LunchMoney to how
# they appear in the exported Mint transactions
ACCOUNT_NAME_MAP_FILE = "account_name_map.csv"
