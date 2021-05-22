"""
Various ways to handle alaska reigon codes
"""

from addfips import AddFIPS

_ORIGINAL_FIPS_MAP = {
    county: "02" + fips for county, fips in AddFIPS()._counties.get("02").items()
}

FIPS = {**_ORIGINAL_FIPS_MAP, **{fips: fips for fips in _ORIGINAL_FIPS_MAP.values()}}

AT_LARGE = {
    **{county: "02AL" for county in FIPS},
    **{f"electoral district {i}": "02AL" for i in range(1, 1 + 40)},
}


def FOUR_REGIONS(state_districts=2013):
    # defined in https://www.google.com/maps/d/u/0/edit?mid=1exlLjaDKQMf7L2pprsW2Q30SS8se4xLP&ll=58.022037288739625%2C-148.71971954377227&z=5
    assert state_districts == 2013
    electoral_districts_by_reigon = {
        "NW": [*range(1, 1 + 6), *range(8, 1 + 10), *range(37, 1 + 40)],
        "ANC": [7, *range(11, 1 + 28)],
        "KP": [*range(29, 1 + 32)],
        "JUN": [*range(33, 1 + 36)],
    }
    counties_by_reigon = {
        "NW": [
            "aleutians east",
            "aleutians west",
            "bethel",
            "bristol bay",
            "copper river",
            "denali",
            "dillingham",
            "fairbanks north star",
            "kusilvak",
            "wade hampton",
            "lake and peninsula",
            "matanuska-susitna",
            "nome",
            "north slope",
            "northwest arctic",
            "southeast fairbanks",
            "valdez-cordova",
            "yukon-koyukuk",
        ],
        "ANC": ["anchorage"],
        "KP": ["kenai peninsula", "kodiak island", "yakutat"],
        "JUN": [
            "haines",
            "skagway",
            "juneau",
            "ketchikan gateway",
            "hoonah-angoon",
            "wrangell",
            "petersburg",
            "prince of wales-hyder",
            "sitka",
        ],
    }

    four_reigons = {
        f"electoral district {district}": f"{name}"
        for name, districts in electoral_districts_by_reigon.items()
        for district in districts
    }

    backmap = {}
    for county, fips in _ORIGINAL_FIPS_MAP.items():
        elements = [
            k for k in _ORIGINAL_FIPS_MAP if county.startswith(k) and county != k
        ]
        if elements:
            assert len(elements) == 1
            backmap[county] = backmap[fips] = elements[0]
            continue
        for reigon, counties in counties_by_reigon.items():
            if county in counties:
                four_reigons[county] = reigon
                four_reigons[fips] = reigon
                break
        else:
            raise RuntimeError(f"Unrecognized county {county}")
    for a, b in backmap.items():
        four_reigons[a] = four_reigons[b]

    four_reigons = {k: "02" + v for k, v in four_reigons.items()}
    return four_reigons
