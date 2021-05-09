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
