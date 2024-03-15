# Lunchmoney Utilities

This repo includes a set of scripts that I created to do various manipulations of data that I have in [LunchMoney](https://my.lunchmoney.app), an online tool for aggregating financial transactions (among other things).

I came to LunchMoney after many years of using [Mint.com](https://mint.intuit.com/), which was declared an end of life product in 2023. I exported my data from Mint and began importing it into LunchMoney. I also configured my new LunchMoney account to have automatic connections with most of the finanical institutions that I was gathering data from in Mint.

In my case, I made several missteps resulting in duplicate transactions, incorrect Tags/Labels, and a few other problems.  The initial set of scripts in this repo were designed to help me get my transactions into better shape.  

**WARNING**  - These scripts were written for my specific use cases.  Your mileage may vary.  Currently none of the scripts delete any data, but it never hurts to export your existing transaction data as a backup before starting.

## Checklist to setup the environment to run the scripts

Clone this repository using `git clone https://github.com/jpjpjp/lunchmoney-python-utils` from a terminal window on your machine, or click on the green "Code" button and select "Download as Zip".

Open a terminal window where the repo was cloned or unzipped to.

### Configure conda environment

1) The utilities in this package require conda python.  If this is not yet installed please, download and install it from here:  https://conda.io/miniconda.html

2) Once properly installed run the following command in this directory:

    conda env create -f environment.yml

3) This will create the environment for the scripts to run in and download all necessary dependencies.   After this process completes run this command:

    conda activate lunchmoney-utils

### Configure your scripts

Before running the scripts for the first time, you'll need to copy the template configuration file and adjust it to your needs:

