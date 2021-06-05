import textwrap
import attr

import pandas as pd
import numpy as np

import electiondata as e


@attr.s
class Census2010Population(e.DataSource):
    alaska_handler = attr.ib()

    def version(self):
        return "1.0.7"

    def description(self):
        return textwrap.dedent(
            """
            Census 2010 population data
            """
        )

    def get_direct(self):

        df = e.to_csv(
            e.download(
                "https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/totals/co-est2019-alldata.csv"
            )
        )
        df = df[df.COUNTY != 0].copy()
        counts = [
            "CENSUS2010POP",
            "ESTIMATESBASE2010",
            "POPESTIMATE2010",
            "POPESTIMATE2011",
            "POPESTIMATE2012",
            "POPESTIMATE2013",
            "POPESTIMATE2014",
            "POPESTIMATE2015",
            "POPESTIMATE2016",
            "POPESTIMATE2017",
            "POPESTIMATE2018",
            "POPESTIMATE2019",
        ]
        df = df[["STNAME", "CTYNAME", *counts]]
        normalizer = e.usa_county_to_fips("STNAME", alaska_handler=self.alaska_handler)
        normalizer.rewrite["doña ana county"] = "dona ana county"
        normalizer.apply_to_df(df, "CTYNAME", "FIPS")
        df.loc[df.FIPS == "02AL", "CTYNAME"] = "Alaska"
        df = e.Aggregator(
            grouped_columns=["FIPS"], aggregation_functions={c: np.sum for c in counts}
        )(df)
        df = e.merge(
            by_source=dict(mainland=df, pr=self.puerto_rico()),
            join_columns=["FIPS"],
            ignore_duplication={},
            resolvers=[],
        )
        return df

    def puerto_rico(self):
        df = pd.read_excel(
            "https://www2.census.gov/programs-surveys/popest/tables/2010-2019/municipios/totals/prm-est2019-annres.xlsx"
        )
        df = np.array(df)
        df = df[4:-5]
        counts = df[:, 1:]
        countystate = [x[1:].split(", ") for x in df[:, 0]]
        cols = [
            "CTYNAME",
            "STNAME",
            "CENSUS2010POP",
            "ESTIMATESBASE2010",
            "POPESTIMATE2010",
            "POPESTIMATE2011",
            "POPESTIMATE2012",
            "POPESTIMATE2013",
            "POPESTIMATE2014",
            "POPESTIMATE2015",
            "POPESTIMATE2016",
            "POPESTIMATE2017",
            "POPESTIMATE2018",
            "POPESTIMATE2019",
        ]
        df = pd.DataFrame(np.concatenate([countystate, counts], axis=1), columns=cols)
        normalizer = e.usa_county_to_fips("STNAME")
        normalizer.apply_to_df(df, "CTYNAME", "FIPS", var_name="normalizer")
        return df
