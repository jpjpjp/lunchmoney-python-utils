""" prep_categories.py

    This script reads in a csv file that defines a set of category groups to be
    configured in LunchMoney.

    It reads in the proposed definitions and existing LunchMoney categories and outputs
    some statistics describing changes that need to take place to set the categories up

    Finally, it outputs two json files that can be read as input to the script
    create_category_groups which will implement the changes proposed by this script
"""

import json
import os
import pandas as pd
from lib.categories import get_categories
from config.lunchmoney_config import (
    INPUT_FILES,
    SPENDING_GROUP_DEFINITIONS,
    CATEGORY_GROUP_DEFINITIONS,
    CATEGORY_ASSIGNEMENTS
)


# Function to read the proposed spending groups and categories from a CSV
def read_spending_groups(path: str, filename: str) -> pd.DataFrame:
    path_to_filename = os.path.join(path, filename)
    return pd.read_csv(path_to_filename)


# Main script execution
if __name__ == "__main__":
    # Read proposed spending groups and categories
    spending_groups_df = read_spending_groups("config", SPENDING_GROUP_DEFINITIONS)
    # Ensure that no category is assigned to more than one group
    all_values = (
        spending_groups_df.values.flatten().tolist()
        + spending_groups_df.columns.tolist()
    )
    value_counts = pd.Series(all_values).value_counts()
    duplicated_values = value_counts[value_counts > 1]
    if not duplicated_values.empty:
        print("Duplicated values found:")
        for value in duplicated_values.index:
            print(f" - {value}")
        print(
            "Warning: Each value should only exist once as a column name and up to once as a value in its column."
        )
        exit()
    # Fetch existing categories and convert to list of dicts
    existing_categories = [
        {
            "name": cat.name,
            "id": cat.id,
            "is_group": cat.is_group,
            "group_id": cat.group_id,
        }
        for cat in get_categories()
    ]

    # Build a list of proposed_group objects which will be used to create
    # new category groups and assign the appropriate categories to them
    proposed_groups = set(spending_groups_df.columns)
    proposed_group_objects = []
    remaining_categories = []
    for category in existing_categories:
        if category["name"] in proposed_groups:
            if category["is_group"]:
                # Proposed group already exists no need to create it
                category["type"] = "existing"
                proposed_group_objects.append(category)
                proposed_groups.remove(category["name"])
            else:
                # A non-group category with the same name as a group exists
                # The category will need to be renamed, and a new group created
                category["action"] = "rename"
                remaining_categories.append(category)
        elif category["is_group"]:
            # An existing category group, not in the proposed list, was found
            # This will be essentially ignored
            category["type"] = "existing"
            proposed_group_objects.append(category)
        else:
            # Otherwise this is a "regular category"
            # It will be evaluated to see if it belongs in one of the proposed groups
            remaining_categories.append(category)

    # For the remaining proposed group names, create a set of objects to define
    # the tasks needed to get them set up properly
    for name in proposed_groups:
        proposed_group_objects.append({"name": name, "type": "to_be_created"})

    # Evaluate the remaining categories to be put in one of the proposed groups
    for category in remaining_categories:
        category["in_group"] = False
        proposed_group = None
        if "action" in category and category["action"] == "rename":
            # Existing categories with the same name as a proposed group will
            # be renamed and then later added to the group once it is created
            proposed_group = category["name"]
        else:
            for col in spending_groups_df.columns:
                if category["name"] in spending_groups_df[col].values.tolist():
                    proposed_group = col
                    break
        if proposed_group:
            # This category belongs in one of the proposed_groups, add it to the
            # list of category ids to be updated with the group id once it's created
            category["in_group"] = True
            group_obj = next(
                (
                    item
                    for item in proposed_group_objects
                    if item["name"] == proposed_group
                ),
                None,
            )
            if group_obj:
                if "categories_to_add" not in group_obj:
                    group_obj["categories_to_add"] = []
                group_obj["categories_to_add"].append(category["id"])
            else:
                print(f'Category:{category["name"]} found for group:{proposed_group}')
                print("But no proposed group object exists!   This should not happen!")
                exit(1)

    # Summarize next steps
    # Display existing category groups to remain unmodified
    existing_group_count = sum(
        1 for cat in proposed_group_objects if cat.get("type") == "existing"
    )
    existing_group_names = [
        cat["name"] for cat in proposed_group_objects if cat.get("type") == "existing"
    ]
    print(
        f"Found {existing_group_count} existing category groups that will not be modified:"
    )
    print(f"Existing category groups: {existing_group_names}")

    # Display the existing categories who's names collide with proposed groups
    rename_cat_count = sum(
        1 for cat in existing_categories if cat.get("action") == "rename"
    )
    print(
        f"\nFound {rename_cat_count} existing categories with the same name as proposed groups:"
    )
    for cat in existing_categories:
        if cat.get("action") == "rename":
            print(f"Will rename '{cat['name']}' to '{cat['name']} Misc'")

    # Display the new category groups that will be created
    new_group_count = sum(
        1 for cat in proposed_group_objects if cat.get("type") == "to_be_created"
    )
    new_group_details = [
        (cat["name"], len(cat.get("categories_to_add", [])))
        for cat in proposed_group_objects
        if cat.get("type") == "to_be_created"
    ]
    print(f"\nNumber of proposed new category groups: {new_group_count}")
    print(
        "Proposed new category groups and the number of existing categories to be added to them:"
    )
    for name, count in new_group_details:
        print(f"  {name}: {count}")

    # Finally display the categories that will not be modified as part of the update
    not_in_group_nor_renamed_names = [
        cat["name"]
        for cat in existing_categories
        if not cat["is_group"]
        and not cat["in_group"]
        and not cat["group_id"]
        and "action" not in cat
    ]
    print(
        f"\n{len(not_in_group_nor_renamed_names)} existing categories are neither in a "
        f"group or have a proposed group name: {not_in_group_nor_renamed_names}"
    )
    print("These will not be modified")

    # Write proposed_group_objects to a file in the INPUT_FILES directory
    with open(os.path.join(INPUT_FILES, CATEGORY_GROUP_DEFINITIONS), "w") as file:
        print(f"\nWriting proposed category group object to {file.name}")
        json.dump(proposed_group_objects, file, indent=4)

    # Write existing_categories to a file in the INPUT_FILES directory
    with open(os.path.join(INPUT_FILES, CATEGORY_ASSIGNEMENTS), "w") as file:
        print(f"Writing proposed category assignements to {file.name}")
        json.dump(existing_categories, file, indent=4)

    print('If everything looks good run create_category_groups.py')
