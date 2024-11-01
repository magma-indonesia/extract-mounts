import os
import json
import pandas as pd
import re
import requests
from typing import Any, Dict, List
from requests import Response

volcanoes: List[Dict[str, Any]] = [
    {
        "name": "Anak Krakatau",
        "smithsonian_id": "262000",
        "code": "KRA",
    },
    {
        "name": "Awu",
        "smithsonian_id": "267040",
        "code": "AWU",
    },
    {
        "name": "Dukono",
        "smithsonian_id": "268010",
        "code": "DUK",
    },
    {
        "name": "Ibu",
        "smithsonian_id": "268030",
        "code": "IBU",
    },
    {
        "name": "Ijen",
        "smithsonian_id": "263350",
        "code": "IJE",
    },
    {
        "name": "Ili Lewotolok",
        "smithsonian_id": "264230",
        "code": "LEW",
    },
    {
        "name": "Karangetang",
        "smithsonian_id": "267020",
        "code": "KAR",
    },
    {
        "name": "Kerinci",
        "smithsonian_id": "261170",
        "code": "KER",
    },
    {
        "name": "Lewotobi Laki-laki",
        "smithsonian_id": "264180",
        "code": "LWK",
    },
    {
        "name": "Marapi",
        "smithsonian_id": "261140",
        "code": "MAR",
    },
    {
        "name": "Merapi",
        "smithsonian_id": "263250",
        "code": "MER",
    },
    {
        "name": "Raung",
        "smithsonian_id": "263340",
        "code": "RAU",
    },
    {
        "name": "Ruang",
        "smithsonian_id": "267010",
        "code": "RUA",
    },
    {
        "name": "Semeru",
        "smithsonian_id": "263300",
        "code": "SMR",
    },
    {
        "name": "Slamet",
        "smithsonian_id": "263180",
        "code": "SLA",
    }
]


