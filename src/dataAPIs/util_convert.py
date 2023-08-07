# %%
from json import loads, dumps
import xml.etree.ElementTree as ET


# %%
def util_convert_coordinates(geojson):
    """
    if downloaded from stat.fi, coordinates need conversion
    the features_converted.json is already converted
    """
    import pyproj
    from tqdm import tqdm

    def projected_to_wgs84(x, y, crs=3067):

        crs = pyproj.CRS.from_epsg(crs)
        wgs84 = pyproj.CRS.from_epsg(4326)

        transformer = pyproj.Transformer.from_crs(crs, wgs84, always_xy=True)
        lon, lat = transformer.transform(x, y)

        return lat, lon

    def convert_coordinates(geometry):
        if geometry['type'] == 'Polygon':
            for ring in geometry['coordinates']:
                for i, coord in enumerate(ring):
                    lon, lat = projected_to_wgs84(coord[0], coord[1])
                    ring[i] = [lat, lon]  # [lon, lat]

        elif geometry['type'] == 'MultiPolygon':
            for polygon in geometry['coordinates']:
                for ring in polygon:
                    for i, coord in enumerate(ring):
                        lon, lat = projected_to_wgs84(coord[0], coord[1])
                        ring[i] = [lat, lon]

    for feature in tqdm(geojson['features']):
        if 'geometry' in feature:
            convert_coordinates(feature['geometry'])

    with open("./features2022ok.json", "w") as f:
        f.write(dumps(geofin))


# %%


# %%
# with open("./pno_2023.kml", "r") as f:
#     kml = f.read()

# geojson = convert_kml_to_geojson(kml)
