import textwrap

import attr

import numpy as np

import electiondata as e
from electiondata.examples.harvard_dataverse_2018_general import (
    HarvardDataverse2018General,
)
from electiondata.examples.harvard_dataverse_congress_district_results import (
    HarvardDataverseCongressDistrict,
)
from electiondata.examples.mit_election_lab_2018_general import (
    MITElectionLab2018General,
)


@attr.s
class Canonical2018General(e.DataSource):
    alaska_handler = attr.ib()
    uncontested_replacements = attr.ib()
    uncontested_replacement_mode = attr.ib(default="all-to-party", kw_only=True)

    def version(self):
        return "1.5.1"

    def description(self):
        return textwrap.dedent(
            """
            Canonical dataset for the 2018 election.

            Contains data for US House (by district), US Senate, and State Governors by county.

            House and Senate data are all validated within 1% of a second source, with the following exceptions
                - Maine is only somewhat aligned (within 2% not 1%) and has some complexity due to RCV
                - Four districts in FL were uncontested. You should pass a list of offices to replace the votes with.
                    By default, it just doesn't fix it at all,
                    but passing in uncontested_replacements=["us state governor", "us senate"]
                    causes it to take the average of the votes of those two by county and adjust for present house
                    districts turnouts
                    You can also have it interpolate by having it use uncontested_replacement_mode="interpolate"
            """
        )

    def get_direct(self):
        df_harvard = HarvardDataverse2018General(self.alaska_handler).get()

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
                "special",
            ]
        ]

        df_mit = df_mit[
            df_mit.office.apply(
                lambda x: x in {"us house", "us senate", "us state governor"}
            )
        ]
        df_mit = df_mit[df_mit.district != "District 0"]

        e.district_normalizer().apply_to_df(df_mit, "district", "district")

        df = e.merge(
            by_source={"harvard": df_harvard, "mit": df_mit},
            join_columns=["county_fips", "office", "district", "state", "special"],
            ignore_duplication={"votes_other": np.mean},
            resolvers=self.resolvers(),
            checksum=e.Aggregator(
                grouped_columns=["district", "office", "state", "special"],
                aggregation_functions={
                    "votes_DEM": sum,
                    "votes_GOP": sum,
                    "votes_other": sum,
                },
                removed_columns=["county_fips"],
            ),
        )
        by_district = e.Aggregator(
            grouped_columns=["district", "office", "state", "special"],
            removed_columns=["county_fips"],
            aggregation_functions=dict(votes_other=sum, votes_DEM=sum, votes_GOP=sum),
        )(df)
        summary = HarvardDataverseCongressDistrict().get_direct()
        e.validate_same(
            by_district[by_district.office == "us house"],
            summary[(summary.year == 2018) & (summary.office == "us house")],
            key_cols=["state", "district", "special"],
            check_cols=["votes_DEM", "votes_GOP"],
            ignore_missing=(
                [
                    ("FL", 10, False),
                    ("FL", 14, False),
                    ("FL", 21, False),
                    ("FL", 24, False),
                ],
                [("NY", 25, True)],
            ),
            ignore_discrepancies=lambda k: k[0] == "ME",
        )
        e.validate_same(
            by_district[by_district.office == "us senate"],
            summary[(summary.year == 2018) & (summary.office == "us senate")],
            key_cols=["state", "district", "special"],
            check_cols=["votes_DEM", "votes_GOP"],
            ignore_discrepancies=lambda k: k[0] == "ME",
        )

        df = e.handle_uncontested(
            df,
            missing_counties=[
                (e.usa_county_to_fips("state")(county, dict(state="FL")), party)
                for county, party in [
                    ("Hillsborough", "DEM"),
                    ("Miami-Dade", "DEM"),
                    ("Broward", "DEM"),
                    ("Orange", "DEM"),
                ]
            ],
            missing_office="us house",
            replacement_offices=self.uncontested_replacements,
            fix_cols=["votes_DEM", "votes_GOP", "votes_other"],
            replacement_mode=self.uncontested_replacement_mode,
        )

        return df

    def resolvers(self):
        return [
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("01")
                and row.office == "us house",
                "harvard",
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips == "04013"
                and row.office in {"us senate", "us house"},
                "harvard",
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("09")
                and row.district == 4
                and row.office == "us house",
                "harvard",
                force_value=0,
            ),
            e.DuplicationResolver(lambda row: row.county_fips == "20097", "harvard"),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("23"),
                "harvard",
                force_value=0,
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips in {"24037", "24039"}
                and row.office in {"us senate", "us state governor"},
                "mit",
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("25")
                and row.office == "us senate",
                "harvard",
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("25")
                and row.office == "us house"
                and row.district == 4,
                "mit",
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("26")
                and row.office == "us state governor",
                "harvard",
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips == "26163" and row.office == "us house",
                "mit",
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("27"), "harvard"
            ),
            e.DuplicationResolver(lambda row: row.county_fips == "28091", "harvard"),
            e.DuplicationResolver(lambda row: row.county_fips.startswith("29"), "mit"),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("33") and row.district == 1,
                "harvard",
                force_value=0,
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("33")
                and row.office == "us state governor",
                "mit",
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
            e.DuplicationResolver(lambda row: row.county_fips == "42029", "mit"),
            e.DuplicationResolver(lambda row: row.county_fips == "42057", "harvard"),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("48")
                and sum(row.votes_DEM) + sum(row.votes_GOP) > 0,
                "harvard",
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("50")
                and row.office == "us state governor",
                "harvard",
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips.startswith("50")
                and row.office == "us senate",
                "mit",
            ),
            e.DuplicationResolver(
                lambda row: row.county_fips == "51153" and row.district == 1,
                "harvard",
            ),
        ]
