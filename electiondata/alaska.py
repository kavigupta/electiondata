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
    "alaska": "02AL",
}
