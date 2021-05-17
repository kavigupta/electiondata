import numpy as np
import pandas as pd


def handle_uncontested(
    df,
    *,
    missing_counties,
    missing_office,
    replacement_offices,
    fix_cols,
    replacement_mode,
):
    rows = []
    for extra_county, party in missing_counties:
        covered = df[
            (df.county_fips == extra_county)
            & (df.office == missing_office)
            & (~df.special)
        ]
        num_offices = 0
        result = 0
        for office in replacement_offices:
            for_office = df[
                (df.county_fips == extra_county) & (df.office == office) & (~df.special)
            ]
            num_offices += for_office.shape[0]
            result += for_office[fix_cols].sum()
        if num_offices == 0:
            continue
        row = covered.iloc[0].copy()
        num_votes = result / num_offices - covered[fix_cols].sum()

        if replacement_mode == "interpolate":
            row[fix_cols] = np.clip(num_votes, 0, np.inf)
        elif replacement_mode == "all-to-party":
            column = "votes_" + party
            assert column in fix_cols
            row[[column]] = np.clip(num_votes.sum(), 0, np.inf)
            row[[c for c in fix_cols if c != column]] = 0
        else:
            raise RuntimeError(f"Invalid replacement mode: {replacement_mode}")
        row.district = "all-uncontested"
        rows.append(row)
    return pd.concat([pd.DataFrame(rows), df])
