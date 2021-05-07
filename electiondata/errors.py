
import attr

@attr.s(hash=True)
class DataError(Exception):
    message = attr.ib()
    fix = attr.ib()
