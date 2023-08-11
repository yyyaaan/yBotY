
# %%
import pandas as pd
import xml.etree.ElementTree as ET
from os.path import exists
from requests import get, post
# plotly, folium imported on call


# %%
class StatFinPaavo:
    """
    Tools to load Paavo data to pandas data frame
    class parameter:
        data_id: can be configured to use different data set
        use show_available_data() to list all data_id
        use show_fields() to list all available data fields

    default dataset paavo_pxt_12f7.px
    to use different dataset, config obj.data_id="paavo_pxt_12f8.px"
    example:
        obj = StatFinPaavo()
        pd = obj.get_data()
    """

    base_url = (
        "https://pxdata.stat.fi/PXWeb/api/v1/fi/"
        "Postinumeroalueittainen_avoin_tieto/uusin/"
    )
    stat_geo_url = (
        "http://geo.stat.fi/geoserver/postialue/ows"
        "?service=WFS&version=1.0.0&request=GetFeature"
        "&typeName=postialue%3Apno_2023&maxFeatures=5000"
        "&outputFormat=application%2Fvnd.google-earth.kml%2Bxml"
    )
    geojson = None
    data_id = "paavo_pxt_12f7.px"

    def get_data(
            self,
            tiedot: list = ["tr_mtu"],
            vuosi: list = ["2021"],
            exclude_kokomaa: bool = True,
            output_json: bool = False,
    ):
        """
        fetch data to pandas data frame
        params:
            tiedot: list of data fields. use show_fields()
            vuosi: list of yyyy in string
        """
        fields = self.show_fields(simplify=False)
        if exclude_kokomaa:
            fields[0]["values"].pop(0)
        query = [
            {
                "code": "Postinumeroalue",
                "selection": {
                    "filter": "item",
                    "values": fields[0]["values"]
                }
            },
            {
                "code": "Tiedot",
                "selection": {
                    "filter": "item",
                    "values": tiedot
                }
            },
            {
                "code": "Vuosi",
                "selection": {
                    "filter": "item",
                    "values": vuosi
                }
            },
        ]

        response = post(
            url=self.base_url + self.data_id,
            json={
                "query": query,
                "response": {"format": "json"},
            }
        )
        self.__handle_error(response)
        if output_json:
            return response.json()
        return pd.DataFrame(
            data=[
                [*x.get('key', []), *x.get('values', [])]
                for x in response.json()["data"]
            ],
            columns=[x["code"] for x in response.json()["columns"]],
        )

    def show_fields(self, simplify=True) -> list:
        """
        show available fields for the selected data_id
        only show available "tiedot" if simplify=True
        """
        res = get(self.base_url + self.data_id)
        self.__handle_error(res)
        fields = res.json()["variables"]
        if not simplify:
            return fields
        return [{
            k: v for k, v in zip(
                fields[1]["values"],
                fields[1]["valueTexts"],
            )
        }]

    def show_available_data(self) -> dict:
        res = get(self.base_url)
        self.__handle_error(res)
        return res.json()

    def __handle_error(self, res):
        if res.status_code > 299:
            raise Exception("Error reading API", res.reason)

    def plot_on_map(
        self,
        df: pd.DataFrame,
        data_column: str,
        pno_column: str = "Postinumeroalue",
        save_to_filename: str = ""
    ):
        """
        df: the data frame that contains postal number
        data_column: specify the column name for numeric data
        pno_column: specify the column name that contains the post number
        save_to_filename: if not empty, save the map to output file
        """

        geojson = self.minimize_geojson(df[pno_column])

        from folium import Choropleth, GeoJsonTooltip, LayerControl, Map

        m = Map(location=[65, 25], zoom_start=5)

        cp = Choropleth(
            geo_data=geojson,
            name="choropleth",
            data=df,
            columns=[pno_column, data_column],
            key_on="id",
            nan_fill_color="white",
            nan_fill_opacity=0.8,
            fill_color="Oranges",
            fill_opacity=0.8,
            line_opacity=0.2,
            legend_name=data_column,
        ).add_to(m)

        df_indexed = df.set_index(pno_column)
        for one in cp.geojson.data['features']:
            try:
                one['properties'][data_column] = df_indexed.loc[one['id'], data_column]  # noqa: E501
            except Exception:
                pass

        GeoJsonTooltip(['posti_alue', 'nimi', data_column]).add_to(cp.geojson)  # noqa: E501
        LayerControl().add_to(m)

        if save_to_filename is not None and len(save_to_filename):
            m.save(save_to_filename)
        return m

    def plot_on_map_plotly(
        self,
        df: pd.DataFrame,
        data_column: str,
        pno_column: str = "Postinumeroalue",
    ):
        """plotly has known issue coloring the inverse occasionally"""
        geojson = self.minimize_geojson(df[pno_column])

        from plotly.express import choropleth

        fig = choropleth(
            data_frame=df,
            geojson=geojson,
            color=data_column,
            locations=pno_column,
            featureidkey="id",
            projection="mercator",
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig

    def minimize_geojson(self, posti_alue):
        if self.geojson is None:
            self.__process_geojson()

        geojson_small = {
            k: v for k, v in self.geojson.items()
            if k != "features"
        }
        geojson_small["features"] = [
            one for one in self.geojson["features"]
            if one["id"] in list(posti_alue)
        ]
        return geojson_small

    def __process_geojson(self):
        """dependency for geo plot. will be called automatically"""
        # download from statfin or read locally
        if not exists("pno_2023.kml"):
            print("downloading postinumeroalue from geo.stat.fi")
            with open("pno_2023.kml", "wb") as f:
                f.write(get(self.stat_geo_url).content)

        # read kml file
        with open("pno_2023.kml", "r") as f:
            kml = f.read()

        # def convert_kml_to_geojson(kml):
        root = ET.fromstring(kml)
        geojson = {"type": "FeatureCollection", "features": []}

        for placemark in root.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):  # noqa: E501

            metadata = {
                x.attrib["name"]: x.text
                for x in placemark.findall((
                    "{http://www.opengis.net/kml/2.2}ExtendedData/"
                    "{http://www.opengis.net/kml/2.2}SchemaData/"
                    "{http://www.opengis.net/kml/2.2}SimpleData"
                ))
            }
            feature = {
                "type": "Feature",
                "id": metadata["posti_alue"],
                "geometry": {},
                "geometry_name": "geom",
                "properties": metadata,
            }

            def process_one_polygon(geometry):
                coordinates = geometry.find((
                    "{http://www.opengis.net/kml/2.2}outerBoundaryIs/"
                    "{http://www.opengis.net/kml/2.2}LinearRing/"
                    "{http://www.opengis.net/kml/2.2}coordinates"
                ))
                return [
                    [float(x) for x in c.split(",")[:2]]
                    for c in coordinates.text.strip().split(" ")
                ]

            geometry = placemark.find("{http://www.opengis.net/kml/2.2}MultiGeometry")  # noqa: E501
            if geometry is not None:
                # multipolygon
                feature["geometry"]["type"] = "MultiPolygon"
                feature["geometry"]["coordinates"] = [
                    [process_one_polygon(g)]
                    for g in geometry.findall("{http://www.opengis.net/kml/2.2}Polygon")  # noqa: E501
                ]

            else:
                # polygon
                geometry = placemark.find("{http://www.opengis.net/kml/2.2}Polygon")  # noqa: E501
                if geometry is None:
                    print(feature["properties"]["posti_alue"], "processing failed")  # noqa: E501
                    continue

                feature["geometry"]["type"] = "Polygon"
                feature["geometry"]["coordinates"] = [process_one_polygon(geometry)]  # noqa: E501

            geojson["features"].append(feature)

        self.geojson = geojson
        return None


# %%
# stat_service = StatFinPaavo()
# df = stat_service.get_data()
# df["median_income"] = pd.to_numeric(df['tr_mtu'], errors='coerce')
# stat_service.plot_on_map(df, data_column="median_income")
# output size can be limited by reduce the postal numbers in df
