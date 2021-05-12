import attr

from collections import defaultdict


@attr.s(hash=True)
class DataError(Exception):
    message = attr.ib()
    fix = attr.ib()
    fixability = attr.ib(default=0)


_errors = set()


def error(err):
    _errors.add(err)


def check(**var_kwargs):
    errors = sorted(_errors)
    _errors.clear()
    if not errors:
        print("Success!")
        return True
    print(f"Errors ({len(errors)}): ")
    for e in errors:
        print(e.message)
    fixes = defaultdict(float)
    for e in errors:
        if e.fix is None:
            continue
        fixes[e.fix] = max(fixes[e.fix], e.fixability)
    fixes = [x for x, _ in sorted(fixes.items(), key=lambda x: -x[1])]
    if fixes:
        print("Plausible fixes: ")
        for fix in fixes:
            fix = replace_vars(fix, var_kwargs)
            print(fix)
    return False


def replace_vars(name, var_kwargs):
    if not isinstance(name, str):
        return name
    for var, repl in var_kwargs.items():
        name = name.replace("$" + var, repl)
    return name


def remove_errors(df, column, error="ERROR"):
    return df[df[column] != error]
