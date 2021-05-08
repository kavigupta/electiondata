from addfips import AddFIPS

from .clean import CleanString
from .matcher import UniqueMatch, DictionaryMap, Dispatcher
from .rewrite import RewriteSystem, RegexRewrite


def standard_name_normalizer():
    return RewriteSystem(
        CleanString(),
        [
            RegexRewrite("'", ""),
            RegexRewrite("^de", "de "),
            RegexRewrite("^de ", "de"),
            RegexRewrite("^la", "la "),
            RegexRewrite("la ", "la"),
            RegexRewrite("^st ", "saint "),
            RegexRewrite("^saint ", "st "),
            RegexRewrite(" & ", " and "),
        ],
    )


def usa_county_to_fips(state_column):
    af = AddFIPS()
    get_county_fips_map = lambda state_fips: {
        k: state_fips + v for k, v in af._counties.get(state_fips, {}).items()
    }
    return UniqueMatch(
        standard_name_normalizer(),
        {
            "counties": Dispatcher(
                lambda x: x[state_column],
                lambda state: DictionaryMap(
                    get_county_fips_map(af.get_state_fips(state)),
                    state,
                    default_rewrite="ERROR",
                ),
            ),
            "errors": DictionaryMap({"ERROR": "ERROR"}),
        },
    )
