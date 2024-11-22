import os
import json
from collections import defaultdict
from collections.abc import Mapping
   

import click

from config import (encdir, zpad)
from _utils import combine_without_duplicates, unique


def process(flat_json):
    print(f"Processing file: {flat_json}")
    with open(flat_json) as reader:
        content = json.load(reader)

    keys = list(content.keys())
    l_key = max([(len(key), key) for key in keys])[1]
    all_values = [v for value in content.values() for v in value]
    unique_values = unique([v for v in all_values])
    l_value = max([(len(str(value)), str(value)) for value in unique_values])[1]

    print(f"Found: {len(keys)} items.")
    print(f"Found: {len(all_values)} values.")
    print(f"Found: {len(unique_values)} unique values.")
    print(f"Largest key: {l_key} ({len(l_key)})")
    print(f"Largest value: {l_value[:300]}... ({len(l_value)})")

    # Prepare the CVs - ignore "data.<coord>.0" and "data.<coord>.-1" initially
    simple_keys = sorted(set([key.split(".")[-1] for key in keys if key.split(".")[-1] not in ("0", "-1")]))
    cvs = {simple_key: [] for simple_key in simple_keys}

    def merge_content(simple_key, seq2):
        seq1 = cvs[simple_key]
        cvs[simple_key] = combine_without_duplicates(seq1, seq2)

    # Group all keys into common simple keys
    [merge_content(simple_key, values) for simple_key in simple_keys
     for key, values in content.items()
     if key.split(".")[-1] == simple_key]
    
    # Add in the "data.<coord>.0" and "data.<coord>.-1" values - merging them into:
    # - "datetimes", "data_ints", "data_floats"
    def consolidate_coord_values(coord_key):
        cvs[f"{coord_key}_values"] = sorted(set([dt for tkey in [f"data.{coord_key}.0", f"data.{coord_key}.-1"] for dt in content[tkey]]))

    consolidate_coord_values("time")

    coords = set([coord.split(".")[1] for coord in keys 
                  if coord.startswith("data.") 
                  and coord.split(".")[-1] in ("0", "-1")
                  and not coord.startswith("data.time.")])
    
    for coord_key in coords:
        consolidate_coord_values(coord_key)

    cv_path = "cvs.json"

    with open(cv_path, "w") as writer:
        json.dump(cvs, writer, indent=4, sort_keys=True)

    print(f"\nWrote: {cv_path}")
    



@click.command()
@click.option("-f", "--flat-json", type=str, required=True, help="Path to the flattened JSON file of vocabs.")
def main(flat_json):
    if not flat_json.endswith(".json"):
        flat_json = flat_json + ".json"

    for fpath in (flat_json, os.path.join(encdir, flat_json)):
        if os.path.isfile(fpath):
            break
    else:
        print(f"[ERROR] No file found at: {flat_json}")
        return
    
    process(fpath)


if __name__ == '__main__':
    main()