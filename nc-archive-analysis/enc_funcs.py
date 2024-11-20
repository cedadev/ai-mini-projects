from collections import defaultdict, deque

from config import regex_int


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
                                    # Special treatment for variable "shape" and "dimensions":
                                    # - we want to retain a list of lists
                                    if subkey in ("shape", "dimensions") and type(subvalue) in (list, tuple):
                                        subvalue = (tuple(subvalue),)
                                        
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
            try:
                d[key][subkey] = sorted(subvalue)
            except Exception as exc:
                print(f"[WARN] Special sort required for: {subvalue}")
                d[key][subkey] = sort_as_floats(subvalue)
        elif isinstance(subvalue, dict):
            add_sorted_lists(d[key], subkey, subvalue)
        else:
            raise Exception(f"subvalue is: {type(subvalue)}")


def finalise_encodings(encodings):
    #print("Encodings before finalisation:", encodings)
    sorted_encodings = {}

    for key, value in encodings.items():
        if isinstance(value, set):
            sorted_encodings[key] = sorted(value)
        elif isinstance(value, dict):
            add_sorted_lists(sorted_encodings, key, value)

    return sorted_encodings

