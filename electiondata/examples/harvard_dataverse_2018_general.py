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
        return "1.6.1"

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

        # Just manually fix the Angus King thing
        df_senate.loc[df_senate.state == "ME", "dem"] += df_senate[
            df_senate.state == "ME"
        ]["other"]
        df_senate.loc[df_senate.state == "ME", "other"] = 0

        df = pd.concat([df_house, df_senate, df_governor])

        df = pd.concat(
            [
                self.normalize_named_counties(df[df.fipscode2 % 100000 == 0]),
                self.normalize_townships(df[df.fipscode2 % 100000 != 0]),
            ]
        )

        df["special"] = df.office == "US Senate Special Election"

        df = df.rename(
            columns={"dem": "votes_DEM", "rep": "votes_GOP", "other": "votes_other"}
        )

        office_normalizer = e.usa_office_normalizer()

        office_normalizer.apply_to_df(df, "office", "office")

        e.district_normalizer().apply_to_df(df, "district", "district")

        df.district = df.apply(
            lambda row: row.district
            if row.district == "statewide" or row.state != "WV"
            else {31: 3, 21: 2, 11: 1}[row.district],
            axis=1,
        )

        df = df[~((df.district == "statewide") & (df.office == "us house"))]

        agg = e.Aggregator(
            grouped_columns=["county_fips", "district", "office", "special"],
            aggregation_functions={
                "votes_DEM": sum,
                "votes_GOP": sum,
                "votes_other": sum,
            },
        )

        agg.removed_columns.append("county")

        df = agg(df)

        # Source: https://ballotpedia.org/Arizona%27s_5th_Congressional_District_election,_2018
        df.loc[(df.state == "AZ") & (df.district == 5), "votes_GOP"] = 186037

        # Source: https://www.nytimes.com/elections/results/connecticut-house-district-1
        df.loc[
            (df.state == "CT") & (df.district == 1) & (df.county_fips == "09003"),
            ["votes_DEM", "votes_GOP", "votes_other"],
        ] = [159950, 81418, 2651]
        df.loc[
            (df.state == "CT") & (df.district == 5) & (df.county_fips == "09003"),
            ["votes_DEM", "votes_GOP", "votes_other"],
        ] = [41805, 26985, 0]
        # Source: https://www.nytimes.com/elections/results/michigan-house-district-13
        df.loc[
            (df.state == "MI") & (df.district == 13),
            ["votes_DEM", "votes_GOP", "votes_other"],
        ] = [165355, 0, 0]

        # Extra row removal, this row should not be present
        df = df[~((df.county_fips == "24037") & (df.district == 1))]

        df = df.copy()

        # this row belongs to the wrong county
        # see https://www.nytimes.com/elections/results/maryland-house-district-5
        # Somerset is included instead of St Marys
        df.loc[
            (df.state == "MD") & (df.district == 5) & (df.county_fips == "24039"),
            "county_fips",
        ] = "24037"

        return df

    def normalize_named_counties(self, df):
        df = df.copy()
        del df["fipscode"], df["fipscode2"], df["total.votes"]
        county_normalizer = e.usa_county_to_fips(
            "state", alaska_handler=self.alaska_handler
        )
        county_normalizer.rewrite["alaska"] = "ERROR"
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

        return df

    def normalize_townships(self, df):
        df = df.copy()
        df["county_fips"] = df.fipscode.apply(lambda x: f"{x:05d}")
        del df["fipscode"], df["fipscode2"], df["total.votes"]
        return df
