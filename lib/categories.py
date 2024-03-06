"""categories.py

   This module provides functions for managing lunchmoney categories via the
   /categories API accessed by the lunchable client

   For apps that manipulate only categories, this module can completely encapsulate
   access to the lunchable client and only requires that the LunchMoney API token
   be set in lunchmoney_config.py.

   Apps that access multiple lunchmoney APIs can pass in a pre-intialized lunchable
   client for API access.
"""

from lunchable import LunchMoney
from config import lunchmoney_config as lmc

private_lunch = None
categories = None


def init_lunchable(token):
    global private_lunch
    if private_lunch is None:
        private_lunch = LunchMoney(access_token=token)
    return private_lunch


def get_categories(lunch=None):
    """If it hasn't been done yet, get's the categories from lunchmoney
    and stores them in the global variable categories
    """
    global categories
    if categories is None:
        if lunch is None:
            lunch = init_lunchable(lmc.LUNCHMONEY_API_TOKEN)
        categories = lunch.get_categories()
    return categories


def get_category_id_by_name(name, lunch=None):
    """Returns the category id for the category with the specified name"""
    categories = get_categories(lunch)
    category = next(
        (category for category in categories if category.name == name), None
    )
    return category.id if category else None


def update_category(
    id,
    name=None,
    description=None,
    is_income=None,
    exclude_from_budget=None,
    exclude_from_totals=None,
    group_id=None,
    archived=None,
    lunch=None,
):
    """Updated the category with id, to have whatever new values are
    in set in the transaction_fields object
    """
    if lunch is None:
        lunch = init_lunchable(lmc.LUNCHMONEY_API_TOKEN)
    return lunch.update_category(
        id,
        name=name,
        description=description,
        is_income=is_income,
        exclude_from_budget=exclude_from_budget,
        exclude_from_totals=exclude_from_totals,
        group_id=group_id,
        archived=archived,
    )


def create_category_group(
    name,
    description=None,
    is_income=None,
    exclude_from_budget=None,
    exclude_from_totals=None,
    category_ids=None,
    new_categories=None,
    lunch=None
):
    """Creates a new category group"""
    if lunch is None:
        lunch = init_lunchable(lmc.LUNCHMONEY_API_TOKEN)
    return lunch.insert_category_group(
        name,
        description=description,
        is_income=is_income,
        exclude_from_budget=exclude_from_budget,
        exclude_from_totals=exclude_from_totals,
        category_ids=category_ids,
        new_categories=None,
    )
