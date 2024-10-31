import os
import json
import pandas as pd
import re
import requests
from typing import Any, Dict, List
from requests import Response

volcanoes: List[Dict[str, Any]] = [
    {
        "name": "Lewotobi Laki-laki",
        "code": 264180,
    },
    {
        "name": "Marapi",
        "code": 261140,
    },
    {
        "name": "Anak Krakatau",
        "code": 262000,
    },
    {
        "name": "Kerinci",
        "code": 261170,
    },
    {
        "name": "Karangetang",
        "code": 267020,
    },
    {
        "name": "Dukono",
        "code": 268010,
    },
    {
        "name": "Ili Lewotolok",
        "code": 264230,
    },
    {
        "name": "Ibu",
        "code": 268030,
    },
    {
        "name": "Semeru",
        "code": 263300,
    },
    {
        "name": "Raung",
        "code": 263340,
    },
    {
        "name": "Ijen",
        "code": 263350,
    },
    {
        "name": "Slamet",
        "code": 263180
    }
]


class MountsProject:
    URL: str = "http://mounts-project.com/timeseries/"

    def __init__(self, include_anomaly: bool = False, filter_value: float = 0.1,
                 output_directory: str = None):
        self.include_anomaly = include_anomaly
        self.filter_value = filter_value

        self.output_directory: str = output_directory
        if output_directory is None:
            self.output_directory = os.path.join(os.getcwd(), 'output')
        os.makedirs(self.output_directory, exist_ok=True)

        self.json_dir: str = os.path.join(self.output_directory, 'json')
        os.makedirs(self.json_dir, exist_ok=True)

        self.volcanoes: List[Dict[str, Any]] = volcanoes
        self.df: pd.DataFrame = pd.DataFrame()

    @staticmethod
    def get_json_from_javascript(text: Any) -> Dict[str, Any]:
        var_graph = re.search(r"(?:^|\s|;)var\s+graph\s*=\s*([^']+})", text)
        string_graph = var_graph.group(1)
        json_graph = json.loads(string_graph)
        return json_graph

    @staticmethod
    def fetch(volcano_code: str) -> Dict[str, Any]:
        url = f"{MountsProject.URL}{volcano_code}"
        response: Response = requests.get(url)
        return MountsProject.get_json_from_javascript(response.text)

    def write_json(self, volcano_code: str):
        json_file = os.path.join(self.json_dir, f"{volcano_code}.json")
        graph_json = self.fetch(volcano_code)
        try:
            with open(json_file, "w") as write_file:
                json.dump(graph_json['data'], write_file, indent=2)
                print(f"🗃️ Saved to: {json_file}")
                return graph_json['data']
        except Exception as e:
            print(f"{e}")

    def values_to_df(self, values: Dict[str, Any], volcano_code: str,
                     volcano_name: str, value_type: str = 'SO2') -> pd.DataFrame:
        df = pd.DataFrame.from_dict(values)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['date'] = df['datetime'].apply(lambda x: x.strftime("%Y-%m-%d"))
        df['time'] = df['datetime'].apply(lambda x: x.strftime("%H:%M:%S"))
        df['type'] = value_type
        df['code'] = volcano_code
        df['volcano_name'] = volcano_name
        df.set_index('datetime', inplace=True)

        if self.include_anomaly is False:
            df = df[df['value'] > self.filter_value]

        return df

    @staticmethod
    def get_so2_values(data) -> Dict[str, Any]:
        values = {
            'datetime': data[2]['x'],
            'value': data[2]['y'],
            'image': data[2]['text'],
        }
        return values

    @staticmethod
    def get_thermal_values(data) -> Dict[str, Any]:
        values = {
            'datetime': data[0]['x'],
            'value': data[0]['y'],
            'image': data[0]['text'],
        }
        return values

    def save(self, df: pd.DataFrame, volcano_name: str, value_type: str = 'so2'):
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

    def run(self):
        for index, volcano in enumerate(self.volcanoes):
            volcano_code = volcano['code']
            volcano_name = volcano['name']
            print(f"🌋 Extracting {volcano_name} volcano.")
            data = self.write_json(volcano_code)
            so2_df: pd.DataFrame = self.values_to_df(
                self.get_so2_values(data), volcano_code, volcano_name)
            thermal_df: pd.DataFrame = self.values_to_df(
                self.get_thermal_values(data), volcano_code, volcano_name, value_type='Thermal')
            self.save(so2_df, volcano_name)
            self.save(thermal_df, volcano_name, value_type='thermal')
