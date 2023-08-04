# %%
from requests import get, post
from io import StringIO
from pandas import read_csv


# %%
class StatFinPaavo:
    """
    Tools to load Paavo data to pandas data frame
    class parameter:
        data_id: can be configured to use different data set
        use show_available_data() to list all data_id
        use show_fields() to list all available data fields

    example:
        obj = StatFinPaavo()
        # default dataset paavo_pxt_12f7.px
        # to use different dataset, config obj.data_id="paavo_pxt_12f8.px"
        pd = obj.get_data()
    """

    base_url = (
        "https://pxdata.stat.fi/PXWeb/api/v1/fi/"
        "Postinumeroalueittainen_avoin_tieto/uusin/"
    )
    data_id = "paavo_pxt_12f7.px"

    def get_data(
            self,
            tiedot: list = ["tr_mtu"],
            vuosi: list = ["2021"],
            exclude_kokomaa: bool = True
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
                    "values": ["2021"]
                }
            },
        ]

        response = post(
            url=self.base_url + self.data_id,
            json={
                "query": query,
                "response": {"format": "csv"},
            }
        )
        self.__handle_error(response)
        return read_csv(StringIO(response.text))

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
