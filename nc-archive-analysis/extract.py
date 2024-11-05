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
import json
from collections import defaultdict, deque
    

import click
from netCDF4 import Dataset, num2date

from config import (known_coord_vars, batch_size, zpad, workdir, 
                    outdir, encdir, regex_int)

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


def get_batch(batch_number, batch_size=batch_size):
    s = (batch_number - 1) * batch_size
    e = s + batch_size
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


def lookup_item(lookup, x):
    # Try dictionary lookup
    if isinstance(x, dict) and lookup in x:
        return x[lookup]

    # Try list index lookup
    if regex_int.match(lookup) and len(x) > int(lookup):
        return [x[int(lookup)]]
    
    return []

def merge_dicts(d1, key, d2):
    "Merge each sub-key as an encoding with each sub-value as a new set."
    if key not in d1 and not d1.get(key, None):
        d1[key] = defaultdict(set)

#    print(d2, type(d2), key, d2.get(key))
    for subkey, subvalue in d2.get(key, {}).items():
        d1[key].setdefault(subkey, set())
        d1[key][subkey].add(subvalue)


def update_encodings(encodings, d):
    "Add content of dict `d` to encodings dict. Returns None."
    # Simple list encodings
    enc_types = [
        # scalars
        (lambda x: [x], ["nc_format"]),
        # lists - None
        (lambda x: x, ["data.time.0", "data.time.-1"]),
        # dict keys
        (lambda x: x.keys(), ["dims"]),
        # dict expansions - depth: 1
        ("merge_dicts", ["global_attrs"]),
        # dict expansions - depth: 2
        ("merge_dicts_depth_2", ["variables"])
    ]

    for formatter, encs in enc_types:
        for enc in encs:
            # If "merge_full_dict", then use that
            if formatter == "merge_dicts":
                merge_dicts(encodings, enc, d)
            elif formatter == "merge_dicts_depth_2":
                if not encodings[enc]:
                    encodings[enc] = {}

                for key, value in d.get(enc, {}).items():
                    if not isinstance(value, dict):
                        encodings[enc].setdefault(key, set())
                        if type(value) in (int, float, str, bytes):
                            encodings[enc][key].add(value)
                        else:
                            encodings[enc][key].update(value)
                    else:
                        if not encodings[enc].get(key, {}):
                            encodings[enc][key] = {}

                        for subkey, subvalue in value.items():
                            if not isinstance(subvalue, dict):
                                encodings[enc][key].setdefault(subkey, set())
                                if type(subvalue) in (int, float, str, bytes):
                                    encodings[enc][key][subkey].add(subvalue)
                                else:
                                    encodings[enc][key][subkey].update(subvalue)
                            else:
                                merge_dicts(encodings[enc][key], subkey, d[enc][key])
                            
            else:
                # if "." found in list then recursively access it
                lookups = deque(enc.split("."))
                values = None

                while lookups:
                    lookup = lookups.popleft()
                    values = lookup_item(lookup, values) if values is not None else lookup_item(lookup, d)

                    if not values:
                        break
                    
                values = formatter(values)
                encodings[enc].update(set(values))



def add_sorted_lists(d, key, value):
    d[key] = {}

    for subkey, subvalue in value.items():
        if isinstance(subvalue, set):
            d[key][subkey] = sorted(subvalue)
        elif isinstance(subvalue, dict):
            add_sorted_lists(d[key], subkey, subvalue)
        else:
            raise Exception(f"subvalue is: {type(subvalue)}")


def finalise_encodings(encodings):
    print("Encodings before finalisation:", encodings)
    sorted_encodings = {}

    for key, value in encodings.items():
        if isinstance(value, set):
            sorted_encodings[key] = sorted(value)
        elif isinstance(value, dict):
            add_sorted_lists(sorted_encodings, key, value)

    return sorted_encodings


def extract(batches, batch_size=batch_size):

    print(f"[INFO] Running for batches: {batches}")

    for batch_number in batches:
        batch_dict = {}
        encodings = defaultdict(set)

        for f in get_batch(batch_number, batch_size):
            if f in lost_files:
                print(f"[WARN] Lost file ignored: {f}")
                continue

            try:
                print(f"[INFO] {f}")
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


def parse_to_ints(s):
    resp = set()
    for item in s.split():
        for part in item.split(","):
            if "-" in part:
                s, e = [int(i) for i in part.split("-")]
                ints = range(s, e + 1)
            else:
                ints = [int(part)]
            resp = resp.union(ints)

    return sorted(resp)


@click.command()
@click.option("-b", "--batches", type=str, help="Batch number as '1', '1,3,5' or '1-3,6'")
@click.option("-s", "--batch-size", type=int, default=batch_size, help="Number of files per batch.")
def main(batches, batch_size=batch_size):
    batches = parse_to_ints(batches)
    extract(batches, batch_size=batch_size)


if __name__ == '__main__':
    main()