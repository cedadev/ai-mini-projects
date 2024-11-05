#!/usr/bin/env python

# Read in the JSON contents and tranform into DataFrame(s), and write to CSV

import os
import json

import pandas as pd
import click
from netCDF4 import Dataset, num2date

from config import known_coord_vars, outdir, tmpdir, columns, LATEST

for dr in (outdir, tmpdir):
    if not os.path.isdir(dr):
        os.makedirs(dr)


def transform_json_to_csv(json_path, latest_only=False, verbose=False, overwrite=False):
    # Check if already written and overwrite is False
    json_id = os.path.basename(json_path).split(".")[0]
    tmpcsv = f"{tmpdir}/{json_id}.csv"

    if not overwrite and os.path.isfile(tmpcsv):
        return tmpcsv

    # Read the contents from the JSON file
    with open(json_path) as reader:
        records = json.load(reader)

    columns = ["collection", "domain", "resolution", "scenario", "ensemble_member_id", 
               "variable", "frequency", "version"]

    # Process the JSON content into rows for the DataFrame
    rows = []
    for d in records.values():
        items = d["dir"].split("/")
        
        if items[0] == "land-prob":
            # Ignore land-prob for now because they have a different number of columns
            print(f"[DEBUG] Ignoring 'land-prob': {items}")

        # Only add this record if `latest_only` is False or this is the latest!
        elif not latest_only or items[-1] == LATEST:
            rows.append(items)

        elif verbose:
            print(f"[DEBUG] Ignoring: {items}")

    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(tmpcsv, index=False)
    print(f"[INFO] Wrote temporary CSV file: {tmpcsv}")

    return tmpcsv


def transform(max_files, latest_only=False, overwrite=False):
    json_files = sorted([os.path.join(outdir, f) for f in os.listdir(outdir)])[:max_files]

    csvs = []
    for json_file in json_files:
        csvs.append(transform_json_to_csv(json_file, latest_only, overwrite))

    print(f"[INFO] Merging {len(csvs)} CSV files.")
    final_csv = f"{outdir}/nc_inventory.csv"

    dfs = [pd.read_csv(csv) for csv in csvs]
    df = pd.concat(dfs)
    print(f"Total rows to write: {len(df)}")
    df.to_csv(final_csv, index=False)
    print(f"Saved: {final_csv}")


@click.command()
@click.option('-m', '--max-files', type=int, default=-1, 
              help="Maximum number of files to convert.")
@click.option('-l', '--latest-only', is_flag=True, show_default=True, default=False,
              help="Flag to only include files under the `latest` directories.")
@click.option('-O', '--overwrite', is_flag=True, show_default=True, default=False,
              help="Flag to overwrite any previously written temporary CSV files.")
def main(max_files, latest_only, overwrite):

    N = max_files if max_files > 0 else "ALL"
    print(f"Transforming {N} JSON files.")
    transform(max_files=max_files, latest_only=latest_only, overwrite=overwrite)
    print(f"Done!")


if __name__ == '__main__':
    main()