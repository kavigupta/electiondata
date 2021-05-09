import functools

import attr

from .errors import DataError, check, error


@attr.s
class Aggregator:
    grouped_columns = attr.ib(kw_only=True)
    aggregation_functions = attr.ib(kw_only=True, default=attr.Factory(dict))
    removed_columns = attr.ib(kw_only=True, default=attr.Factory(list))

    @property
    def kept_columns(self):
        return self.grouped_columns + list(self.aggregation_functions)

    def unique_columns(self, df):
        return [x for x in df if x not in self.kept_columns + self.removed_columns]

    def __call__(self, df, **var_kwargs):
        original_df = df

        unique_columns = self.unique_columns(df)
        df = df[self.kept_columns + unique_columns]
        df = (
            df.groupby(self.grouped_columns)
            .agg(
                {
                    **self.aggregation_functions,
                    **{
                        unicol: functools.partial(enforce_unique, unicol)
                        for unicol in unique_columns
                    },
                }
            )
            .reset_index()
        )

        works = check(**var_kwargs)
        if not works:
            return original_df

        return df


def enforce_unique(column, values):
    values = [x if x == x else "nan" for x in values]
    values = list(set(values))

    if len(values) > 1:
        error(
            DataError(
                f"Non-unique values in aggregation of {column}: {values}",
                f"$var_name.removed_columns.append({column!r})",
            )
        )
    return values[0]
