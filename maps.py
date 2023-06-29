import os
import streamlit as st
import pandas as pd
import geopandas as gd
import numpy as np
from scipy.spatial import cKDTree
from maps_class import *
import os.path
import pandas as pd
from gdrive import *


## Store the initial value of widgets in session state
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False


#! Input Parameters for Generating Maps
## Input Consolidation for the Maps.py 
## (User Input(ST_SHP,Base Folder ID,Mapping Folder ID,Map Generation Format,ST_NAME,ELection Type,Election Year,AC))
## Data Returned (State Shape File,Base Retro Data(AC Filtered),Mapping FIle(rer. AC),ST_NAME,Map Type,Election Year,Election Type,AC)

with st.container():
    
    #! Download the shape files from EDM-DB/Internal team Resources/00_ShapeFiles folder
    # Creating a drive_object instance of class drive_api() in gdrive.py
    drive_object = drive_api()
    # Calling main Function in drive_api class
    
    # folders = drive_object.connect_EDM_DB()  # Connecting to EDM Folder
    # print(folders)
    # itr_info = {}  # getting the information for the Internal team Resources Folder
    # for f_id, f_info in folders.items():
    #     if f_id == 'Internal Team Resources':
    #         itr_info['name'] = f_id
    #         for key in f_info:
    #             if key == 'id':
    #                 itr_info['id'] = f_info[key]
    #             else:
    #                 itr_info['parent'] = f_info[key]
    # print(itr_info)
    # # Getting the information of all subfolders in Internal Team Resources Folder
    # folders = drive_object.search_a_folder(itr_info['id'])
    # #Getting all the info of  00_Shapefiles folder in Internal Team Resources Folder
    # folder_info = {}
    # for item in folders:
    #     if item['name'] == '00_Shapefiles(Copy)':
    #         folder_info['name'] = item['name']
    #         folder_info['id'] = item['id']
    #         folder_info['parent'] = item['parents']
    # print("\n\n")
    # print(folder_info)
    # # Getting info of all subfolders in the 00_ShapeFiles folder
    # folders = drive_object.search_a_folder(folder_info['id'])
    # print("\n\n")
    # print(folders)
    # # Creating a Select box to Select the State to make Shape of

    # # Creating a set of all file names of shape files
    # shp_names = [None]
    # for item in folders:
    #     shp_names.append(item['name'])
    # print("\n\n")
    # print(shp_names)

    # Downloading the shape file and storing it in data/shapefiles folder for the selected state
    ## Select the shape file of the state you want maps for (Streamlit Front end Section)
    shape_file_folderId = st.sidebar.text_input(
        "Shape File Folder ID",
        label_visibility=st.session_state.visibility,
        disabled=st.session_state.disabled,
        key="9"
    )
    #print(f"\n\n{sel_option}")
    ##Getting the folder info of the required state (useful:name)
    #shape_info = [item for item in folders if item['name'] == sel_option][0]
    #print("\n\n")
    #print(shape_info)
    # create a new folder with state name for the downloads
    exist = False
    # try:
    #     dir = "data/shapefiles/"+shape_info['name']+"/"
    #     os.mkdir(dir)
    #     print("Directory is created")
    # except FileExistsError:
    #     print("Directory already exists")
    #     exist = True
    # # Getting all subfolder info inside the state folder
    # folders = drive_object.search_a_folder(shape_info['id'])
    # print("\n\n")
    # print(folders)
    # # TODO: To make sure when the drive is updated with new files to include those files in this data
    # # TODO : To make sure if all file exists do not download it again and again
    # # Download all files present in the subfolder info
    # if exist == False:
    #     drive_object.export_all_files(folders[0]['id'], dir)

    # Get the AC values from the ac_shape_file
    path = "data/shapefiles/"+"SHP_MadhyaPradesh"+"/"+"AC_POST.shp"
    ac_shp = pd.DataFrame(gd.read_file(path).drop(["geometry"], axis=1))
    ac_list = set(sorted(ac_shp['AC_NO'].to_list()))

    ## Get the Folder id of the Base Retro Path
    base_retro_folder_id = st.sidebar.text_input(
        "Base Retro Folder ID", label_visibility=st.session_state.visibility, disabled=st.session_state.disabled, key="5")
    ## GEt the Folder Id of the Mapping File
    mapping_file_folder_id = st.sidebar.text_input(
        "Mapping Files Folder ID", label_visibility=st.session_state.visibility, disabled=st.session_state.disabled, key="6")

    ## Select the Map format you want
    map_type = st.sidebar.radio("Choose Map Generation Format",
                                ("Mandal Map",
                                 "Win/Loss",
                                 "Vote Share",
                                 "Margin")
                                )
    print(f"\n\n{map_type}")
    
    
    ## Get Election Year, Election Type and State Name and AC
    
    
    #* Store the initial value of widgets in session state
    # Create a container for state_name
    c1, c2, c3, c4 = st.columns(4)
    
    
    #* Get State Name
    #with c1.container():
    #c1.subheader("State Name")
    st_name = c1.text_input("State Name", 
                            label_visibility=st.session_state.visibility,
                            disabled=st.session_state.disabled, key="1")
    
    
    #* Get Election Type
    election_type = c2.selectbox(
        "Election Type", ('LS', 'VS', 'Bye-polls'), key="2")
    
    #* Get Election year
    election_year = c3.text_input(
        "Election year", label_visibility=st.session_state.visibility, disabled=st.session_state.disabled, key="3")
    #*AC Select
    ac = c4.selectbox("AC", ac_list, key="4")

    #* Submit button 
    submitted = st.button('Submit')
    if submitted:
    
    
        ## Data Collection for calling the mandal maps class
        # Data Needed -> ST_NAME,Election Year,Election Type, AC, Village Shape File(AC), Base Retro File(AC),Mapping File(AC)
        
        #*Mapping Files of the required AC
        print("\n\nFound the AC File")
        print("Mapping File of the Excel Info")
        #connect to grive and get the mapping file
        mapping_files_excel_list = drive_object.search_a_folder_q_param(
            f"mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and '{mapping_file_folder_id}' in parents and name contains '{ac}'")
        for file in mapping_files_excel_list:
            if (file['name'].split("."))[0] == str(ac):
                ac_mapping_file_info = file
        print(ac_mapping_file_info)
    
        # Base Retro Data of the required_file (AC Filtered)
        base_retro_excel_list = drive_object.search_a_folder_q_param(
            f"mimeType='text/csv' and '{base_retro_folder_id}' in parents")
        print(base_retro_excel_list)
        for file in base_retro_excel_list:
            if str(st_name) in file['name']:
                if str(election_year) in file['name'] :
                    base_retro_file_info = file
        print("\n\n Base Retro File Found")
        print(base_retro_file_info)
        
        ## Download the Base retro file and mapping file of the AC
        base_retro_folder_path = "data/baseretro/"
        mapping_file_folder_path = "data/mappingfile/"
        print("Reading AC Mappping File")
        ac_mapping_file = export_the_file(ac_mapping_file_info,mapping_file_folder_path)
        print("Reading Base Retro File")
        base_retro_data = export_the_file(base_retro_file_info,base_retro_folder_path)
        ## Calling the Mandal Maps Function to plot a map
        
        
        # Subsetting the dataset for faster computation

        vill_shp = return_v_gdf()
        vill_shp = vill_shp[vill_shp['AC_POST']==ac]
        print("Read Village Shape File")
        
        
        
        
        ## Creation of mandal maps
        ac_mapping_file,vill_shp = rename(vill_shp=vill_shp,ac_mapping_file=ac_mapping_file)
        mandal_map = mapping_files(base_retro_data,ac_mapping_file,vill_shp)
        #ac_mapping_file,vill_shp = mandal_map.rename()
        print("\n\nStep_1")
        ac_shape_file,ac_name = mandal_map.basic_correction_and_explode()
        # subsetting the base_retro_data as base_retro_1
        base_retro_ac =return_base_retro_data(base_retro_data=base_retro_data,ac=ac)   
        
        
        ## Create Mandal Maps
        if map_type=="Mandal Map":
            mandal_maps(ac,ac_shape_file,ac_name,"data")
        ## Create win/loss maps
        elif map_type == 'Win/Loss': 
            win_loss_maps(ac_shape_file,base_retro_ac,vill_shp,ac,ac_name,election_type,election_year,"data")
        ## Create Vote Share Maps
        elif map_type =='Vote Share':
            vs_maps_creation(ac_shape_file,base_retro_ac,vill_shp,ac,ac_name,election_type,election_year,"data")
        else:
            margin_maps_creation(ac_shape_file,base_retro_ac,vill_shp,ac,ac_name,election_type,election_year,"data")





