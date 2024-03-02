"""list_unused_tags.py

    This program prints out a list of any lunchmoney tags that are not associated
    with any transactions
"""

import sys

# import os

from config import lunchmoney_config as lmc
from lunchable import LunchMoney
from lunchable.models import TransactionUpdateObject
from typing import Any, Dict


def main():
    """
    Iterates through all tags and checks if they have transactions
    """
    # Since we are working with both the tags and transactions APIs we'll initialize
    # lunchable here
    lunch = LunchMoney(access_token=lmc.LUNCHMONEY_API_TOKEN)
    tags = lunch.get_tags()

    for tag in tags:
        trans = lunch.get_transactions(
            tag_id=tag.id, start_date="2000-01-01", end_date="3000-01-01"
        )
        if len(trans) == 0:
            print(f"There are {len(trans)} transactions with the tag '{tag.name}'")
            if tag in lmc.VALID_TAGS:
                print('--Unexpected?')

if __name__ == "__main__":
    sys.exit(main())
