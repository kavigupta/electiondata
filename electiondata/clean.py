import attr


@attr.s
class CleanString:
    case_sensitive = attr.ib(default=False)

    def __call__(self, x):
        x = str(x)
        x = x.strip()
        if not self.case_sensitive:
            x = x.lower()
        return x
