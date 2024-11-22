#!/usr/bin/env python
"""
extract.py
==========

Reads NetCDF files and captures their metadata in a dictionary structure.

Generates two types of output:
- Outputs the dictionaries in batches within JSON files.
- Outputs all values found in each metadata category, as a JSON file.

"""

import os
import random
import json
from collections import defaultdict
    

import click
from netCDF4 import Dataset, num2date

from _utils import parse_to_ints, sort_as_floats
from config import (known_coord_vars, batch_size, zpad, workdir, 
                    outdir, encdir)
from enc_funcs import update_encodings, finalise_encodings

#outdir="outputs"

for dr in (workdir, outdir, encdir):
    if not os.path.isdir(dr):
        os.makedirs(dr)


file_list_file = f"{workdir}/filelist-cpm-gpm-prob-rcm.txt"
#file_list_file = "random-filelist.txt"
filelist = open(file_list_file).read().strip().split()
#filelist = ["/badc/ukcp18/data/land-gcm/uk/60km/rcp26/01/uas/day/v20200302/uas_rcp26_land-gcm_uk_60km_01_day_20191201-20291130.nc"]

lost_files_file = f"{workdir}/lost-files.txt"
lost_files = open(lost_files_file).read().strip().split()


def get_name_parts(f, basedir="/badc/ukcp18/data/"):
    dr, fname = os.path.split(f)
    fbase, ext = os.path.splitext(fname)

    return {"dir": dr.replace(basedir, ""), 
            "fbase": fbase,
            "ext": ext.lstrip(".")}


def get_times(tvar):
    s, e = [num2date(tvar[idx], tvar.units).strftime("%Y-%m-%dT%H:%M:%S") for idx in (0, -1)]
    return s, e


def get_limits(v):
    return [float(v[idx]) for idx in (0, -1)]


def coerce_values(d):
    for key, value in d.items():
        vcls = value.__class__.__name__
        if vcls.startswith("float"):
            d[key] = float(value)
        elif vcls.startswith("int"):
            d[key] = int(value)

    return d


def get_batch(batch_number, batch_size=batch_size, random_sample=-1):
    s = (batch_number - 1) * batch_size
    e = s + batch_size

    if random_sample > 0:
        return [filelist[i] for i in random.sample(range(s, e + 1), random_sample)]
    else:
        return filelist[s:e]


def get_file_dict(f):
    d = get_name_parts(f)
    ds = Dataset(f)

    d["nc_format"] = ds.file_format
    d["dims"] = {d.name:d.size for d in ds.dimensions.values()}
    d["variables"] = {v.name: {"dtype": v.dtype.name, 
                               "dimensions": v.dimensions, 
                               "size": int(v.size), 
                               "shape": tuple(int(i) for i in v.shape), 
                               "attrs": coerce_values(v.__dict__)} for v in ds.variables.values()}
    
    d["global_attrs"] = coerce_values(ds.__dict__)    
    d["data"] = {v.name: get_limits(v) for v in ds.variables.values() if v.name in known_coord_vars and len(v.shape) < 2}

    times = get_times(ds["time"]) if "time" in ds.variables else None
    if times is not None:
        d["data"].update({"time": times})

    return d


def extract(batches, batch_size=batch_size, random_sample=-1):

    print(f"[INFO] Running for batches: {batches}")

    for batch_number in batches:
        batch_dict = {}
        encodings = defaultdict(set)

        for f in get_batch(batch_number, batch_size, random_sample):
            if f in lost_files:
                print(f"[WARN] Lost file ignored: {f}")
                continue

            print(f"[INFO] Processing: {f}")
            try:
                d = get_file_dict(f)
                key = f"{d['fbase']}:{d['dir'].split('/')[-1]}"
                batch_dict[key] = d

            except Exception as exc:
                print(f"[ERROR] Could not parse: {f}")

            update_encodings(encodings, d)

        if not batch_dict:
            print("[INFO] Stopping as no files found in batch.")
            break

        # Write the metadata in the files
        outfile = f"{outdir}/{batch_number:0{zpad}}.json"

        with open(outfile, "w") as writer:
            json.dump(batch_dict, writer, indent=4)

        print(f"Wrote: {outfile}")

        # Write the metadata encodings file
        encodings = finalise_encodings(encodings)
        encfile = f"{encdir}/{batch_number:0{zpad}}.json"

        with open(encfile, "w") as writer:
            json.dump(encodings, writer, indent=4)

        print(f"Wrote: {encfile}")



@click.command()
@click.option("-b", "--batches", type=str, help="Batch number as '1', '1,3,5' or '1-3,6'")
@click.option("-s", "--batch-size", type=int, default=batch_size, help="Number of files per batch.")
@click.option("-r", "--random-sample", type=int, default=-1, help="Randomly select this many per batch.")
def main(batches, batch_size=batch_size, random_sample=-1):
    batches = parse_to_ints(batches)
    extract(batches, batch_size=batch_size, random_sample=random_sample)


if __name__ == '__main__':
    main()