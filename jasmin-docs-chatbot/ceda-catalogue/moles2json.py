import time
import json
import os

if os.environ['USER'] == 'root':
    raise Exception('Do not run as root - probably run as vagrant')

os.environ['DJANGO_SETTINGS_MODULE'] = 'cedamoles_site.settings'

import django
django.setup()

from cedamoles_app.models import *


INITIAL_URL = "https://api.catalogue.ceda.ac.uk/api/v2/observations/?format=json&?publicationStatus__in=published,citable"
REQ_FIELDS  = ["uuid", "title", "abstract", "keywords", "timePeriod", "geographicExtent", "phenomena", "projects"]
LOOKUP_FIELDS = ["projects", "phenomena", "geographicExtent", "timePeriod"]
NAME_MAP = {"timePeriod": "time", "geographicExtent": "bbox"}
SPATIAL_MAP = {"east": "eastBoundLongitude", "north": "northBoundLatitude",
               "west": "westBoundLongitude", "south": "southBoundLatitude"}
URL_TMPL = "https://catalogue.ceda.ac.uk/uuid/{uuid}/"
WAIT = 1
DEBUG_LIMIT = None
DEBUG = False


def decode_projects(projects):
    return [getattr(p, "title") for p in projects.all() if getattr(p, "title")]


def decode_phenomena(phenomena):
    return [term.name for phen in phenomena.all() for term in phen.names.all() if not term.name.startswith("http")]

def decode_bbox(geographicExtent):
    try:
        return {key: getattr(geographicExtent, exkey, "") for key, exkey in SPATIAL_MAP.items()}
    except:
        print(f"[WARN] No bbox found")
        return None


def decode_time(timePeriod):
    return [str(getattr(timePeriod, tp, "")) for tp in ["startTime", "endTime"]]


def process_record(rec: Observation, fields: list=REQ_FIELDS):
    result = {}

    for key in REQ_FIELDS:
        # Check first for null values because lookups will fail on those
        if not getattr(rec, key) or key not in LOOKUP_FIELDS:
            value = getattr(rec, key)
        else:
            decoder = eval(f"decode_{NAME_MAP.get(key, key)}")
            value = decoder(getattr(rec, key))

        result[NAME_MAP.get(key, key)] = value

    # Add url to the dictionary
    result["url"] = URL_TMPL.format(uuid=result["uuid"])
    return result


def main():

    content = []
    i = 0
    chunk_size = 100
    n = Observation.objects.count()
    counter = 0

    while i < n:
       
        print(f"[INFO] Working on batch: [{i} - {i + chunk_size}]")
        obs = Observation.objects.order_by("ob_id")[i:i+chunk_size]
        for ob in obs:
            content.append(process_record(ob))

        counter += 1
        if DEBUG_LIMIT and counter > DEBUG_LIMIT:
            break

        outfile = f"outputs/output_{counter:03d}.json"
        with open(outfile, "w") as writer:
            json.dump(content, writer)

        print(f"[INFO] Wrote: {outfile}")
        i += chunk_size


if __name__ == "__main__":
    main()

