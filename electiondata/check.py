from .errors import DataError

_errors = set()


def error(err):
    _errors.add(err)


def check(**var_kwargs):
    errors = sorted(_errors)
    _errors.clear()
    if not errors:
        print("Success!")
        return True
    print("Errors: ")
    for e in errors:
        print(e.message)
    fixes = {e.fix for e in errors if e.fix != None}
    if fixes:
        print("Plausible fixes: ")
        for fix in fixes:
            fix = replace_vars(fix, var_kwargs)
            print(fix)
    return False


def replace_vars(name, var_kwargs):
    for var, repl in var_kwargs.items():
        name = name.replace("$" + var, repl)
    return name
