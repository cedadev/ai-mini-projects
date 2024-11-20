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


def sort_as_floats(seq):
    "Handles cases where some values are strings."
    return [value for _, value in sorted({float(x): x for x in seq}.items())]