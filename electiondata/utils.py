def remove_non_first_rank(df, column):
    return df[[not (x > 1) for x in df[column]]]


def columns_for_variable(df, *, values_are, columns_for):
    return (
        df.pivot_table(
            index=list(x for x in df if x not in {values_are, columns_for}),
            columns=columns_for,
            fill_value=0,
        )
        .reset_index()
        .sort_index()
    )


def stringify_fips(df, fips_column):
    df[fips_column] = df[fips_column].apply(lambda x: f"{x:05d}")


def set_without_nans(xs):
    return {x for x in xs if x == x}


def render_row(row):
    return "(" + ", ".join(f"{k}={v}" for k, v in zip(row.index, row.values)) + ")"
