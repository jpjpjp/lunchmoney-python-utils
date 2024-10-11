""" update_payees.py

    This file uses update_local_transactions to create a dataframe of all lunch money
    transactions for the API key, using a locally stored copy of the transaction
    data if its available, or by fetching it directly from the API.  As a side
    effect it updates the locally stored transaction data.

    It then filters the dataframe for all transactions whose payee starts with
    a configured string and updates those transactions using the following logic
    1) It removes the defined string up to an optional terminator character from the payee
    2) If any notes exist on the transaction they are moved to the payee, appended to
       any remaining text
    3) The notes are then updated to "Paid via: " with the extracted string from the payee field
"""

# Import necessary modules
# import shutil
import pandas as pd
import sys


# Import configuration file and shared methods
import config.lunchmoney_config as lmc
from update_local_transactions import (
    update_local_transactions
)
from lib.transactions import (
    lunchmoney_update_transaction
)

def build_update_list(df):
    update_list = []

    for index, row in df.iterrows():
        payee = row['payee']
        notes = row['notes'] if pd.notna(row['notes']) else ""
        
        # Extract the new notes
        terminator_index = payee.find(lmc.PAYEE_TERMINATOR) if lmc.PAYEE_TERMINATOR else -1
        if terminator_index != -1:
            new_notes = "Paid via " + payee[:terminator_index]
            remaining_payee = payee[terminator_index + len(lmc.PAYEE_TERMINATOR):].strip()
        else:
            new_notes = "Paid via " + payee
            remaining_payee = ""

        # Construct the new payee
        if remaining_payee:
            new_payee = remaining_payee
            if notes:
                new_payee += " - " + notes
        else:
            new_payee = notes if notes else lmc.EMPTY_PAYEE_STRING

        update_list.append({
            "id": row["id"],
            "index": index,
            "new_notes": new_notes,
            "new_payee": new_payee
        })

    return update_list

def format_transaction(transaction):
    """
    Format a transaction series into a string with specific fields formatted.
    - Date is converted to 'YYYY-MM-DD'.
    - Tags are converted from a list of objects to a comma-separated string of names.
    """
    # Extract and format the date
    formatted_date = transaction["date"].strftime("%Y-%m-%d")

    # Extract and format the tags
    if transaction["tags"] and isinstance(transaction["tags"], list):
        formatted_tags = ", ".join(
            tag["name"] for tag in transaction["tags"] if "name" in tag
        )
    else:
        formatted_tags = ""

    # Create the formatted string
    formatted_transaction = (
        f"Date: {formatted_date}, "
        f"Amount: {transaction['amount']}, "
        f"Payee: {transaction['payee']}, "
        f"Category Name: {transaction['category_name']}, "
        f"Account Display Name: {transaction['account_display_name']}, "
        f"Notes: {transaction['notes']}, "
        f"Tags: {formatted_tags}"
    )

    return formatted_transaction

def update_transactions(df, update_list, interactive=True):
    if (interactive):
        print(f"Found {len(df)} transactions to update")
        for update in update_list:
            transaction = df.loc[update["index"]]
            formatted_transaction = format_transaction(transaction)
            print(f"Transaction to update: {formatted_transaction}")
            print(f"New Payee: {update['new_payee']}")
            print(f"New Notes: {update['new_notes']}")

        print("\nProceed with update y/n? ", end="")
        user_input = input().strip().lower()
    else:
        user_input = "y"

    if user_input == "y":
        for update in update_list:
            print(".", end="")
            if len(update["new_payee"])>= 140:
                if interactive:
                    print("New Payee exceeds 140 character limit: " + update["new_payee"])
                    print("Press 'y' to truncate and continue or 'n' to stop process and manually edit (y/n)", end="")
                    user_input = input().strip().lower()
                    if user_input != "y":
                        print("Return to lunch money and fix the long notes field for:")
                        print(format_transaction(df.loc[update["index"]]))
                        sys.exit()
                update["new_payee"] = update["new_payee"][:140]
                
            api_response = lunchmoney_update_transaction(
                update["id"],
                {"payee": update["new_payee"], "notes": update["new_notes"]}
            )
            if "updated" not in api_response or not api_response["updated"]:
                print(f'Error calling Lunch Money PUT /transactions: {api_response}')
                print(f'id: {update["id"]}, payee:{update["new_payee"]}, notes:{update["new_notes"]}')
                sys.exit()
    
    print("\nAll transactions updated successfully.")
                
# TODO add a command line param to run non-interactively
def main():
    df = update_local_transactions()

    # Find the transactions whose "payee" category starts with the lmc.PAYEE_SEARCH_STRING
    filtered_df = df[df['payee'].str.startswith(lmc.PAYEE_SEARCH_STRING)]
    update_list = build_update_list(filtered_df)
    update_transactions(filtered_df, update_list)



if __name__ == '__main__':
    sys.exit(main())


