"""create_category_groups.py

   This file reads in the two JSON files that were created by the prep_categories
   script and makes the API calls necessary to create lunchmoney category groups
   (as needed) and assign existing categories to those groups as defined in the
   category definition file specified by the SPENDING_GROUP_DEFINITIONS variable
   in lunchmoney_config.json


"""

import json
import os
import time
from lib.categories import update_category, create_category_group
from config.lunchmoney_config import (
    INPUT_FILES,
    CATEGORY_GROUP_DEFINITIONS,
    CATEGORY_ASSIGNMENTS,
)


def main():
    # Read the group and category structure lists written by prep_categories.py
    (groups, categories) = read_input_files(
        INPUT_FILES, CATEGORY_GROUP_DEFINITIONS, CATEGORY_ASSIGNMENTS
    )

    # Rename an existing categories that have the same name as a proposed group
    rename_categories_with_proposed_group_name(categories)

    # Create the proposed category groups
    create_proposed_category_groups(groups)


def read_json_file(file_path):
    """Reads a JSON file and returns its content."""
    with open(file_path, "r") as file:
        return json.load(file)


def read_input_files(path, group_file, category_file):
    """Reads the files created by prep_"""
    print("Reading the input files created by prep_categories.py...")
    try:
        groups = read_json_file(os.path.join(path, group_file))
        categories = read_json_file(os.path.join(path, category_file))
        return (groups, categories)

    except FileNotFoundError as e:
        print(f"Error: {e}. Unable to find expected input files.")
    except json.JSONDecodeError as e:
        print(f"Error: {e}. Found input files but the content was not as expected.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}.")
    print(
        "Please run prep_categories.py before running this script "
        "to ensure all necessary files are prepared."
    )
    exit(1)


def rename_categories_with_proposed_group_name(categories):
    """Renames existing categories that have the same name as a proposed group
    "Misc" is added to the existing category name
    """
    print("\nRenaming existing categories with proposed group names...")
    num_renamed = 0
    for cat in categories:
        if cat.get("action") == "rename":
            num_renamed += 1
            name = cat["name"]
            new_name = f"{cat['name']} Misc"
            print(f"Renaming '{name}' to '{new_name}'")
            if not update_category(cat["id"], name=new_name):
                print("Failed")
                exit(1)
            time.sleep(1)  # Adding a delay to avoid hitting rate limits
    if num_renamed == 0:
        print("...Did not find any categories that needed to be renamed")


def create_proposed_category_groups(groups):
    """Creates the proposed category groups"""
    print("\nCreating proposed category groups...")
    num_created = 0
    for group in groups:
        if "type" in group and group["type"] == "to_be_created":
            name = group["name"]
            sub_categories = None
            num_sub_cats = 0
            if "categories_to_add" in group:
                sub_categories = group["categories_to_add"]
                num_sub_cats = len(sub_categories)
            num_created += 1
            print(f"Creating group '{name}' with {num_sub_cats} sub categories")
            create_category_group(name, category_ids=sub_categories)
            time.sleep(1)  # Adding a delay to avoid hitting rate limits
    if num_created == 0:
        print("...did not find any proposed category groups that did not already exist")


if __name__ == "__main__":
    main()
