import string

from addfips import AddFIPS

from .clean import CleanString
from .matcher import UniqueMatch, DictionaryMap, Dispatcher, BlackBoxMap
from .rewrite import RewriteSystem, PointwiseRewrite, RegexRewrite


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


def usa_county_to_fips(state_column, *, alaska_handler=None):
    af = AddFIPS()

    def get_county_fips_map(state_fips):
        if alaska_handler is not None and state_fips == "02":
            return alaska_handler
        return remove_problematic(
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


def usa_office_normalizer():
    def full_cleanup(x):
        x = CleanString()(x)
        if x.startswith("for "):
            x = x[len("for ") :]
        if x.endswith(" member"):
            x = x[: -len(" member")]
        return x

    return UniqueMatch(
        RewriteSystem(
            full_cleanup,
            [
                # standard stuff
                RegexRewrite("^for ", ""),
                RegexRewrite(r" \& ", " and "),
                RegexRewrite(r"( )?/( )?", " and "),
                RegexRewrite(r"\blt(\.|\b)", "lieutenant"),
                RegexRewrite(" special election$", ""),
                RegexRewrite(r"\bsenator\b", "senate"),
                PointwiseRewrite("us representative", "us house"),
                ## Legislative positions
                PointwiseRewrite("state senate", "us state senate"),
                RegexRewrite(r"house of delegates", "us state house"),
                RegexRewrite(r"state assembly", "state house"),
                RegexRewrite(
                    r"state (house( delegate)?|representative)", "us state house"
                ),
                ## Executive positions
                PointwiseRewrite("governor", "us state governor"),
                PointwiseRewrite("lieutenant governor", "us state lieutenant governor"),
                PointwiseRewrite(
                    "governor and lieutenant governor", "us state governor"
                ),
                ## state sc judges
                RegexRewrite(
                    r"^justice of (the )?supreme court|(state )?supreme court justice$",
                    "state supreme court justice",
                ),
                RegexRewrite(
                    r"^(state )?supreme court (associate )?justice,? (position|seat) (?P<place>(\d|[a-z])+)$",
                    r"state supreme court justice \g<place>",
                ),
                RegexRewrite(
                    r"^(associate )?justice (-|of the) supreme court( of appeals)?(,| -)?( (place|division))? (?P<place>\d+)$",
                    r"state supreme court justice \g<place>",
                ),
                RegexRewrite(
                    r"^justice, supreme court, place (?P<place>\d+)$",
                    r"state supreme court justice \g<place>",
                ),
                RegexRewrite(
                    r"^chief justice (of the|-) supreme court$",
                    r"state supreme court justice chief",
                ),
            ],
        ),
        {
            "standard_offices": DictionaryMap.identity(
                "us senate",
                "us house",
                "us state senate",
                "us state house",
                "us state house a",
                "us state house b",
                "us state governor",
                "us state lieutenant governor",
                "state supreme court justice",
                *(
                    f"state supreme court justice {i}"
                    for i in [*range(20), *string.ascii_lowercase, "chief"]
                ),
            ),
            "state_specific_offices_1": BlackBoxMap(
                lambda x, _: all(
                    key not in x
                    for key in [
                        "senat",
                        "house",
                        "rep",
                        "assembly",
                        "leg",
                        "delegate",
                        "gov",
                        "supreme",
                    ]
                ),
                lambda x, _: f"us state specific office: {x}",
            ),
            "state_specific_offices_2": BlackBoxMap(
                lambda x, _: x.startswith("us state specific office"), lambda x, _: x
            ),
        },
    )


def district_normalizer():
    return UniqueMatch(
        RewriteSystem(
            CleanString(),
            [RegexRewrite("^district ", "")],
        ),
        {
            "numbered": DictionaryMap({str(x): x for x in range(1, 100)}),
            "statewide": DictionaryMap.identity("statewide"),
        },
    )
