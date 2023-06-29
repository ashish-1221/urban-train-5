import matplotlib.patheffects as pe
import streamlit as st
import pandas as pd
import geopandas as gd
import numpy as np
from scipy.spatial import cKDTree
import os.path
import folium
from streamlit_folium import st_folium,folium_static
from folium.plugins import Draw
from folium import Map, FeatureGroup, Marker, LayerControl
import warnings
warnings.filterwarnings('ignore')
import shapefile
import folium
from folium.plugins import Search
from folium.plugins import *
import branca.colormap
from st_aggrid import AgGrid,GridUpdateMode,JsCode,DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from gdrive import *
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from collections import OrderedDict
import io

## Setting the main page conditions
st.set_page_config(
    page_title="FPI_Census_Maps_easy",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)



## Creating the session state
if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False       


st.info("Currently for MP State, can be pushed out to all states")
st.warning("Enter the Mapping Sheet Id ==> 1bqcgyBNVJ5jOZnrJPxqQNnWsLYTJIlyCm6yKfTTkaTg")
st.info("Filter out the AC, Village, Locality in the Table")
st.info("Colour Scales Represent Mandals")
st.info("Red Boundary Represents Locality")
st.info("Blue dashed Boundary represents Village Shapes")
    
## UDF for reading the village Shape file of the selected State Name
@st.cache_data(persist=True)
def return_v_gdf(st_name):
    print("reading the village Shape File")
    print("\n")
    village_file_path = (os.path.join(os.getcwd(),"data","shapefiles","SHP_MadhyaPradesh","VILLAGE_TOWN.shp"))
    vill_shape_file = gd.read_file(village_file_path)
    vill_shape_file = vill_shape_file[['OID_','AC_POST','AC_NAME_PO','PC_NAME_PO','NAME11',
                                               'SUB_DIST11','DIST_11','geometry']]
    print("reading the AC Shape File")
    ac_file_path = (os.path.join(os.getcwd(),"data","shapefiles","SHP_MadhyaPradesh","AC_POST.shp"))
    ac_shape_file = gd.read_file(ac_file_path)
    print("Reading the State Shape file")
    st_shape_file = ac_shape_file.dissolve(by="STATE_UT").reset_index(drop=False)
    return vill_shape_file,ac_shape_file,st_shape_file

## UDF for the base map which which contain the state geography and the ac boundary
def state_and_ac_layer(ac_shape_file,st_shape_file,ac_no):
        lat = np.mean(ac_shape_file['geometry'].centroid.y) # Latitude of mean of ac_shape_files geometries
        lon = np.mean(ac_shape_file['geometry'].centroid.x) # Longitude of the mean of the ac_shape_file geometries
        m = folium.Map(location=[lat,lon],zoom_start = 5, tiles="openstreetmap")  # Creating a base map
        Draw(export=False).add_to(m)
        
        # Add the State Layer on the Map
        geoj = st_shape_file.to_json()
        folium.features.GeoJson(
            data=geoj,
            style_function = lambda x:
                {
                    'fillColor':'None',
                    'color':'blue',
                    'weight':'3'
                }
        ).add_to(m)
        
        # Add the AC Layer on top if it
        ac_shp = ac_shape_file[ac_shape_file['AC_NO'] == int(ac_no)]
        geo_j1 = ac_shp.to_json()
        folium.features.GeoJson(
            data=geo_j1,
            style_function=lambda x: {
                'fillColor': 'None',
                'color': 'red',
                'weight': '2'},
            tooltip=folium.features.GeoJsonTooltip(
                fields=['AC_NAME'],
                sticky=True
                )
        ).add_to(m)
        #
        return m
    

## Create a mandal map

