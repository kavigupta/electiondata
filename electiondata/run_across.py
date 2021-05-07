
from .errors import DataError

def check(fn, *arguments, **var_kwargs):
    errors = set()
    for args in zip(*arguments):
        try:
            fn(*args)
        except DataError as e:
            errors.add(e)
    if not errors:
        print("Success!")
        return
    print("Errors: ")
    errors = sorted(errors)
    for e in errors:
        print(e.message)
    print("Plausible fixes: ")
    for e in errors:
        if e.fix is not None:
            fix = replace_vars(e.fix, var_kwargs)
            print(fix)

def replace_vars(name, var_kwargs):
    for var, repl in var_kwargs.items():
        name = name.replace("$" + var, repl)
    return name

def run_on_df(fn, df, *columns):
    return df.apply(lambda row: fn(*[row[c] for c in columns]), axis=1)

def remove_bad(df, column):
    return df[run_on_df(lambda col: not col.startswith("BAD:"), df, column)]
