
import re
import numpy as np

import us
from addfips import AddFIPS
from fuzzy_match import match

from .run_across import run_on_df, remove_bad
from .errors import DataError

class NameNormalizer:
    def __init__(self):
        self.synonyms = [("st", "saint"), (" & ", " and ")]
        self.prefixes = ["de", "la"]

    @property
    def regexes(self):
        for a, b in self.synonyms:
            yield f"\\b{re.escape(a)}\\b", b
            yield f"\\b{re.escape(b)}\\b", a
        for a in self.prefixes:
            yield f"^{a}", f"{a} "
            yield f"^{a} ", f"{a}"

    def __call__(self, name):
        name = name.lower()
        yield name
        for a, b in self.regexes:
            yield re.sub(a, b, name)

class CountyFIPS:

    def __init__(self):
        self.add_fips = AddFIPS()
        self.typos = {}
        self.county_normalizer = NameNormalizer()
        self.bads = [r".*\bstate totals\b.*", r".*\buocava\b.*", r".*\btotal votes\b.*"]

    def __call__(self, state, county):
        if county == "":
            return "BAD: <empty>"
        if not isinstance(county, str) and np.isnan(county):
            return "BAD: nan"

        county = county.lower()
        state = self.normalize_state(state)

        if any(re.fullmatch(bad, county) for bad in self.bads):
            return f"BAD: {county}"

        if (county, state) in self.typos:
            county = self.typos[county, state]

        for county_norm in self.county_normalizer(county):
            fips = self.add_fips.get_county_fips(county_norm, state=state)
            if fips is not None:
                return fips
        county_names = self.county_names(state)
        replacement, confidence = match.extractOne(county, county_names)
        if confidence > 0.25:
            fix = f"$var.typos[{county!r}, {state!r}] = {replacement!r}"
        else:
            fix = None
        raise DataError(f"{state}: {county} does not exist", fix)

    def process(self, df, state, county, county_fips):
        df[county_fips] = run_on_df(self, df, state, county)
        df = remove_bad(df, county_fips)
        return df

    def county_names(self, state):
        state_fips = self.add_fips.get_state_fips(state)
        counties = self.add_fips._counties.get(state_fips, {})
        return list(counties)


    def normalize_state(self, state):
        return us.states.lookup(state).abbr