class MountsProject:
    URL: str = "http://mounts-project.com/timeseries/"

    def __init__(self, include_anomaly: bool = False, filter_value: float = 0.1,
                 output_directory: str = None, save_to_database: bool = True):
        self.include_anomaly = include_anomaly
        self.filter_value = filter_value

        self.output_directory: str = output_directory
        if output_directory is None:
            self.output_directory = os.path.join(os.getcwd(), 'output')
        os.makedirs(self.output_directory, exist_ok=True)

        self.json_dir: str = os.path.join(self.output_directory, 'json')
        os.makedirs(self.json_dir, exist_ok=True)

        self.save_to_database = save_to_database

        self.volcanoes: List[Dict[str, Any]] = volcanoes

    @staticmethod
    def get_json_from_javascript(text: Any) -> Dict[str, Any]:
        """Get JSON from javascript string variable.

        Args:
            text (Any): Javascript string variable.

        Returns:
            Dict[str, Any]: JSON from javascript.
        """
        var_graph = re.search(r"(?:^|\s|;)var\s+graph\s*=\s*([^']+})", text)
        assert var_graph is not None, f"❌ Data not found."
        string_graph = var_graph.group(1)
        json_graph = json.loads(string_graph)
        return json_graph

    @staticmethod
    def fetch(smithsonian_id: str) -> Dict[str, Any]:
        """Fetch JSON from URL.

        Args:
            smithsonian_id (str): Volcano smithsonian_id.

        Returns:
            Dict[str, Any]: JSON from URL.
        """
        url = f"{MountsProject.URL}{smithsonian_id}"
        response: Response = requests.get(url)
        return MountsProject.get_json_from_javascript(response.text)

    def write_json(self, smithsonian_id: str) -> List[Dict[str, Any]]:
        """Write JSON to file.

        Args:
            smithsonian_id (str): Volcano smithsonian_id.

        Returns:
            List[Dict[str, Any]]: List of dict from URL.
        """
        json_file = os.path.join(self.json_dir, f"{smithsonian_id}.json")
        graph_json = self.fetch(smithsonian_id)
        try:
            with open(json_file, "w") as write_file:
                json.dump(graph_json['data'], write_file, indent=2)
                print(f"🗃️ Saved to: {json_file}")
                return graph_json['data']
        except Exception as e:
            print(f"{e}")

    def values_to_df(self, values: Dict[str, Any], volcano: Dict[str, str], value_type: str = 'SO2') -> pd.DataFrame:
        """Values to dataframe.

        Args:
            values (Dict[str, Any]): Values of SO2 or Thermal.
            volcano (Dict[str, str): Volcano name, code, and smithsonian_id
            value_type (str): Value type. Defaults to 'SO2'.

        Returns:
            pd.DataFrame: Values to dataframe.
        """
        df = pd.DataFrame.from_dict(values)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['date'] = df['datetime'].apply(lambda _datetime: _datetime.strftime("%Y-%m-%d"))
        df['time'] = df['datetime'].apply(lambda _datetime: _datetime.strftime("%H:%M:%S"))
        df['type'] = value_type
        df['name'] = volcano['name']
        df['code'] = volcano['code']
        df['smithsonian_id'] = volcano['smithsonian_id']

        # Rearrange columns
        df = df.loc[:, ['datetime', 'date', 'time', 'type', 'name', 'code', 'smithsonian_id', 'value', 'image']]

        df.set_index('datetime', inplace=True)

        if self.include_anomaly is False:
            df = df[df['value'] > self.filter_value]

        return df

    @staticmethod
    def get_so2_values(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get SO2 values.

        Args:
            data (List[Dict[str, Any]): Values of SO2 from JSON.

        Returns:
            Dict[str, Any]: Values of SO2.
        """
        values = {
            'datetime': data[2]['x'],
            'value': data[2]['y'],
            'image': data[2]['text'],
        }
        return values

    @staticmethod
    def get_thermal_values(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get Thermal values.

        Args:
            data (List[Dict[str, Any]]): Values of Thermal in JSON.

        Returns:
            Dict[str, Any]: Values of Thermal in JSON.
        """
        values = {
            'datetime': data[0]['x'],
            'value': data[0]['y'],
            'image': data[0]['text'],
        }
        return values

    def save(self, df: pd.DataFrame, volcano_name: str, value_type: str = 'so2') -> None:
        """Save dataframe to file.

        Args:
            df (pd.DataFrame): Dataframe to save.
            volcano_name (str): Volcano name.
            value_type (str): Value type. Defaults to 'so2'.

        Returns:
            None
        """
        value_type: str = value_type.lower()
        excel_dir = os.path.join(self.output_directory, 'excel', value_type)
        os.makedirs(excel_dir, exist_ok=True)

        csv_dir = os.path.join(self.output_directory, 'csv', value_type)
        os.makedirs(csv_dir, exist_ok=True)

        excel_file = os.path.join(excel_dir, f"{volcano_name}.xlsx")
        csv_file = os.path.join(csv_dir, f"{volcano_name}.csv")

        df.to_excel(excel_file, index=True)
        df.to_csv(csv_file, index=True)
        print(f"=> ✅ Excel: {excel_file}")
        print(f"=> ✅ CSV: {csv_file}")

    def run(self) -> None:
        """Run mounts project scrapping.

        Returns:
            None
        """
        for index, volcano in enumerate(self.volcanoes):
            print(f"🌋 Extracting {volcano['name']} volcano.")
            data = self.write_json(volcano['smithsonian_id'])

            so2_df: pd.DataFrame = self.values_to_df(
                self.get_so2_values(data), volcano=volcano)
            thermal_df: pd.DataFrame = self.values_to_df(
                self.get_thermal_values(data), volcano=volcano, value_type='Thermal')

            self.save(so2_df, volcano['name'])
            self.save(thermal_df, volcano['name'], value_type='thermal')
        print(f"\n✅ Done!")
