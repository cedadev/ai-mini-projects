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


def combine_without_duplicates(*seqs):
    """Helper function to remove duplicates. Avoiding sets because contents
    might be (unhashable) lists."""
    result = seqs[0]
    for seq in seqs[1:]:
        for item in seq:
            if item not in result:
                result.append(item)

    return result


def unique(seq):
    """Remove any duplicate entries, without using sets which cannot include
    (unhashable) lists."""
    result = []
    for item in seq:
        if item not in result:
            result.append(item)

    return result