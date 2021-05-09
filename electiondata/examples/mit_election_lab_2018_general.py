import textwrap

import electiondata as e


class MITElectionLab2018General(e.DataSource):
    def version(self):
        return "1.2.0"

    def description(self):
        return textwrap.dedent(
            """
            MIT Election Lab's 2018 dataset. This dataset contains information for most 2018 results.

            It appears to be missing all of Alaska's results, IA-1 House results, and all results for
                Kalawao County, HI
                Yazoo County, MS
            """
        )

    def get_direct(self):
        data = e.download(
            "https://raw.githubusercontent.com/MEDSL/2018-elections-official/master/county_2018.csv"
        )
        df = e.to_csv(data)
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
        party_match = e.usa_party_normalizer()

        party_match.rewrite["fair representation vt"] = "other"
        party_match.rewrite["repeal bail reform"] = "other"

        party_match.apply_to_df(df, "party", "party", var_name="party_match")
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
