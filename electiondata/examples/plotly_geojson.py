import json
from collections import defaultdict
from datetime import datetime
import textwrap

import attr

import electiondata as e


@attr.s
class PlotlyGeoJSON(e.DataSource):
    alaska_handler = attr.ib(default=e.alaska.FIPS)
    year = attr.ib(default=datetime.today().year)

    def version(self):
        return "1.0.2"

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

            [kusilvak] = [x for x in data["features"] if x["id"] == "02270"]
            kusilvak["id"] = "02158"

        by_county = defaultdict(list)
        for feat in data["features"]:
            ident = feat["id"]
            if ident in self.alaska_handler:
                ident = self.alaska_handler[ident]
            by_county[ident].append(feat)
        data = dict(
            type=data["type"],
            features=[
                merge_geojson(elements, id) for id, elements in by_county.items()
            ],
        )
        return data


def merge_geojson(elements, id):
    result = {}
    assert all(el["type"] == "Feature" for el in elements)
    result["type"] = "Feature"
    result["properties"] = {
        "CENSUSAREA": sum(el["properties"]["CENSUSAREA"] for el in elements)
    }
    result["geometry"] = dict(type="MultiPolygon", coordinates=[])
    for el in elements:
        geo = el["geometry"]["coordinates"]
        result["geometry"]["coordinates"] += dict(MultiPolygon=geo, Polygon=[geo])[
            el["geometry"]["type"]
        ]
    result["id"] = id
    return result
