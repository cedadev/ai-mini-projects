#!/usr/bin/env python

# Read in the JSON contents and transform into DataFrame(s), and write to CSV

import json
from pathlib import Path
from typing import List, Optional

import pandas as pd
import click
from netCDF4 import Dataset, num2date

from config import known_coord_vars, outdir, tmpdir, columns, LATEST

for dr in (Path(outdir), Path(tmpdir)):
    dr.mkdir(parents=True, exist_ok=True)


def transform_json_to_csv(json_path: Path, latest_only: bool = False, verbose: bool = False, overwrite: bool = False) -> Path:
    """
    Transform a JSON file to a temporary CSV file.

    Args:
        json_path (Path): The path to the JSON file.
        latest_only (bool): Flag to only include the latest records.
        verbose (bool): Flag to enable verbose output.
        overwrite (bool): Flag to overwrite existing temporary CSV files.

    Returns:
        Path: The path to the temporary CSV file.
    """
    json_id = json_path.stem
    tmpcsv = Path(tmpdir) / f"{json_id}.csv"

    if not overwrite and tmpcsv.is_file():
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


def transform(max_files: int, latest_only: bool = False, overwrite: bool = False) -> None:
    """
    Transform multiple JSON files into a single CSV file.

    Args:
        max_files (int): Maximum number of JSON files to process.
        latest_only (bool): Flag to only include the latest records.
        overwrite (bool): Flag to overwrite existing temporary CSV files.
    """
    json_files = sorted(Path(outdir).glob("*.json"))[:max_files]

    csvs = []
    for json_file in json_files:
        csvs.append(transform_json_to_csv(json_file, latest_only, overwrite))

    print(f"[INFO] Merging {len(csvs)} CSV files.")
    final_csv = Path(outdir) / "nc_inventory.csv"

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
def main(max_files: int, latest_only: bool, overwrite: bool) -> None:
    """
    Main entry point for the script.

    Args:
        max_files (int): Maximum number of JSON files to process.
        latest_only (bool): Flag to only include the latest records.
        overwrite (bool): Flag to overwrite existing temporary CSV files.
    """
    N = max_files if max_files > 0 else "ALL"
    print(f"Transforming {N} JSON files.")
    transform(max_files=max_files, latest_only=latest_only, overwrite=overwrite)
    print(f"Done!")


if __name__ == '__main__':
    main()
