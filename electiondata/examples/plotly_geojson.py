import json
from datetime import datetime
import textwrap

import attr

import electiondata as e


@attr.s
class PlotlyGeoJSON(e.DataSource):
    year = attr.ib(default=datetime.today().year)

    def version(self):
        return "1.0.0"

    def description(self):
        return textwrap.dedent(
            """
            Plotly's GeoJSON file, mapping county fips codes to data

            The `year` argument specifies what year you want the data for. Years from 2002-now are supported.
            """
        )

    def get_direct(self):
        assert self.year >= 2002, "Years before 2002 are not supported"
        data = json.loads(
            e.download(
                "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
            )
        )
        # changes according to this doc: https://www.ddorn.net/data/FIPS_County_Code_Changes.pdf
        if self.year >= 2013:
            data["features"] = [x for x in data["features"] if x["id"] != "51515"]
        if self.year >= 2015:
            [oglala_lakota] = [x for x in data["features"] if x["id"] == "46113"]
            oglala_lakota["id"] = "46102"
        return data
