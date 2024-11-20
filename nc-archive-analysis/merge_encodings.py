import os
import json
from collections import defaultdict
from collections.abc import Mapping
   

import click

from config import (encdir, zpad)
from _utils import parse_to_ints, sort_as_floats


def merge_json_structures_with_deduplication(json_list):
    """
    Recursively merges a list of JSON-like structures (dictionaries/lists).
    Arrays at the same keys are concatenated with duplicates removed,
    and dictionaries are merged recursively.

    Args:
        json_list (list): List of JSON-like structures to merge.

    Returns:
        dict: Merged JSON-like structure with deduplicated arrays.
    """
    def combine_without_duplicates(*seqs):
        """Helper function to remove duplicates. Avoiding sets because contents
        might be (unhashable) lists."""
        result = seqs[0]
        for seq in seqs[1:]:
            for item in seq:
                if item not in result:
                    result.append(item)

        return result

    def merge_dicts(d1, d2):
        """Helper function to merge two dictionaries."""
        for key, value in d2.items():
            if key in d1:
                if isinstance(d1[key], list) and isinstance(value, list):
                    # Merge lists and remove duplicates
                    d1[key] = combine_without_duplicates(d1[key], value) #list(set(d1[key] + value))
                elif isinstance(d1[key], dict) and isinstance(value, dict):
                    merge_dicts(d1[key], value)
                else:
                    # Replace non-dict, non-list types
                    d1[key] = value
            else:
                d1[key] = value
        return d1

    merged = {}
    for json_data in json_list:
        if not isinstance(json_data, Mapping):
            raise ValueError("Each item in json_list must be a dictionary.")
        merged = merge_dicts(merged, json_data)

    # Ensure all lists are sorted for consistency (optional)
    def sort_lists(data):
        if isinstance(data, dict):
            return {k: sort_lists(v) for k, v in data.items()}
        elif isinstance(data, list):
            try:
                s_data = sorted(data)
            except Exception as exc:
                s_data = sort_as_floats(data)
            return s_data
        else:
            return data

    return sort_lists(merged)


def flatten_json(nested_json, parent_key='', sep='.'):
    """
    Recursively flattens a nested JSON object into a single-layer dictionary.
    
    Args:
        nested_json (dict): The JSON object to flatten.
        parent_key (str): The base key for recursion (used internally).
        sep (str): The separator used to join keys.

    Returns:
        dict: A flattened JSON dictionary.
    """
    items = []
    for k, v in nested_json.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def merge(batches):

    print(f"[INFO] Running for batches: {batches}")
    encodings = defaultdict(set)

    jsons = []
    for batch_number in batches:
        infile = f"{encdir}/{batch_number:0{zpad}}.json"

        with open(infile) as reader:
            jsons.append(json.load(reader))

        print(f"Loaded: {infile}")

    merged_encodings = merge_json_structures_with_deduplication(jsons)

    # Now flatten the merged encodings
    merged_encodings = flatten_json(merged_encodings)
    encfile = f"{encdir}/{batches[0]:0{zpad}}-{batches[-1]:0{zpad}}.json"

    with open(encfile, "w") as writer:
        json.dump(merged_encodings, writer, indent=4)

    print(f"Wrote: {encfile}")


@click.command()
@click.option("-b", "--batches", type=str, help="Batch number as '1', '1,3,5' or '1-3,6'")
def main(batches):
    batches = parse_to_ints(batches)
    merge(batches)


if __name__ == '__main__':
    main()