## Standardization of columns
def col_standardize(base_retro,vill_shape_file,vill_loc):
    # Renaming the Columns and getting only the required columns
    base_retro = base_retro.rename(
                        columns={
                            'Mandal 01-Dec-22': 'Mandal',
                            'Locality': 'Locality'
                        }
                    )
    vill_shape_file = vill_shape_file.rename(
                        columns={
                            'OID_': 'VILL_ID',
                            'AC_POST': 'AC',
                            'NAME11': 'Village_Name',
                            'AC_NAME_PO':'AC_Name'
                        }
                    )
    
    vill_shape_file = vill_shape_file.loc[:,['VILL_ID','AC','AC_Name','Village_Name','geometry']]
    vill_loc = vill_loc[['AC','AC_Name','VILL_ID','Village_Name','Final_Locality','Final_Mandal']]
    vill_loc[['VILL_ID']] = vill_loc[['VILL_ID']].apply(pd.to_numeric)
    return base_retro,vill_shape_file,vill_loc


def get_data(base_retro,vill_shape_file,vill_loc,ac_no):
    base_retro = base_retro[base_retro['AC']==int(ac_no)]
    vill_shp = vill_shape_file[vill_shape_file['AC']==int(ac_no)]
    df1 = vill_shp.merge(vill_loc,on='VILL_ID',how='inner')
    return base_retro,vill_shp,vill_loc,df1

## Adding the Locality Layer on top of the folium map
def locality_layer(m,df1,ac_no):
    locality = df1.dissolve(['Final_Locality']).reset_index(drop=False)
    locality = locality[locality['AC_x']==int(ac_no)]
    # Adding the Feature Group having all the mandal with individual Colors
    fg2 = folium.FeatureGroup(name="Locality Layer")
    for x in locality.index:
        color = np.random.randint(16, 256, size=3)
        color = [str(hex(i))[2:] for i in color]
        color = '#'+''.join(color).upper()
        locality.at[x, 'color'] = color

    def style(feature):
        return {
            'fillColor': feature['properties']['color'],
            'color': feature['properties']['color'],
            'weight': 3,
            'fillOpacity': '0.7'

        }
    fg2.add_child(folium.GeoJson(
        locality,
        style_function=style,
        tooltip=folium.GeoJsonTooltip(
            
            fields=['Final_Locality'],
            labels=True,
            sticky=True
        )
    ))
    m.add_child(fg2)
    return m
    


def mandal_maps(m,df1,ac_no):
    mandal = df1.dissolve(['Final_Mandal']).reset_index(drop=False)
    mandal = mandal[mandal['AC_x'] == int(ac_no)]
    # Adding a feature group having all the mandal with individual colors
    fg3 = folium.FeatureGroup(name="Mandal Layer")
    for x in mandal.index:
        color = np.random.randint(16,256,size=3)
        color = [str(hex(i))[2:] for i in color]
        color = '#'+''.join(color).upper()
        mandal.at[x,'color'] = color
        
    def style(feature):
        return {
            'fillColor':feature['properties']['color'],
            'color':feature['properties']['color'],
            'weight':3,
            'fillOpacity':'0.4'
            
        }

    fg3.add_child(folium.GeoJson(
        mandal,
        style_function=style,
        tooltip=folium.GeoJsonTooltip(
            
            fields=['Final_Mandal'],
            labels=True,
            sticky=True
        )
       ))
    m.add_child(fg3)
    # Creating a feature group to show the individual mandal boundary and the villages present inside it.
    # Mandal boundary should be that only that only
    
    return m


## Adding a village layer on top of folium map
def vill_layer(m,df1):
    geo_j = df1.to_json()
    fg2 = folium.FeatureGroup(name="Village Layer")
    fg2.add_child(folium.features.GeoJson(
            data=geo_j,
            style_function=lambda x:
                {
                    'fillColor': 'yellow',
                    'color': 'blue',
                    'weight': '2',
                    'dashArray':'5,5',
                    'fillOpacity': '0.001'

                },
            tooltip=folium.features.GeoJsonTooltip(
                fields=['Village_Name_y','VILL_ID','Final_Mandal','Final_Locality'],
                aliases=['Village Name:-','Village_ID:-','Mandal:-','Locality:-']
                
            ),
            highlight_function=lambda x:
                {
                    'fillColor': 'blue',
                    'color': 'blue',
                    'weight': '4',
                    'fillOpacity': '0.02'
                }
        ))
    m.add_child(fg2)
    return m

