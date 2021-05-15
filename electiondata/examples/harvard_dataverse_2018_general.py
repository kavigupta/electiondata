import io
from zipfile import ZipFile
import textwrap

import attr
import requests
import pandas as pd

import electiondata as e


@attr.s
class HarvardDataverse2018General(e.DataSource):
    alaska_handler = attr.ib()

    def version(self):
        return "1.4.0"

    def description(self):
        return textwrap.dedent(
            """
        Harvard Dataverse's 2018 dataset. This dataset contains information for most 2018 results

        It has some weird inconsistent data for New England, specifically CT, MA, NH, RI, VT.
        """
        )

    def get_direct(self):

        # https://doi.org/10.7910/DVN/UYSHST
        bs = requests.get(
            "https://dataverse.harvard.edu/api/access/datafile/:persistentId?persistentId=doi:10.7910/DVN/UYSHST/0UQP48"
        ).content
        zf = ZipFile(io.BytesIO(bs))
        with zf.open("national-files/us-house-wide.csv") as f:
            df_house = e.to_csv(f.read().decode("utf-8"))
        with zf.open("national-files/us-senate-wide.csv") as f:
            df_senate = e.to_csv(f.read().decode("utf-8"))
        with zf.open("national-files/governor-wide.csv") as f:
            df_governor = e.to_csv(f.read().decode("utf-8"))

        df = pd.concat([df_house, df_senate, df_governor])

        df = df[df.fipscode2 % 100000 == 0]  # only counties
        del df["fipscode"], df["fipscode2"], df["total.votes"]
        df = df.rename(
            columns={"dem": "votes_DEM", "rep": "votes_GOP", "other": "votes_other"}
        )

        county_normalizer = e.usa_county_to_fips(
            "state", alaska_handler=self.alaska_handler
        )

        county_normalizer.rewrite["baltimore"] = "baltimore county"
        county_normalizer.rewrite["franklin"] = "franklin county"
        county_normalizer.rewrite["richmond"] = "richmond county"
        county_normalizer.rewrite["jodaviess"] = "jo daviess"
        county_normalizer.rewrite["bedford"] = "bedford county"
        county_normalizer.rewrite["fairfax"] = "fairfax county"
        county_normalizer.rewrite["roanoke"] = "roanoke county"
        county_normalizer.rewrite["jeff davis"] = "jefferson davis"
        county_normalizer.rewrite["leflore"] = "le flore"
        county_normalizer.rewrite["oglala lakota (formerly shannon)"] = "oglala lakota"
        county_normalizer.rewrite["somerset cty townships"] = "somerset county"
        county_normalizer.rewrite["cook suburbs"] = "cook"
        county_normalizer.rewrite["oxford cty townships"] = "oxford county"
        county_normalizer.rewrite["state uocava"] = "ERROR"

        county_normalizer.rewrite["aroostook cty townships"] = "aroostook"
        county_normalizer.rewrite["franklin cty townships"] = "franklin county"
        county_normalizer.rewrite["hancock cty townships"] = "hancock county"

        county_normalizer.apply_to_df(
            df, col_in="county", col_out="county_fips", var_name="county_normalizer"
        )
        df = e.remove_errors(df, "county_fips")

        office_normalizer = e.usa_office_normalizer()

        office_normalizer.apply_to_df(df, "office", "office")

        agg = e.Aggregator(
            grouped_columns=["county_fips", "district", "office"],
            aggregation_functions={
                "votes_DEM": sum,
                "votes_GOP": sum,
                "votes_other": sum,
            },
        )

        agg.removed_columns.append("county")

        df = agg(df)

        return df
