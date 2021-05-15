import textwrap

import numpy as np

import electiondata as e
from electiondata.examples.harvard_dataverse_2018_general import (
    HarvardDataverse2018General,
)
from electiondata.examples.mit_election_lab_2018_general import (
    MITElectionLab2018General,
)


class Canonical2018General(e.DataSource):
    def version(self):
        return "1.0.0"

    def description(self):
        return textwrap.dedent(
            """
            Canonical dataset for the 2018 election.

            Contains data for US House (by district), US Senate, and State Governors by county.

            The "other" votes are not super informative, necessarily.
            """
        )

    def get_direct(self):
        df_harvard = HarvardDataverse2018General(e.alaska.AT_LARGE).get()

        df_mit = MITElectionLab2018General().get()
        df_mit = df_mit.copy()

        df_mit["state"] = df_mit["state_po"]

        df_mit = df_mit[
            [
                "state",
                "office",
                "district",
                "votes_DEM",
                "votes_GOP",
                "votes_other",
                "county_fips",
            ]
        ]

        df_mit = df_mit[
            df_mit.office.apply(
                lambda x: x in {"us house", "us senate", "us state governor"}
            )
        ]

        e.district_normalizer().apply_to_df(df_mit, "district", "district")
        e.district_normalizer().apply_to_df(df_harvard, "district", "district")
        return e.merge(
            by_source={"harvard": df_harvard, "mit": df_mit},
            join_columns=["county_fips", "office", "district"],
            ignore_duplication={"votes_other": np.mean},
            resolvers=[
                e.DuplicationResolver(
                    lambda row: row.county_fips.startswith("01")
                    and row.office == "us house",
                    "harvard",
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips.startswith("41")
                    and row.office == "us house"
                    and row.district == 2,
                    "harvard",
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips.startswith("41")
                    and row.office == "us house"
                    and row.district == 2,
                    "harvard",
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips == "04013"
                    and row.office in {"us senate", "us house"},
                    "harvard",
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips == "20097", "harvard"
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips.startswith("26"), "harvard"
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips.startswith("27"), "harvard"
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips == "28091", "harvard"
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips.startswith("23")
                    and len(row.votes_DEM) == len(row.votes_GOP) == 2,
                    "mit",
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips in {"24037", "24039"}
                    and row.office in {"us senate", "us state governor"},
                    "mit",
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips.startswith("29"), "mit"
                ),
                e.DuplicationResolver(lambda row: row.county_fips == "42029", "mit"),
                e.DuplicationResolver(
                    lambda row: row.county_fips == "42057", "harvard"
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips.startswith("48")
                    and sum(row.votes_DEM) + sum(row.votes_GOP) > 0,
                    "harvard",
                ),
                e.DuplicationResolver(
                    lambda row: row.county_fips == "51153" and row.district == 1,
                    "harvard",
                ),
            ],
            checksum=e.Aggregator(
                grouped_columns=["district", "office", "state"],
                aggregation_functions={
                    "votes_DEM": sum,
                    "votes_GOP": sum,
                    "votes_other": sum,
                },
                removed_columns=["county_fips"],
            ),
        )