## Calling the new Locality Layer
def locality_layer_1(m,df1,ac_no):
    locality = df1.dissolve(['Final_Locality']).reset_index(drop=False)
    locality = locality[locality['AC_x']==int(ac_no)]
    # Adding the Feature Group having all the mandal with individual Colors
    geo_j = locality.to_json()    
    fg2 = folium.FeatureGroup(name="Locality Layer (I)")
    fg2.add_child(folium.features.GeoJson(
        data=locality,
        style_function=lambda x:
        {
            'fillColor': 'None',
            'color': '#b22222',
            'weight': '2'

        },
        # tooltip=folium.features.GeoJsonTooltip(
        #     fields=['Village_Name_y', 'VILL_ID',
        #             'Final_Mandal', 'Final_Locality'],
        #     aliases=['Village Name:-', 'Village_ID:-',
        #              'Mandal:-', 'Locality:-']

        # ),
        highlight_function=lambda x:
        {
            'fillColor': 'None',
            'color': 'red',
            'weight': '6',
            'fillOpacity': 'None'
        }
    ))
    m.add_child(fg2)
    return m

    

## Major function to start the creation of all maps
def create_maps(base_retro,vill_shape_file,vill_loc):
            # getting only the data of the required ac
            ac_no = vill_loc['AC'].unique()[0]
            base_retro,vill_shp,vill_loc,df1 = get_data(base_retro,vill_shape_file,vill_loc,ac_no)
            # Calling the Maps having the ac and state boundary layer on top of basetile layer
            m = state_and_ac_layer(ac_shape_file,st_shape_file,ac_no)
            # Calling the mandal map function
            m = mandal_maps(m,df1,ac_no)
            #Calling the village layer function
            m = vill_layer(m,df1)
            # Calling the Locality Layer Function
            #m = locality_layer(m,df1,ac_no)
            # Calling the new Locality Layer
            m = locality_layer_1(m,df1,ac_no)
            return m



def geo_mandal(base_retro,vill_shape_file,vill_loc):
    ac_no = vill_loc['AC'].unique()[0]
    base_retro, vill_shp, vill_loc, df1 = get_data(
        base_retro, vill_shape_file, vill_loc, ac_no)
    fig,ax = plt.subplots(1,1,figsize=(8,12))
    cmap = plt.cm.Set1
    
    #Plotting the mandal and color each category via cmap
    df1 = df1.dissolve('Final_Mandal', as_index=False)
    df1.plot(ax=ax, cmap=cmap, linewidth=1.2, edgecolor='black')
    (df1.plot(ax=ax, color='None', linewidth=0.1, edgecolor='grey'))

    # Adding Legened
    legend_labels = df1['Final_Mandal'].to_list()
    legend_colors = cmap(np.linspace(0, 1, len(legend_labels)))
    lines = [Line2D([0], [0], marker="s", markersize=10, markeredgecolor='black', linewidth=0, color=c) for c in
             legend_colors]

    plt.legend(lines, legend_labels, prop={'size': 6}, framealpha=0, handletextpad=0.1,
               bbox_to_anchor=(1, 0), loc="lower left", labelspacing=1.0)

    # Adding level
    df1['rep'] = df1['geometry'].representative_point()
    df1['centroid'] = df1['geometry'].centroid
    za_points_1 = df1.copy()
    za_points_1.set_geometry('rep', inplace=True)
    za_points_2 = df1.copy()
    za_points_2.set_geometry('centroid', inplace=True)
    
    texts = []
    for x, y, label in zip(za_points_1.geometry.x,
                           za_points_1.geometry.y,
                           za_points_1["VILL_ID"]):  # +za_points_2.geometry.x)/2,+za_points_2.geometry.y)/2

        fp = matplotlib.font_manager.FontProperties(
            fname=r"fonts/FiraSans-ExtraBold.ttf")

        texts.append(plt.text(x, y, label, fontproperties=fp, horizontalalignment='center',
                              fontsize=2, 
                              path_effects=[pe.withStroke(linewidth=0.6,
                                                          foreground="white")]))

    ac = df1['AC_x'].unique()[0]
    ac_name = df1['AC_Name_x'].unique()[0]
    plt.title(f'AC -{ac} ({ac_name}) || Mandal Boundary')
    ax.axis('off')
    #st.pyplot(fig)
    
    
    # Save to file first or an image file has already existed.
    fn = f"{ac}.png"
    plt.savefig(fn,dpi=600)
    with open(fn, "rb") as img:
        btn = st.download_button(
            label="Download image",
            data=img,
            file_name=fn,
            mime="image/png"
        )
    
