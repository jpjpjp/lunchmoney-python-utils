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
# Cache File for read_or_fetch_lm_transactions in lib/transactions
###################################
# The name of the file to write lunchmoney transactions to that are fetched by the API
# If this file exists, the data here will be used instead of making an API call
# If not the API will append  _START-DATE_END-DATE.csv and write a cache for future requests
# Delete this file, to force an API call, or call delete_transactions_cache()
PATH_TO_TRANSACTIONS_CACHE = "/tmp/lm_transactions"

###################################

###################################
# Default location for input and output files
###################################
INPUT_FILES = "./input"
OUTPUT_FILES = "./output"

###################################
# Variables used by get_new_transaction.py
###################################
LOOKBACK_TRANSACTION_DAYS = 7
###################################
# Variables used by process_duplicates.py
###################################
# Number of days to look for duplicate transactions
LOOKBACK_LM_DUP_DAYS = 7


###################################
# Variables used by compare_plaid_with_mint.py
###################################
# Start and End Dates to fetch transactions - in MM/DD/YYYY format
START_DATE_STR = "1/1/2021"
END_DATE_STR = "12/31/2023"
# The name of the csv file with your mint transactions, in the INPUT_FILES directory
MINT_CSV_FILE = "transactions.csv"
# The format of the date strings in your Mint data
# This is the format of the dates as exported by Mint and LunchMoney
MINT_DATE_FORMAT = "%Y-%m-%d"
# This is the format of dates once a CSV is opened and saved in Excel
# MINT_DATE_FORMAT = "%m/%d/%y"

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

###################################
# Variables used by prep_categories.py
###################################
# Name of CSV that defines Spending Groups in the config directory
SPENDING_GROUP_DEFINITIONS = "default-mint-spending-groups.csv"

###################################
# Filenames written by prep_categories.py and read by create_category_groups.py
###################################
# Name of generated file with a list of objects that define the set
# of new category groups to be created.
CATEGORY_GROUP_DEFINITIONS = "category_group_objects.json"

# Name of output file with a list of objects that define the set
# of new category groups to be created
CATEGORY_ASSIGNEMENTS = "category_objects.json"
