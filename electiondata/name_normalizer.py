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


def remove_problematic(county_name_map):
    problematic = set()
    for name in county_name_map:
        name_extended = {
            name + " " + suffix for suffix in {"county", "city", "borough", "district"}
        }
        similar_names = set(county_name_map) & name_extended
        if len(similar_names) == 0:
            # no similar names
            continue
        fipses = set(county_name_map[name] for name in similar_names)
        if len(fipses) == 1 and county_name_map[name] in fipses:
            # no ambiguity
            continue
        if county_name_map[name] in fipses:
            # recoverable ambiguity, one of the fipses corresponds to the county name
            problematic.add(name)
            continue
        # irrecoverable ambiguity, should never happen
        raise RuntimeError(
            f"Prefix of the name of a county and the county both present: {name}"
        )

    return {k: v for k, v in county_name_map.items() if k not in problematic}


def usa_county_to_fips(state_column):
    af = AddFIPS()
    get_county_fips_map = lambda state_fips: remove_problematic(
        {k: state_fips + v for k, v in af._counties.get(state_fips, {}).items()},
    )
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
