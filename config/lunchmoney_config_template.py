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
# Directory to use for temporary and local cache files
CACHE_DIR = "/tmp"
# Name for local cache of fetched transactions, handy for iterative development
LM_FETCHED_TRANSACTIONS_CACHE = "lm_transactions"

###################################
# Default location for input and output files
###################################
INPUT_FILES = "./input"
OUTPUT_FILES = "./output"
CONFIG_FILES = "./config"

###################################
# Variables used by get_new_transaction.py and update_local_transactions.py
###################################
LOOKBACK_TRANSACTION_DAYS = 7

###################################
# Date range of transactions to fetch
# Used by process_duplicates and compare_plaid_with_mint.py
###################################
# Start and End Dates to fetch transactions - in MM/DD/YYYY format
START_DATE_STR = "1/1/2024"
END_DATE_STR = "4/25/2024"

#####################################
# Variables used by update_local_transaction_data.py
#####################################
PATH_TO_LOCAL_TRANSACTIONS = "lm-transaction-backup.csv"
# Validate that local data has required fields
DATE = "date"
PAYEE = "payee"
AMOUNT = "amount"
CATEGORY = "category_name"
ACCOUNT = "account_display_name"
COLS_TO_VALIDATE = [DATE, PAYEE, AMOUNT, CATEGORY, ACCOUNT]

###################################
# Variables used by process_duplicates.py
###################################
# Number of days to look for duplicate transactions
LOOKBACK_LM_DUP_DAYS = 7
# If two or more transactions look like duplicates but aren't it could be helpful
# to provide more info in the Payee or Notes field to help disambiguate
# If this parameter is set to anything, the interactive process of disambiguation
# will provide the ability to update these fields when tagging a transaction as non-dup
# Comment out or set to False to avoid this behavior which may be desirable
# when processing many transactions which are in fact duplicates
# Set to True when periodically running this script..
ASK_UPDATE_NON_DUPS = False


###################################
# Variables used by update_payees.py
###################################
# This script will remove text from the payee field and will move it to 
# the notes field.   These configurations control what text to look for
# and how that text will be removed
# String to look for at the beginning of the payee field
PAYEE_SEARCH_STRING = "CHECK"
# Terminator for string to extract
PAYEE_TERMINATOR = "-"
# Using these as an example it will extract any string that starts with
# CHECK up until a hyphen so for example it would extract:
# CHECK 12354 - from CHECK 12354 - Monthly Rent
# If there is no hyphen it will extract the entire payee field

# This is the string that will be assigned to the payee if there is no
# data after the PAYEE_TERMINATOR and no notes in the updated transactions
# Search for this in the GUI and update accordingly
EMPTY_PAYEE_STRING = "???"


###################################
# Variables used by compare_plaid_with_mint.py  and get_new_transactions.py
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
# increase the number of times you will be prompted to manually disambiguate multiple
# possible duplicates, when the program runs.
# Setting these to smaller number will result in more transactions with an action of
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
