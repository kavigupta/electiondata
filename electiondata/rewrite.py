from abc import ABC, abstractmethod
import re

import attr


class Rewrite(ABC):
    @abstractmethod
    def applies_to(self, x):
        """
        Returns a truthy value if this rewrite rule applies to the given object.
        """
        pass

    @abstractmethod
    def rewrites_of(self, x, result_of_applies):
        """
        Returns an iterable of possible rewrites of x. The result_of_applies argument is the
            output of the applies_to method, which can contain information about how to execute
            the rewrite.
        """
        pass

    def __call__(self, x):
        result_of_applies = self.applies_to(x)
        if result_of_applies:
            return self.rewrites_of(x, result_of_applies)
        return [x]


@attr.s
class RegexRewrite(Rewrite):
    regex = attr.ib()
    replacement = attr.ib()

    def applies_to(self, x):
        return re.search(self.regex, x)

    def rewrites_of(self, x, _result_of_applies):
        return [x, re.sub(self.regex, self.replacement, x)]


@attr.s
class PointwiseRewrite(Rewrite):
    match = attr.ib()
    replacement = attr.ib()

    def applies_to(self, x):
        return x == self.match

    def rewrites_of(self, x, _result_of_applies):
        return [x, self.replacement]


@attr.s
class RewriteSystem:
    preprocessor = attr.ib()
    rewrites = attr.ib()

    def __call__(self, x):
        x = self.preprocessor(x)
        xs = [x]
        for rewrite in self.rewrites:
            xs = [y for x in xs for y in rewrite(x)]
        return xs

    def __setitem__(self, key, value):
        self.rewrites.append(PointwiseRewrite(key, value))
