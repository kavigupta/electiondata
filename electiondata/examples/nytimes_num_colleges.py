import textwrap
import pandas as pd
import numpy as np

import electiondata as e


class NYTimesNumColleges(e.DataSource):
    def version(self):
        return "1.0.0"

    def description(self):
        return textwrap.dedent(
            """
            NYtimes number of colleges by county
            """
        )

    def get_direct(self):
        colleges = pd.read_csv(
            "https://raw.githubusercontent.com/nytimes/covid-19-data/master/colleges/colleges.csv"
        )
        norm = e.usa_county_to_fips("state")
        norm.rewrite["baltimore"] = "baltimore city"
        norm.rewrite["st. louis"] = "st. louis city"
        norm.rewrite["new york city"] = "new york"
        norm.rewrite["franklin"] = "franklin city"
        norm.rewrite["richmond"] = "richmond city"
        norm.rewrite["fairfax"] = "fairfax city"
        norm.rewrite["roanoke"] = "roanoke city"
        norm.rewrite["st. thomas"] = "st. thomas island"
        norm.rewrite["doña ana"] = "dona ana"
        norm.rewrite["bayam_n"] = "bayamon"
        norm.rewrite["maoputasi"] = "ERROR"
        norm.rewrite["mangilao village"] = "ERROR"
        norm.rewrite["nan"] = "ERROR"
        norm.rewrite["joplin"] = "jasper"
        norm.rewrite["kansas city"] = "jackson"
        norm.rewrite["washington, d.c."] = "ERROR"
        norm.apply_to_df(colleges, "county", "county_fips", var_name="norm")

        colleges = e.remove_errors(colleges, "county_fips")
        agg = e.Aggregator(
            grouped_columns=["county_fips"],
            aggregation_functions={"college": lambda x: len(set(x))},
        )

        agg.removed_columns.append("cases")
        agg.removed_columns.append("cases_2021")
        agg.removed_columns.append("city")
        agg.removed_columns.append("college")
        agg.removed_columns.append("county")
        agg.removed_columns.append("ipeds_id")
        agg.removed_columns.append("notes")
        agg.removed_columns.append("state")
        agg.removed_columns.append("date")

        return agg(colleges, var_name="agg")
