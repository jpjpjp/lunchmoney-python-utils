"""fix_negative_credits.py
    This file was generated by ChatGPT from the following prompt:
        Write a python script called fix_negative_credits.py, that uses the
        lunchable package found here: @https://juftin.com/lunchable/interacting/
        #class-documentation to fetch and update lunchmoney transactions.

        This script should fetch all the transactions where the "payee" is one of
        the values in the list PAYEES, which is defined in config/lunchmoney_config.py.

        Once it has the transaction list it should check the amount of each
        transaction. For any transaction that has a negative amount it should update
        the transaction so that the amount is the absolute value of the negative amount

    I've commented out the orig code wherever I have changed it            
"""

# fix_negative_credits.py
import asyncio
from datetime import datetime  # Manual add, did not prompt about this
from lunchable import LunchMoney
from lunchable.models import TransactionUpdateObject # Manual add
"""from config.lunchmoney_config import PAYEES  # Ensure this module exists and is correctly configured"""
from config import lunchmoney_config as lmc

"""Manaully added"""
START_DATE = datetime.strptime(lmc.START_DATE_STR, "%m/%d/%Y")
END_DATE = datetime.strptime(lmc.END_DATE_STR, "%m/%d/%Y")
""""""

# Initialize LunchMoney client
"""lunch = LunchMoney()"""
lunch = LunchMoney(lmc.LUNCHMONEY_API_TOKEN)


async def fix_negative_credits():
    # Fetch all transactions
    """transactions = await lunch.get_transactions()"""
    transactions = lunch.get_transactions(start_date=START_DATE, end_date=END_DATE)
    
    # Filter transactions by payee in PAYEES and negative amount
    """filtered_transactions = [t for t in transactions if t.payee in PAYEES and t.amount < 0]"""
    # My fault...I gave the AI the wrong column name, and it turns out I want to change amounts greater than 0
    # meaning that credits, actually have a negative amount, and expenses have a positive amount
    filtered_transactions = [t for t in transactions if t.payee in lmc.PAYEES and not t.is_income]

    # Update each filtered transaction
    for transaction in filtered_transactions:
        """updated_amount = abs(transaction.amount)"""
        updated_amount = 0 - transaction.to_base
        """ This generated error: 'dict' object has no attribute 'model_dump'
        await lunch.update_transaction(
            transaction_id=transaction.id,
            transaction={"amount": updated_amount}
        )"""
        income_update = TransactionUpdateObject(amount=updated_amount)
        lunch.update_transaction(transaction_id=transaction.id, transaction=income_update)
        print(f"Updated transaction {transaction.id} to have amount {updated_amount}")

asyncio.run(fix_negative_credits())
