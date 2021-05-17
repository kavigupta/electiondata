import textwrap

import electiondata as e


class MITElectionLab2018General(e.DataSource):
    def version(self):
        return "1.6.0"

    def description(self):
        return textwrap.dedent(
            """
            MIT Election Lab's 2018 dataset. This dataset contains information for most 2018 results.

            This dataset should probably not be used by itself. The main point is to be used as part of the canonical set
            There's a bunch of results missing.
            """
        )

    def get_direct(self):
        data = e.download(
            "https://raw.githubusercontent.com/MEDSL/2018-elections-official/master/county_2018.csv"
        )
        df = e.to_csv(data)

        # literal pointwise corrections
        # this row is fake and should not be present
        df = df[~((df.county == "Yuma") & (df.candidate == "Wendy Rogers"))]
        df = df.copy()

        matcher = e.usa_county_to_fips("state")

        matcher.rewrite["chenago county"] = "chenango county"
        matcher.rewrite["lac qui parte"] = "lac qui parle"
        matcher.rewrite["jodaviess"] = "jo daviess"
        matcher.rewrite["meeer"] = "meeker"

        matcher.rewrite["st. louis"] = "st. louis county"
        matcher.rewrite["baltimore"] = "baltimore county"
        matcher.rewrite["kansas city"] = "jackson"

        matcher.rewrite["state totals"] = "ERROR"
        matcher.rewrite["nan"] = "ERROR"
        matcher.rewrite["state uocava"] = "ERROR"
        matcher.rewrite["total votes by candidate"] = "ERROR"
        matcher.rewrite["total votes by party"] = "ERROR"
        matcher.rewrite["federal precinct"] = "ERROR"

        matcher.apply_to_df(df, "county", "county_fips", var_name="matcher")
        df = e.remove_errors(df, "county_fips")
        party_match = e.usa_party_normalizer("candidate")

        party_match.rewrite["fair representation vt"] = "other"
        party_match.rewrite["repeal bail reform"] = "other"

        party_match.apply_to_df(df, "party", "party", var_name="party_match")

        df = df[df.office.map(lambda x: "(partial term ending" not in x.lower())]

        office_normalizer = e.usa_office_normalizer()

        office_normalizer.rewrite[
            "nc supreme court associate justice seat 1"
        ] = "state supreme court justice 1"
        office_normalizer.rewrite[
            "governor's council"
        ] = "us state specific office: governor's council"
        office_normalizer.rewrite[
            "judge of the supreme court position 5"
        ] = "state supreme court justice 5"
        office_normalizer.rewrite["us state house pos. 1"] = "us state house a"
        office_normalizer.rewrite["us state house pos. 2"] = "us state house b"
        office_normalizer.rewrite["us state house representative"] = "us state house"

        office_normalizer.apply_to_df(
            df, "office", "office", var_name="office_normalizer"
        )

        df = e.remove_non_first_rank(df, "rank")

        agg = e.Aggregator(
            grouped_columns=["county_fips", "candidate", "office", "district"],
            aggregation_functions=dict(
                candidatevotes=sum,
                party=e.MultiPartyResolver.usa(),
            ),
        )
        agg.removed_columns.append("county")
        agg.removed_columns.append("mode")
        df = agg(df, var_name="agg")

        df = df.rename(columns={"candidatevotes": "votes"})

        agg = e.Aggregator(
            grouped_columns=["county_fips", "office", "district", "party"],
            aggregation_functions=dict(
                votes=sum,
            ),
        )
        agg.removed_columns.append("candidate")
        agg.removed_columns.append("writein")
        df = agg(df, var_name="agg")

        df = e.columns_for_variable(df, values_are="votes", columns_for="party")

        df.columns = ["_".join(col).strip("_") for col in df.columns.values]

        # These counties are not in this district
        df = df[
            ~(
                (df.state_po == "VA")
                & (df.office == "us house")
                & (df.district == "District 1")
                & ((df.county_fips == "51059") | (df.county_fips == "51600"))
            )
        ]

        # all senate seats are statewide
        df = df[~((df.district != "statewide") & (df.office == "us senate"))]
        # remove senate special elections, this dataset does not handle them correctly
        df = df[
            ~(
                (df.office == "us senate")
                & ((df.state_po == "MS") | (df.state_po == "MN"))
            )
        ]
        return df


class MITElectionLab2018GeneralHouseResults(e.DataSource):
    underlying = MITElectionLab2018General()

    def description(self):
        return (
            self.underlying.description()
            + "\nThis dataset is just the house results from that year, with the two_party_partisanship field added in"
        )

    def version(self):
        return self.underlying.version() + ".0"

    def get_direct(self):
        df = self.underlying.get_direct()
        df = df[df.office == "US Representative"]

        agg = e.Aggregator(
            grouped_columns=["county_fips"],
            aggregation_functions={
                "votes_DEM": sum,
                "votes_GOP": sum,
                "votes_other": sum,
            },
        )

        agg.removed_columns.append("district")
        agg.removed_columns.append("rank")
        agg.removed_columns.append("special")
        agg.removed_columns.append("totalvotes")

        df = agg(df, var_name="agg")
        df["two_party_partisanship"] = (df.votes_DEM - df.votes_GOP) / (
            df.votes_DEM + df.votes_GOP
        )
        return df
