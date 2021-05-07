def run_on_df(fn, df, *columns):
    return df.apply(lambda row: fn(*[row[c] for c in columns]), axis=1)


def remove_bad(df, column):
    return df[run_on_df(lambda col: not col.startswith("BAD:"), df, column)]


def remove_non_first_rank(df, column):
    return df[[not (x > 1) for x in df[column]]]
