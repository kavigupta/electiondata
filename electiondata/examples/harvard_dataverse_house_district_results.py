import textwrap
import pandas as pd
import numpy as np

import electiondata as e


class HarvardDataverseHouseDistrict(e.DataSource):
    def version(self):
        return "1.0.0"

    def description(self):
        return textwrap.dedent(
            """
            All house results from 1978 to 2018, by district (not county)
            """
        )

    def get_direct(self):
        df = pd.read_csv(
            "https://dataverse.harvard.edu/api/access/datafile/4202836", sep="\t"
        )
        df = df[df.stage == "gen"]
        df = df[~(df.runoff == True)]
        df.district = df.district.apply(lambda x: 1 if x == 0 else x)

        party_normalizer = e.usa_party_normalizer()
        party_normalizer.rewrite["aloha democratic"] = "other"
        party_normalizer.rewrite["independent-republican"] = "republican"
        party_normalizer.rewrite["national democrat"] = "democratic"
        party_normalizer.rewrite["democratic-nonpartisan league"] = "democratic"
        party_normalizer.rewrite["foglietta (democrat)"] = "democratic"
        party_normalizer.rewrite["regular democracy"] = "other"
        party_normalizer.rewrite["national democratic party of alabama"] = "democratic"
        party_normalizer.rewrite["democracy in action"] = "other"
        party_normalizer.rewrite["pro-democracy reform"] = "other"
        party_normalizer.rewrite["academic christian freedom"] = "other"
        party_normalizer.rewrite["quality congressional representation"] = "other"
        party_normalizer.rewrite["representing the 99%"] = "other"
        party_normalizer.apply_to_df(df, "party", "party", var_name="party_normalizer")
        agg = e.Aggregator(
            grouped_columns=["year", "state_po", "district", "party"],
            aggregation_functions={"candidatevotes": sum},
        )

        agg.removed_columns.append("fusion_ticket")
        agg.removed_columns.append("writein")
        agg.removed_columns.append("candidate")

        df = agg(df)

        del df["runoff"], df["special"], df["mode"], df["totalvotes"], df["unofficial"]

        df = df.rename(columns={"candidatevotes": "votes"})
        df = e.columns_for_variable(df, values_are="votes", columns_for="party")
        df.columns = ["_".join(col).strip("_") for col in df.columns.values]

        df["state"] = df["state_po"]
        del df["state_po"]

        # Pointwise fixes, CT from Ballotpedia, ME from NYT
        ballotpedia_fixes_2018 = [
            ("CT", 1, 175087, 96024),
            ("CT", 2, 179731, 102483),
            ("CT", 3, 174572, 95667),
            ("CT", 4, 168726, 106921),
            ("CT", 5, 151225, 119426),
            ("ME", 2, 131954, 134061),
            ("NY", 1, 131954, 134061),
        ]

        # Wikipedia
        wiki_ny = e.read_wikipedia(
            "https://en.wikipedia.org/wiki/2018_United_States_House_of_Representatives_elections_in_New_York",
            "Republican Hold",
        )
        for i, (district, dem_votes, gop_votes, _) in enumerate(
            np.array(wiki_ny)[:-1, [0, 1, 3, 5]]
        ):
            assert district == f"District {i + 1}"
            ballotpedia_fixes_2018.append(("NY", i + 1, dem_votes, gop_votes))
        for state, dist, dem, gop in ballotpedia_fixes_2018:
            df.loc[
                (df.year == 2018) & (df.state == state) & (df.district == dist),
                ["votes_DEM", "votes_GOP"],
            ] = [dem, gop]

        return df
