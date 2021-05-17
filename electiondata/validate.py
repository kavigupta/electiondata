from collections import Counter

from .errors import DataError, error, check
from .utils import render_row


def validate_same(
    df1,
    df2,
    *,
    key_cols,
    check_cols,
    close_enough_dist=0.01,
    ignore_missing=((), ()),
    ignore_discrepancies=lambda k: False,
):
    def grab_key_range(df):
        from_keys = {tuple(r[key_cols]): r for _, r in df.iterrows()}
        counts = Counter(tuple(r) for _, r in df[key_cols].iterrows())
        for v, c in counts.items():
            if c >= 2:
                error(DataError(f"Duplicate values for key columns: {v}", None))
        return {k: from_keys[k] for k in counts if counts[k] == 1}

    def close_enough(x, y):
        if x == y:
            return True
        if abs(x - y) / (1 + min(x, y)) < close_enough_dist:
            return True
        return False

    v1 = grab_key_range(df1)
    v2 = grab_key_range(df2)

    for v in set(v2) - set(v1) - set(ignore_missing[0]):
        error(DataError(f"Entry appears in df2 but not df1: {v}", None))
    for v in set(v1) - set(v2) - set(ignore_missing[1]):
        error(DataError(f"Entry appears in df1 but not df2: {v}", None))

    vcommon = set(v1) & set(v2)
    for k in vcommon:
        if ignore_discrepancies(k):
            continue
        r1, r2 = v1[k], v2[k]
        if any(not close_enough(r1[c], r2[c]) for c in check_cols):
            error(
                DataError(
                    f"Discrepancy for key {k}: {render_row(r1[check_cols])} != {render_row(r2[check_cols])}",
                    None,
                )
            )
    return check()
