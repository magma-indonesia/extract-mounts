#!/usr/bin/env python
# coding: utf-8

# # Data mining untuk Thermal dan SO2 dari web http://mounts-project.com
# ---

# ## Import Modules python yang dibutuhkan
# Adapun module yang digunakan antara lain:
# 1. Module `requests` digunakan untuk membuka web http://mounts-project.com
# 2. Module `json` digunakan untuk melakukan formatting data JSON
# 3. Module `re` digunakan untuk melakukan ekstraksi data JSON dari variable JavaScript menggunakan Regex
# 4. Module `pandas` digunakan untuk melakukan formatting data ke DataFrame dan converting ke Excel atau CSV
# 5. Module `os` digunakan untuk mendapatkan directory dan file
# 6. Module `JSON` digunakan untuk display data JSON

# In[1]:


import requests
import json
import re
import pandas as pd
import os
from IPython.display import JSON
from datetime import datetime


# ## Inisiasi Variable yang Dibutuhkan
# Inisiasi variable untuk web http://mounts-project.com

# In[2]:


mounts_url = 'http://mounts-project.com/timeseries/'


# Inisiasi variable untuk `output_directory` tempat hasil ekstrak data disimpan

# In[3]:


output_directory = os.path.join(os.getcwd(), 'output')

output_directory


# In[4]:


if (not os.path.exists(output_directory)):
    os.mkdir(output_directory)


# Variable `volcanoes` merupakan variable kode gunung api berdasarkan ID smithsonian number (https://volcano.si.edu/).  
# Untuk mendapatkan data beberapa gunung api, masukkan kode gunung api dalam bentuk `list`

# In[5]:


volcanoes = [
    {
        "name" : "Anak Krakatau",
        "code" : 262000,
    },
    {
        "name" : "Kerinci",
        "code" : 261170,
    },
    {
        "name" : "Karangetang",
        "code" : 267020,
    },
    {
        "name" : "Dukono",
        "code" : 268010,
    },
    {
        "name" : "Ili Lewotolok",
        "code" : 264230,
    },
    {
        "name" : "Ibu",
        "code" : 268030,
    },
    {
        "name" : "Semeru",
        "code" : 263300,
    },
    {
        "name" : "Raung",
        "code" : 263340,
    },
    {
        "name" : "Ijen",
        "code" : 263350,
    }
]


# In[6]:


for index, volcano in enumerate(volcanoes):
    print(volcano['name'], volcano['code'])


# Menginisiasi list kosong untuk menyimpan DataFrame hasil ekstraksi data. List ini akan berisi kumpulan data Thermal dan SO2 dari berbagai gunung api

# In[7]:


dataframes = {}


# ---
# ## Inisiasi Fungsi-fungsi yang digunakan untuk extract, transformasi, dan export data
# Fungsi yang digunakan untuk mengeskstrak variable JSON Thermal dan SO2 dari JavaScript web Mounts Project. Variabel ini tersimpan dengan nama `var_graph`

# In[8]:


def get_json_from_javascript(response):
    var_graph = re.search(r"(?:^|\s|;)var\s+graph\s*=\s*([^']+})", response.text)
    string_graph = var_graph.group(1)
    json_graph = json.loads(string_graph)
    return json_graph


# Hasil dari ekstraksi JSON pada fungsi `get_json_from_javascript` selanjutnya digunakan untuk extraksi nilai **SO2** dan **Thermal**

# In[9]:


def get_so2_values(graph_json):
    so2_values = {
        'Date time': graph_json['data'][2]['x'],
        'Value': graph_json['data'][2]['y'],
    }
    so2_df = pd.DataFrame.from_dict(so2_values)
    so2_df['Type'] = 'SO2'
    return so2_df


# In[10]:


def get_thermal_values(graph_json):
    thermal_values = {
        'Date time': graph_json['data'][0]['x'],
        'Value': graph_json['data'][0]['y'],
    }
    thermal_df = pd.DataFrame.from_dict(thermal_values)
    thermal_df['Type'] = 'Thermal'
    return thermal_df


# Splitting kolom `Date Time` ke `Date` dan `Time`

# In[11]:


def convert_to_date(date_time):
    return date_time.strftime("%Y-%m-%d")


# In[12]:


def convert_to_time(date_time):
    return date_time.strftime("%H:%M:%S")


# Fungsi ini digunakan untuk meng-export data hasil ekstraksi ke dalam format Excel

# In[13]:


def export_to_excel(filtered_df, volcano_code, volcano_name):
    filename = '{} - {}.xlsx'.format(volcano_name, volcano_code)
    path = os.path.join(output_directory, filename)
    filtered_df.to_excel(path, sheet_name='Join Data')
    return path


# ---
# ## Kode Utama
# Kode utama ekstraksi data

# In[14]:


df_excel = pd.DataFrame()

for index, volcano in enumerate(volcanoes):
    volcano_code = volcano['code']
    volcano_name = volcano['name']
    
    # http://mounts-project.com/timeseries/262000
    url = mounts_url+str(volcano_code) 
    
    # Buka http://mounts-project.com/timeseries/262000
    response = requests.get(url)
    
    # Get data JSON
    graph_json = get_json_from_javascript(response)
    
    so2 = get_so2_values(graph_json)
    thermal = get_thermal_values(graph_json)
    
    df = pd.concat([
        so2,
        thermal
    ])
    
    df['Date time'] = pd.to_datetime(df['Date time'])
    df['Date'] = df['Date time'].apply(convert_to_date)
    df['Time'] = df['Date time'].apply(convert_to_time)
    df['Code'] = volcano_code
    df.set_index('Date time', inplace=True)
    
    filtered_df = df[df['Value'] > 0.1]
    dataframes[volcano_name] = filtered_df
    
    df_excel = pd.concat([
        df_excel, pd.DataFrame([{
            "code" : volcano_code,
            "volcano_name" : volcano_name,
            "filename" : export_to_excel(filtered_df, volcano_code, volcano_name),
            "updated_at" : filtered_df.index.max()
    }])], ignore_index=True)
    
    print("Data untuk gunung api {} berhasil diekstrak, dan disimpan dalam variable dataframes['{}']".format(volcano_name,volcano_name))


# In[15]:


df_excel


# In[16]:


df_excel.to_excel('output.xlsx', index=False)
