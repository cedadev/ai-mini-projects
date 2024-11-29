import os
import json
from random import randint

import click

from config import (outdir, zpad)
from _utils import parse_to_ints, sort_as_floats, combine_without_duplicates
TOTAL_FILES = 710
DEFAULT_N_RECS = 5
DEFAULT_OUTPUT = "example_records.json"


def gather_random_records(output_path=DEFAULT_OUTPUT, n_recs=DEFAULT_N_RECS):
    files_to_use = list(range(10, TOTAL_FILES + 1, TOTAL_FILES // n_recs))
    print(f"Extracting records from files numbered: {files_to_use}")
    records = {}

    for i in files_to_use:
        infile = f"{outdir}/{i:0{zpad}}.json"
        data = json.load(open(infile))
        n_recs = len(data)
        idx = randint(0, n_recs - 1)
        k, v = [(k, v) for (k, v) in data.items()][idx]
        records[k] = v

    with open(output_path, "w") as writer:
        json.dump(records, writer, indent=4)

    print(f"Wrote: {output_path}")


@click.command()
@click.option("-o", "--output-path", default=DEFAULT_OUTPUT, type=str, help="Output path.")
@click.option("-n", "--nrecs", default=DEFAULT_N_RECS, type=int, help="Number of records to use.")
def main(output_path=DEFAULT_OUTPUT, nrecs=DEFAULT_N_RECS):
    gather_random_records(output_path, nrecs)


if __name__ == '__main__':
    main()