import us
import textwrap

import pandas as pd

import electiondata as e


class CensusApportionment(e.DataSource):
    def version(self):
        return "1.0.1"

    def description(self):
        return textwrap.dedent(
            """
            Census apportionment for 2010 and 2020
            """
        )

    def get_direct(self):
        raw_table = pd.read_excel(
            "https://www2.census.gov/programs-surveys/decennial/2020/data/apportionment/apportionment-2020-table01.xlsx"
        )
        raw_table = raw_table.iloc[3:-2]
        raw_table.columns = ["State", "Pop", "seats_2020", "delta"]
        raw_table["seats_2010"] = raw_table.seats_2020 - raw_table.delta
        return {
            us.states.lookup(row.State).abbr: {
                2010: row.seats_2010,
                2020: row.seats_2020,
            }
            for _, row in raw_table.iterrows()
        }
