def remove_non_first_rank(df, column):
    return df[[not (x > 1) for x in df[column]]]
