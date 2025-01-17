import time
import json
import os
import requests


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


def url2json(url: str):
    if DEBUG: print(f"Downloading: {url}")
    time.sleep(WAIT)
    return requests.get(url).json()


def decode_projects(urls: list):
    projects = [url2json(url).get("title", "") for url in urls[:DEBUG_LIMIT]]
    return [proj for proj in projects if proj]


def decode_phenomena(urls: list):
    phenomena = [url2json(url).get("names", []) for url in urls[:DEBUG_LIMIT]]
    return sorted([name.get("name") for phen in phenomena for name in phen if not name.get("name", "").startswith("http")])


def decode_bbox(url: str):
    resp = url2json(url)
    return {key: resp.get(exkey, "") for key, exkey in SPATIAL_MAP.items()}


def decode_time(url: str):
    resp = url2json(url)
    return resp.get("startTime", ""), resp.get("endTime", "")


def parse(resp: dict, fields: list=REQ_FIELDS):
    records = resp["results"]
    count = len(records)
    print(f"Working on {count} records.")

    results = []

    for i, rec in enumerate(records[:DEBUG_LIMIT]):
        result = {}

        for key in REQ_FIELDS:
            # Check first for null values because lookups will fail on those
            if not rec[key] or key not in LOOKUP_FIELDS:
                value = rec[key]
            else:
                decoder = eval(f"decode_{NAME_MAP.get(key, key)}")
                value = decoder(rec[key])

            result[NAME_MAP.get(key, key)] = value

        # Add url to the dictionary
        result["url"] = URL_TMPL.format(uuid=result["uuid"])
        results.append(result)
        print(f"Processed {i+1} of {count} records.")

    return results


def main(url: str=INITIAL_URL):

    c = 1
    content = []

    while url:

        print(f"Processing: {url}")
        resp = url2json(url)
        content.extend(parse(resp))
        url = resp["next"]

        outfile = f"output_{c:03d}.json"
        with open(outfile, "w") as writer:
            json.dump(content, writer)

        print(f"Wrote: {outfile}")
        c += 1

        if DEBUG_LIMIT and c > DEBUG_LIMIT:
            break


if __name__ == "__main__":
    main()

