import textwrap
import attr

import electiondata as e


@attr.s
class Census2010Population(e.DataSource):
    alaska_handler = attr.ib()

    def version(self):
        return "1.0.0"

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
        normalizer = e.usa_county_to_fips("STNAME", alaska_handler=self.alaska_handler)
        normalizer.rewrite["doña ana county"] = "dona ana county"
        normalizer.apply_to_df(df, "CTYNAME", "FIPS")
        return df