def form_callback():
    m = create_maps(base_retro, vill_shape_file, vill_loc_1)
    folium.LayerControl().add_to(m)
    folium_static(m, width=1100, height=500)




## Aggrid grid options builder
def aggrid_intializer(df):
    gd = GridOptionsBuilder.from_dataframe(df)
    gd.configure_pagination(enabled=False,paginationAutoPageSize=True)
    gd.configure_default_column(editable=True,filterable=True,groupable=True,enablePivot=True,enableValue=True,enableRowGroup=True)
    gd.configure_selection(selection_mode="multiple",use_checkbox=True)
    gridoptions = gd.build()
    grid_table = AgGrid(
        df,
        gridOptions=gridoptions,
        update_mode=GridUpdateMode.FILTERING_CHANGED|GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        theme="streamlit",
        height = 500,
        width = '100%',
        fit_columns_on_grid_load=False,
        reload_data=False,
        enable_enterprise_modules=True,
        header_checkbox_selection_filtered_only=True,
        use_checkbox=True
    )
    new_df = grid_table['data']
    return new_df



## Creating the container for inputs in the web page
with st.container():
        
        # # Reading the Data for the required files
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            st.file_uploader(label="Base Retro Data")
        with c2:
            st.file_uploader(label="Shape Files",accept_multiple_files=True)
        with c3:
            map_sheet_id = str(c3.text_input("Mapping Sheet Id"))
        with c4:
            el_year = st.selectbox('Election Year',(2018,2019))    
        vill_shape_file,ac_shape_file,st_shape_file = return_v_gdf("Madhya Pradesh")
        if el_year == 2018:
            base_path = os.path.join(os.getcwd(),"data","baseretro","2018_base_segmentation_MP.csv")
        else:
            base_path = os.path.join(os.getcwd(),"data","baseretro","2019_base_segmentation_MP.csv")
        base_retro = pd.read_csv(base_path)
        st.session_state.vill_loc = get_dataframe(map_sheet_id)
        base_retro, vill_shape_file, st.session_state.vill_loc = col_standardize(base_retro, vill_shape_file,st.session_state.vill_loc)
        ## multiple tabs reflecting diffrent types of maps
        tab1,tab2,tab3,tab4 = st.tabs(['Mandal Map','Vote Share Map','Win/Loss Map','Margin Map'])
        with tab1:
            vill_loc_1 =  aggrid_intializer(st.session_state.vill_loc)
            tab11,tab12 = st.tabs(['Generate Map','Import to Gsheet'])
            with tab11:
                form_callback()
                geo_mandal(base_retro,vill_shape_file,vill_loc_1)
            with tab12:
                st.info("Make sure no filters are present in the above mapping sheet")
                if st.button('Update to gsheet'):
                    Export_Data_To_Sheets(map_sheet_id,vill_loc_1)
                    st.snow()
                    st.success("Gsheet Updated")
                    
                    
                