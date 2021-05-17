import copy
import numbers
import warnings

import numpy as np
import pandas as pd

import attr

from .aggregator import Aggregator
from .errors import DataError, error, check
from .utils import set_without_nans, render_row


@attr.s
class DuplicationResolver:
    applies = attr.ib()
    which_source = attr.ib()
    force_value = attr.ib(default=None)


def merge(
    *,
    by_source,
    join_columns,
    ignore_duplication,
    resolvers,
    checksum=None,
    ignore_discrepancies=0.01,
):

    by_source = copy.deepcopy(by_source)

    if checksum is not None:
        checksums = {source: checksum(by_source[source]) for source in by_source}

    should_be_unique = (
        set(list(by_source.values())[0]) - set(join_columns) - set(ignore_duplication)
    )

    extra_cols = [(col, source) for col in should_be_unique for source in by_source]

    for col, source in extra_cols:
        by_source[source][col, source] = by_source[source][col]

    all_data = pd.concat(list(by_source.values()))

    def set_collapse_similar(values):
        values = set(values)
        if len(values) == 1:
            return values
        if not all(isinstance(v, numbers.Number) for v in values):
            return values
        spread = max(values) - min(values)
        if min(values) == 0 or spread / min(values) > ignore_discrepancies / 100:
            return values
        return {np.mean(list(values))}

    agg = Aggregator(
        grouped_columns=join_columns,
        aggregation_functions={
            **ignore_duplication,
            **{col: set for col in all_data if col in should_be_unique},
            **{cs: set_without_nans for cs in extra_cols},
        },
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = agg(all_data)

    kept_cols = [x for x in df if x not in extra_cols]

    new_table = []
    for _, row in df.iterrows():
        row = row.copy()
        stringify = render_row(row)

        sources = {r.which_source for r in resolvers if r.applies(row)}
        if len(sources) > 1:
            error(
                DataError(f"Multiple disagreeing resolvers apply to {stringify}", None)
            )
            continue
        if len(sources) == 1:
            [source] = sources
            for col in should_be_unique:
                if not row[col, source]:
                    force_values = {
                        r.force_value
                        for r in resolvers
                        if r.applies(row) and r.force_value is not None
                    }
                    if len(force_values) == 1:
                        row[col] = force_values
                    else:
                        error(DataError(f"Invalid entry chosen for {stringify}", None))
                    continue
                row[col] = row[col, source]
        if any(len(row[col]) > 1 for col in should_be_unique):
            error_message = f"Disagreement on values in {stringify}"
            if checksum is not None:
                error_message += "; checksums"
                for source in by_source:
                    mask = 1
                    for c in checksum.grouped_columns:
                        if c in join_columns:
                            mask = mask & (checksums[source][c] == row[c])
                        else:
                            mask = mask & checksums[source][c].apply(
                                lambda x: {x} == row[c]
                            )
                    rendered_checkpoint = render_row(checksums[source][mask].iloc[0])
                    padded_source = source + " " * (
                        max(len(s) for s in by_source) - len(source)
                    )
                    error_message += f"\n    {padded_source}={rendered_checkpoint}"
            error(DataError(error_message, None))
            continue
        row = row[kept_cols]
        for col in should_be_unique:
            [row[col]] = row[col]
        new_table.append(row)

    if not check():
        raise RuntimeError("Erorr in merge: see above for details")

    new_table = pd.DataFrame(new_table)
    return new_table
