"""Gate test 2 for issue #30: untested on purpose. Never merge."""


def gate_probe(values):
    total = sum(values)
    count = len(values)
    average = total / count
    return {"total": total, "count": count, "average": average}