1. Copy `config/lunchmoney_config_template.py` to `config/lunchmoney_config.py`.
2. Open `config/lunchmoney_config.py` and fill in your specific configuration details.   All scripts require the following configuration element:
  - LUNCHMONEY_API_TOKEN - set this to your API token which you can get from the [LunchMoney Developers page](https://my.lunchmoney.app/developers).

3.  The remaining configuration elements are script specific and outlined in the script documentation

## process_duplicates.py

I still occasionally find duplicate lunchmoney transactions, I'm not sure why.  This may be because of the way I originally imported my Mint transaction data, or an ongoing issue with Plaid, but it has happened enough that I thought it would be handy to write a small script to identify potential duplicates for inspection and then, based on the results of that inspection tag them as non-duplicates or mark them for deletion.

### Script Configuration
The script relies on the following settings in the [./config/lunchmoney-config.py](./config/lunchmoney_config.py), which you must set up the first time you run any of the scripts by following [these instructions](#configure-your-scripts).   

  - START_DATE_STR  - Earliest date to fetch transactions, in MM/DD/YYYY format
  - END_DATE_STR - Latest date to fetch transactions from, in MM/DD/YYYY format
  - LOOKBACK_LM_DUP_DAYS - The number of days to lookback for potential duplicates - default is 7
  - PATH_TO_TRANSACTIONS_CACHE - The location of a cache file for transactions fetched via the API  This is useful if you run this script multiple times.  After the first API request the data is written to `{PATH_TO_TRANSACTIONS_CACHE}-{START_DATE_STR}-${END_DATE_STR}.csv`.  Future requests for transactions from the same data range will use the cached copy if the file exists.

### Running the script

After ensuring that your environment is set up as [described here](#checklist-to-setup-the-environment-to-run-the-scripts), type the following in your terminal:
  ```bash
  python process_duplicates.py
  ```
This script will fetch all the all the transactions in the specified data range, ignoring pending transactions and any parents of split transactions.   It will sort the transactions by `account_display_name` and then attempt to identify any transactions with the same account, amount, and a date within a LOOKBACK_LM_DUP_DAYS window.

When it finds multiple transactions that meet this criteria they are presented to the user, who is asked to interactively identify if one is a duplicate or if all the transactions are valid.   If a duplciate is identified it is **marked for deletion**.  If the transactions are verfied as non duplicate, they are updated with the "Not-Duplicate" tag to prevent triggering this process in the future.   The user also has an opportunity to update the Payee or Notes field with more details explaining the difference between the two.

**Note on Deletion** Currently, the Lunchmoney API does not provide an interface for deleting transactions, so transactions marked for deletion are tagged with tag named: "Duplicate".   After the script completes it will write any transactions tagged as a duplicate to the ouptut directory.

After the script runs, the user can filter for transactions with the "Duplicate" tag and delete them.

## prep_categories.py and create_category_groups.py

These two scripts "team up" to create a set of category groups in lunchmoney based on a csv file that defines the desired category groups and their subcategories.  It may be especially useful to former Mint users who have imported their transactions from Mint.  

Mint has the concept of "Spending Groups" which logically groups categories together, for example the Spending Group "Education" includes that categories "Tuition", "Student Loan" and "Books & Supplies".   Unfortunately, the relationships between Spending Groups and Categories is not preserved when transactions are exported from Mint.

Fortunately, the LunchMoney data model treats "Category Groups" as a first class citizen, allowing them to be created via API and exposed when transactions are fetched via the API. These scripts allow users to automatically create a set of Category Groups and associate them with a set of logical sub categories based on an input configuration file.

### Script Configuration
The scripts rely on three settings in the [./config/lunchmoney-config.py](./config/lunchmoney_config.py), which you must set up the first time you run any of the scripts by following [these instructions](#configure-your-scripts).   For most users the default settings for these configurations will be sufficient:

  - SPENDING_GROUP_DEFINITIONS - a CSV file which describes the proposed category groups in the first row, and the proposed sub_categories in the columns.   The default Mint Spending Group definitions are supplied in the file [./config/default-mint-spending-groups.csv](./config/default-mint-spending-groups.csv), which is the default setting for this configuration.
  - CATEGORY_GROUP_DEFINITIONS - This file will be generated by the `prep_categories.py` script and read as input by the `create_category_groups.py` script.  It has details about the proposed and existing lunchmoney category groups.
  - CATEGORY_ASSIGNMENTS - This file is also generated by the first script and used by the second.  It contains details about the existing lunchmoney categories and how they will be changed by running the `create_category_groups.py` script

It's worth mentioning that one difference between Mint and LunchMoney is that Mint users could assign a transaction to either a Category or Spending Group.  For example, you could categorize a transaction with the category "Education" even though this is also considered a Spending Group. LunchMoney does not allow transactions to be categorized as a Category Group.

These scripts will rename any categories that have the same name as a proposed category group.  For example, if you use the default spending group definitions, it will rename the existing category "Education" to "Education Misc", and then create a new category group called "Eduction", making the category "Education Misc" a subgroup of that category.   All transactions that were previously categorized as "Education" will now have a category of "Education Misc".

### Running the scripts

After ensuring that your environment is set up as [described here](#checklist-to-setup-the-environment-to-run-the-scripts), start typing the following in your terminal:
  ```bash
  python prep_categories.py
  ```
This script will fetch all the existing categories from your LunchMoney account and compare them with your proposed category groups and sub groups.   It will generate ouput to the terminal that describes which of those categories will be renamed by the next script, which category groups already exist, and which category groups will be created.

It will also generate a list of existing categories that are not assigned to any category. You may wish to update your spending group definition file to assign these remaining categories to a category group and rerun this script.  You can safely rerun this script as many times as necessary as it does not make any changes to your actual LunchMoney configuration.

Once the changes proposed by the `prep_categories.py` script are to your liking you can run the script to actually make the canges by typing the following in your terminal:
  ```bash
  python create_category_groups.py
  ```
  **WARNING - This step is not reversable!**

This script will read the configuration files written by the other script, rename the existing categories as needed, and create any new Category Groups with their proposed sub categories.

As each step takes place, details are written to the terminal.  Note that a one second pause is added between each API call to avoid overloading the LunchMoney servers or hitting any API Rate limits.

After running this script you can view your updated categories in the [LunchMoney Gui](https://my.lunchmoney.app/categories) to confirm that the changes are as expected.

## compare_plaid_with_mint.py

This script compares a set of transactions in LunchMoney that were imported directly from their financial institution via Plaid, with a CSV file of Mint transactions that were previously imported into Lunchmoney.

### Background

When I first started using LunchMoney, I began by importing an initial set of transactions from Mint.  I later set up automatic connections to my accounts in LunchMoney via Plaid. When these connections are first set up there is an option to set how far back in time to pull transactions. I've seen that some users on the forum forget to do this.  In my case I attempted to do this by rolling back the month and day to the last date of an imported Mint transaction, but did not notice that the default year in this dialog was one year ago.

This tool addresses the challenge of identifying duplicate transactions and discrepancies between the transactions pulled from Plaid and those exported from Mint.

### Script Configuration

Before running the script set the following variables in config/lunchmoney_config.py

  - START_DATE_STR  - Earliest date to fetch transactions, in MM/DD/YYYY format
  - END_DATE_STR - Latest date to fetch transactions from, in MM/DD/YYYY format
  - MINT_CSV_FILE - Name of the csv file with your mint transactions, in the `input` directory
  - MINT_DATE_FORMAT - The default of "%Y-%m-%d" is probably OK
  - PATH_TO_TRANSACTIONS_CACHE - The location of a cache file for transactions fetched via the API  This is useful if you run this script multiple times.  After the first API request the data is written to `{PATH_TO_TRANSACTIONS_CACHE}-{START_DATE_STR}-${END_DATE_STR}.csv`.  Future requests for transactions from the same data range will use the cached copy if the file exists.
  - LOOKBACK_DAYS - Number of days earlier than the transaction date in the Lunchmoney/Plaid transaction to check for duplicates in the Mint Data
  - LOOKAHEAD_DAYS - Number of days later than the transaction date in the Lunchmoney/Plaid transaction to check for duplicates in the Mint Data

Note that the LOOKBACK and LOOKAHEAD_DAYS are necessary because while LunchMoney tends to use the date that the transaction occured, most Mint connectors used the settled date (usually a bit later) as the transaction date.   You can experiment with these values.   The larger the window, the more likely it is that you will get multiple duplicate candidates.  When this occurs the script will interactively ask you to select the correct one.   When the window is smaller you are more likely to miss some duplicates which will require manual investigation.

There is a second optional configuation file called `account_name_map.csv`.  This file allows you to map the "account_display_name" that LunchMoney uses for the Plaid transactions with the "Account Name"s that were in your Mint Import data.   To set up this mapping:
  1)  copy [`/config/account_name_map-template.py`](./config/account_name_map-template.py) to `config/account_name_template.py`.   
  2) Edit the file with your specific account names.  
      - The first "row" is the set of names of the accounts used by your Plaid transactions.  You can find these on the [Accounts - Lunch Money](https://my.lunchmoney.app/accounts) page in the `Automatic bank syncing via Plaid` section.  You only need to include the ones where the name is different for Mint
      - The second row is the set of account names used in your Mint Transactions.  If you did not modify these during the original import you can find these on the [Accounts - Lunch Money](https://my.lunchmoney.app/accounts) in the `Manually-managed accounts` section, however if you changed any of these via the Import Wizard, you will need to use the accounts in your Mint transactions CSV file.   Put each Account Name in the "column" that matches the LunchMoney account name that you put in row 1.
      - If multiple imports took place, or if your Mint data has multiple Account Names that map to a single Plaid account, additional rows can be added to add additional synonyms
      
      Each "column" in the CSV file is a set of synonyms that map Mint Account Names to the Plaid Account Name at the top of the column.

### Running the script

Once the configuration is set you can execute the script by typing the following in a terminal window:
```sh
python compare_plaid_with_mint.py
```

The script will fetch/read in the two sets of transactions and attempt to match duplicates between the two input sources.  A Plaid transaction is considered to duplicate a Mint transaction if the "Amount" and "Account" are the same, and the "Date" for the Mint transaction falls within the specified window of the date for the Plaid transactions.

If multiple possible transactions match the criteria, the user is interactively prompted to select the right transaction to map as a duplicate.

When the script completes it's run, it writes two new files to the `output` directory:
  - `plaid_analyzed_transactions.csv` has the details of all the plaid transactions that were fetched along with two additional columns: "action" and "related_id".   The "action" column will be populated with the word "Duplicate" or "Investigate".   If it is "Duplicate", the "related_id" column will have the index of the transaction in the mint output file that matches the Plaid transaction.
  - `mint_analyzed_transactions.csv` is a list of all the Mint transactions with an index column and the same two additional columns.   If a duplicate was found the "action" column will include the word "Match" and the "related_id" will the be id field of the duplicate transaction in the plaid file.

Both files will have the transactions sorted first by Account Name, and then by Date which makes any manual analyis easier.

### Analyzing the Output

After running this script I typically, open both files side by side and start by randomly selecting a few transactions with an "action" of "Duplicate" in the plaid output file and then look for the matching index in the mint output file to convince myself that the matching is legitamite.  I also do the reverse, by looking at some random transactions with an "action" of "Match" in the mint file and look for the "requested_id" in the plaid file.

I then focus on looking at each of the transactions listed as "Investigate" to see why a match wasn't found.  In my experience this can happen for the following reasons:
- The same account is named differently between LunchMoney and Mint.  In this case, edit the `config/account_name_template.csv file and run again.  
  - Pro Tip: you can copy the `output/plaid_analyzed_transactions.csv` to `./input/${LM_CSV_FILE_BASE}-{START_DATE_STR}-${END_DATE_STR}.csv` and `output/mint_analyze_transactions.csv` to `input/${MINT_CSV_FILE}` to use this output as input for the subsequent run.  This will save you the work of re-doing any manual disambiguation for duplicates that were previously identified.
- The transaction was split in Mint.   In this case I can find two or more transactions for the same account on around the same day that add up to the total amount.  After finding this I'll generally manually set the "action" cell for the plaid transaction to "Duplicate"
- The Mint transaction has a date that is set outside of the [LOOKAHEAD/LOOKBACK]_DAYS window.   These can be manually identified or you can experiment with broadening this window and rerunning the script (see Pro Tip above!)
- There may be Plaid transactions pulled for accounts or dates that simply weren't represented in the Mint data.   I found several example of this in my data, even though I was sure that I had the accounts set up in Mint and Mint covered the dates.  My only conclusion was that Mint connectivity got flaky in 2023 and transactions were simply missed.   When I identified these types of Transactions, I set the "action" column to "Keep" in the plaid output file.

### Deleting the duplicates

My original plan was to write a tool that could ingest the `plaid_analyzed_transacetions.csv` file and use the API to delete all the transactions with an "action" of "Duplicate", however I realized that there is not yet an API that allows for the deletion of a single transaction.

What I ended up doing was realizing that it was a big mess.  I manaully pulled the few transactions that were in the plaid data that was not in my original Mint import, into my Mint file, deleted all my transactions, and started from scratch with a new import file that included the missing transactions from Plaid.

You could attempt to manually delete the duplicate transactions, or it should be possible to write a script that could use [Create Transaction Group](https://lunchmoney.dev/#create-transaction-group) and [Delete Transaction Group](https://lunchmoney.dev/#delete-transaction-group) APIs.  If anyone is interested, I'd be happy to create an initial version of this script for you to test on your data.  Just open a pull request or direct message `jpjpjp` on the [LunchMoney Discord Server](https://discord.com/channels/842337014556262411/1134593926297309204)

## Other scripts

This repo includes the following other scripts.   In an effort to get some interested parties access to the `compare_plaid_with_mint.py` script, I have started the repo without documenting them yet.

  - [fix_negative_credits.py](./fix_negative_credits.py) - I found a few credit transactions that I imported from Mint which showed up as expenses in LunchMoney.  I had hoped to use the [Update Transaction API](https://lunchmoney.dev/#update-transaction) to fix these, but neither setting the `is_income` field or using the absolute value of the `amount` field got the intended result, so I ended up fixing them all manually in the GUI
  - [get_new_transactions.py](./get_new_transactions.py) is a script for adding the latest transactions to lunchmoney to a locally stored CSV of transactions in Mint format.
  - [list_unused_tags](./list_unused_tags.py) iterates through all the tags and lists the ones with zero transactions associated with them.  In my several attempts at Mint imports I ended up with multiple copies of tags, especially when the Mint transactions included more than one label.   For now, I simply use the output of this script to manually delete the tags, but if the API expands to include a `DELETE /tags` endpoint this could be run periodically as an automated cleanup job.