import os
import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode,JsCode
import geopandas as gd
import numpy as np
import folium
import streamlit_folium as st_folium


@st.cache
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')
# Delete previous definitio in dat\map_data

st.title("Basic Checks")
# """Show the files and take the required columns"""

# """CAPI Sheet"""
st.header("CAPI Sheet")




capi_file = pd.read_csv(r"data\\capi_file_master.csv",skiprows=1)
gb = GridOptionsBuilder.from_dataframe(capi_file,editable=True,filterable=True,groupable=True)
# gb.configure_pagination(paginationAutoPageSize=Fas,paginationPageSize=50) #Add pagination
gb.configure_side_bar(filters_panel=True,columns_panel=True) #Add a sidebar
#gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
# Configure grid options

gridOptions = gb.build()

grid_response = AgGrid(
    capi_file,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.MODEL_CHANGED|GridUpdateMode.SELECTION_CHANGED|GridUpdateMode.GRID_CHANGED|GridUpdateMode.FILTERING_CHANGED|GridUpdateMode.VALUE_CHANGED,
    fit_columns_on_grid_load=False,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    header_checkbox_selection_filtered_only=True,
    theme='streamlit',  # Add theme color to the table
    enable_enterprise_modules=True,
    height=500,
    width='100%',
    reload_data=True,
    allow_unsafe_jscode=True
    
)
data1 = grid_response['data']
selected1 = grid_response['selected_rows']
capi_file1 = pd.DataFrame(data1)

csv = convert_df(capi_file1)
st.download_button(
    "Export as csv",
    csv,
    "capi.csv",
    mime="text/csv"
)

capi_file1.to_csv(r"data\map_data\capi_file.csv")

# """Booth Location Information"""
st.header("Booth Location Information")
booth_file = pd.read_csv(r"data\\booth_loc_master.csv")
gb = GridOptionsBuilder.from_dataframe(booth_file,editable=True,filterable=True,groupable=True)
#gb.configure_pagination(paginationAutoPageSize=True,paginationPageSize=3) #Add pagination
gb.configure_side_bar() #Add a sidebar
gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
gridOptions = gb.build()

grid_response1 = AgGrid(
    booth_file,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.MODEL_CHANGED|GridUpdateMode.SELECTION_CHANGED|GridUpdateMode.GRID_CHANGED,
    fit_columns_on_grid_load=False,
    data_return_mode=DataReturnMode.FILTERED,
    header_checkbox_selection_filtered_only=True,
    theme='streamlit',  # Add theme color to the table
    enable_enterprise_modules=True,
    height=500,
    width='100%',
    reload_data=True
)
data = grid_response1['data']
selected = grid_response1['selected_rows']
booth_file1 = pd.DataFrame(data)
booth_file1.to_csv(r"data\map_data\booth_file.csv")


# Merge the files
# Reading the filtered files
capi_file1 = pd.read_csv(r"data\map_data\capi_file.csv")
booth_file1 = pd.read_csv(r"data\map_data\booth_file.csv")
merged_file = pd.merge(capi_file1,booth_file1,how='outer',on='key')





