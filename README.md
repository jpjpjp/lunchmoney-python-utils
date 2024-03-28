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

When I first started using Lunch Money, I imported about 10 years worth of transactions from Mint.  Then I told Lunch Money about my active bank accounts and had it fetch transactions.  Unforutnatly, I didn't tell Lunch Money to ignore transactions older than the ones I imported.  This led to a lot of duplciates (and actually a few new transactions that Mint somehow never picked up).  This script is useful for identifying those duplicates so that they can all be easily deleted in one bulk transactions.

Even after doing this initial setup, I still occasionally find duplicate lunchmoney transactions, I'm not sure why.  This may be because of the way I originally imported my Mint transaction data, or an ongoing issue with Plaid, but it has happened enough that I thought it would be handy to write a small script to identify potential duplicates for inspection and then, based on the results of that inspection tag them as non-duplicates or mark them for deletion.

### Script Configuration
The script relies on the following settings in the [./config/lunchmoney-config.py](./config/lunchmoney_config.py), which you must set up the first time you run any of the scripts by following [these instructions](#configure-your-scripts).   

  - START_DATE_STR  - Earliest date to fetch transactions, in MM/DD/YYYY format
  - END_DATE_STR - Latest date to fetch transactions from, in MM/DD/YYYY format
  - LOOKBACK_LM_DUP_DAYS - The number of days to lookback for potential duplicates. This is necessary if a transaction was somehow categorized when it was pending and when it settled the date was actually later.  It's also useful when comparing Lunch Money/Plaid transactions with imported data since the transaction date can often be different - default is 7
  - CACHE DIR and LM_FETCHED_TRANSACTIONS_CACHE - The directory and name of a cache file for transactions fetched via the API. This is useful if you run this script multiple times.  After the first API request the data is written to `{CACH_DIR}/{LM_FETCHED_TRANSACTIONS_CACHE}-{START_DATE_STR}-${END_DATE_STR}.csv`.  Future requests for transactions from the same data range will use the cached copy if the file exists.   Delete this file to force a refresh pull from the API
  - ASK_UPDATE_NON_DUPS - When this parameter is set to True, and the user indentifies a potential set of duplicates as non duplicates, it will ask the user if they want to update the Payee or Notes field to make it clearer what the distinction is between the transactions.  This is useful when the script is run for "periodic hygiene" on your LunchMoney transactions, and most potential duplicates are actually legitimage.  This level of interactivity can be cumbersome however if you ar running this script after accidentally importing tons of plaid transactions that duplicate what you already imported in Mint.  In this case it is reccomended to set this configuration paramter to False to move more quicly through a large set of duplicate transacations.

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

## Other scripts

This repo includes the following other scripts.   In an effort to get some interested parties access to the `compare_plaid_with_mint.py` script, I have started the repo without documenting them yet.

  - [fix_negative_credits.py](./fix_negative_credits.py) - I found a few credit transactions that I imported from Mint which showed up as expenses in LunchMoney.  I had hoped to use the [Update Transaction API](https://lunchmoney.dev/#update-transaction) to fix these, but neither setting the `is_income` field or using the absolute value of the `amount` field got the intended result, so I ended up fixing them all manually in the GUI
  - [get_new_transactions.py](./get_new_transactions.py) is a script for adding the latest transactions to lunchmoney to a locally stored CSV of transactions in Mint format.
  - [list_unused_tags](./list_unused_tags.py) iterates through all the tags and lists the ones with zero transactions associated with them.  In my several attempts at Mint imports I ended up with multiple copies of tags, especially when the Mint transactions included more than one label.   For now, I simply use the output of this script to manually delete the tags, but if the API expands to include a `DELETE /tags` endpoint this could be run periodically as an automated cleanup job.
  - [compare_plaid_with_mint](./compare_plaid_with_mint.py) is my first attempt to come up with a tool to help deal with duplicates when you first import Mint data into Lunch Money and then add the same accounts to Lunch Money, accidentally fetching transactions that are earlier than the transactions that you imported.  I now thing that the [process_duplicates.py](#process-duplicates.py) script is the right way to deal with this issue.