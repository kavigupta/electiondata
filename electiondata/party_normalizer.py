import attr

from .errors import DataError, error
from .clean import CleanString
from .matcher import UniqueMatch, DictionaryMap, BlackBoxMap, Dispatcher
from .rewrite import RewriteSystem


def usa_party_normalizer(candidate_column):
    independent_dems = ["bernie sanders", "bernard sanders", "angus king"]

    def is_independent_dem(candidate):
        candidate = str(candidate)
        candidate = candidate.lower().split()
        return any(
            set(dem.split()) - set(candidate) == set() for dem in independent_dems
        )

    party_match = UniqueMatch(
        RewriteSystem(CleanString(), []),
        {
            "major parties": DictionaryMap(
                {"democratic": "DEM", "republican": "GOP"},
            ),
            "minor parties": Dispatcher(
                lambda x: x[candidate_column],
                lambda candidate: BlackBoxMap(lambda x, _: True, lambda x, _: "DEM")
                if is_independent_dem(candidate)
                else BlackBoxMap(
                    lambda x, _c: "dem" not in x and "rep" not in x,
                    lambda _x, _c: "other",
                ),
            ),
        },
    )
    party_match.rewrite["democratic-npl"] = "democratic"
    party_match.rewrite["democrat"] = "democratic"
    party_match.rewrite["democrat&republican"] = "democratic"
    party_match.rewrite["democrat/republican"] = "democratic"
    party_match.rewrite["democratic / republican"] = "democratic"
    party_match.rewrite["independent republican"] = "republican"
    party_match.rewrite["democratic-farmer-labor"] = "democratic"
    party_match.rewrite["dem/prog"] = "democratic"
    party_match.rewrite["prog/dem"] = "democratic"
    party_match.rewrite["dem/rep"] = "democratic"
    party_match.rewrite["rep/dem"] = "republican"

    return party_match


@attr.s(hash=True)
class MultiPartyResolver:
    @classmethod
    def usa(cls):
        return MultiPartyResolver(("DEM", "GOP"))

    major_parties = attr.ib()

    def __call__(self, parties):
        parties = list(set(parties))
        assert parties
        if len(parties) == 1:
            return parties[0]
        major_parties = list(set(self.major_parties) & set(parties))
        if len(major_parties) == 1:
            return major_parties[0]
        return "other"
