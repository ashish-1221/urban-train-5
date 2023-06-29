import streamlit as st
from gdrive import *
import geopandas as gd
import os
import pandas as pd
from scipy.spatial import cKDTree
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from collections import OrderedDict
import folium
from streamlit_folium import st_folium


@st.cache_data(persist=True)
def return_v_gdf():
    vill_shp = gd.read_file("data/shapefiles/"+"SHP_MadhyaPradesh"+"/"+"VILLAGE_TOWN.shp")
    return vill_shp

@st.cache_data(persist=True)
def return_ac_gdf(ac):
    ac_shp = gd.read_file("data\shapefiles\SHP_MadhyaPradesh\AC_POST.shp")
    return ac_shp


def return_base_retro_data(base_retro_data,ac):
    return base_retro_data[base_retro_data['AC']==ac]


##Margin Maps Integration
# Margin map
def margin_category(mac):
    if mac < -40:
        return "< -40%"
    elif (mac >= -40) and (mac < -20):
        return "-40% to -20%"
    elif (mac >= -20) and (mac < 0):
        return "-20% to 0%"
    elif (mac >= 0) and (mac < 20):
        return "0% to 20%"
    elif (mac >= 20) and (mac < 40):
        return "20% to 40%"
    else:
        return "> 40%"


def margin_color(mc):
    if mc == "< -40%":
        return '#B20000'
    elif mc == "-40% to -20%":
        return '#FF0000'
    elif mc == "-20% to 0%":
        return '#FF5C5C'
    elif mc == "0% to 20%":
        return '#EBFB1F'
    elif mc == "20% to 40%":
        return '#90EE90'
    else:
        return '#138808'


def margin_maps(ac, final1, vill_shp1, ac_shape_file, ac_name, election_year, election_type,
                final_map_folder_path):

    final1['margin category'] = final1['BJP Margin %'].apply(lambda x: margin_category(x))
    final1['hex_margin'] = final1['margin category'].apply(lambda x: margin_color(x))

    fig, ax = plt.subplots(1, 1, figsize=(8, 10))

    df_final1 = vill_shp1.merge(final1, how='left', on='V_ID')
    color_dict = dict(df_final1[['margin category', 'hex_margin']].values)
    category = ['< -40%', '-40% to -20%', '-20% to 0%', '0% to 20%', '20% to 40%', '> 40%']
    color_dict = {k: color_dict[k] for k in category if k in color_dict}

    # plotting margin df
    df_final1.plot(ax=ax, column='margin category', color=df_final1['hex_margin'], linewidth=0.15,
                   edgecolor='grey')

    # plotting Mandal boundary
    ac_shape_file_shp = ac_shape_file.dissolve('MANDAL', as_index=False)
    ac_shape_file_shp.plot(ax=ax, color='None', linewidth=1.2, edgecolor='black')

    # Adding title
    plt.title(
        f'{election_type} {election_year} Elections || AC -{ac} ({ac_name}) || Village Level BJP Margin with Mandal Boundary')

    # Adding legend
    lines = [Line2D([0], [0], marker="s", markersize=10,
                    markeredgecolor='black', linewidth=0, color=c) for c in color_dict.values()]
    labels = [x for x in color_dict.keys()]

    plt.legend(lines, labels, prop={'size': 8}, framealpha=0, handletextpad=0.1, bbox_to_anchor=(1.05, 0),
               loc="lower left", labelspacing=1.2)

    # Adding level
    df_final1['rep'] = df_final1['geometry'].representative_point()
    df_final1['centroid'] = df_final1['geometry'].centroid

    za_points_1 = df_final1.copy()
    za_points_1.set_geometry('rep', inplace=True)
    za_points_2 = df_final1.copy()
    za_points_2.set_geometry('centroid', inplace=True)
    texts = []
    for x, y, label in zip(za_points_1.geometry.x,
                           za_points_1.geometry.y,
                           za_points_1["V_ID"]):  # +za_points_2.geometry.x)/2,+za_points_2.geometry.y)/2

        fp = matplotlib.font_manager.FontProperties(fname=r"fonts/FiraSans-ExtraBold.ttf")

        texts.append(plt.text(x, y, label, fontproperties=fp, horizontalalignment='center',
                              fontsize=2.3, path_effects=[pe.withStroke(linewidth=0.6,
                                                          foreground="white")]))

    ax.axis('off')
    st.pyplot(fig)
    # Save the map into mandal boundary folder
    if not os.path.exists(final_map_folder_path + "\\" + "margin map"):
        os.makedirs(final_map_folder_path + "\\" + "margin map")
        plt.savefig(final_map_folder_path + "\\" + "margin map" + "\\" + str(ac) + ".png", bbox_inches='tight',
                    dpi=600)
    else:
        plt.savefig(final_map_folder_path + "\\" + "margin map" + "\\" + str(ac) + ".png", bbox_inches='tight',
                    dpi=600)




## Win Loss Maps Integration
# calculating VS, Margin, Rank1&2 party from Base retro
def vs_margin_win_loss(df_retro, ac, election_year):
    ac_ = 'AC'
    level = 'V_ID'
    party = 'mapped_party'
    candidate = 'name' 
    mapped_year = 'booth 2022'
    mapped_ps = election_year + ' Mapped PS'
    votes = 'Adjusted Votes'

    df_retro_1 = df_retro.copy()

    # rolling up on locality level
    df2 = df_retro_1.groupby([ac_,party, level,candidate], as_index=False).agg(
        {mapped_year: lambda x: "+".join(set(map(str, x))), votes: 'sum'})

    err = []
    lst = []
    for i in df2[level].unique()[:]:
        try:
            df3 = df2.loc[df2[level] == i]
            df3['Rank'] = df3[votes].rank(ascending=False, method='first')

            total_votes = df3[votes].sum()
            df3['Total Votes'] = total_votes

            r1_party = df3.loc[df3['Rank'] == 1][party].values[0]
            r1_votes = df3.loc[df3['Rank'] == 1][votes].values[0]

            df3['Rank 1 Party'] = r1_party
            df3['Rank 1 Votes'] = r1_votes

            if len(df3.loc[df3['Rank'] == 2]) == 0:
                r2_party = '-'
                r2_votes = 0

            else:
                r2_party = df3.loc[df3['Rank'] == 2][party].values[0]
                r2_votes = df3.loc[df3['Rank'] == 2][votes].values[0]

            df3['Rank 2 Party'] = r2_party
            df3['Rank 2 Votes'] = r2_votes

            if len(df3.loc[df3[party] == 'BJP']) == 0:
                bjp_votes = 0

            else:
                bjp_votes = df3.loc[df3[party] == 'BJP'][votes].values[0]

            df3['BJP Votes'] = bjp_votes

            df3['BJP Vote Share %'] = round(df3['BJP Votes'] / df3['Total Votes'] * 100, 2)

            if df3.loc[df3['Rank'] == 1][party].values[0] == 'BJP':
                bjp_margin = bjp_votes - r2_votes
            else:
                bjp_margin = bjp_votes - r1_votes

            df3['BJP Margin Votes'] = bjp_margin
            df3['BJP Margin %'] = round(df3['BJP Margin Votes'] / df3['Total Votes'] * 100, 2)

            df3 = df3.fillna(0)
            df4 = df3.drop([party, candidate, votes, 'Rank'], axis=1).drop_duplicates()

            if len(df4) > 1:
                df4[mapped_ps] = '+'.join(df4[mapped_ps].str.split('+').sum())
                df4 = df4.drop_duplicates()

            lst.append(df4)

        except Exception as ee:
            err.append([ac, i, ee])

    final_df = pd.concat(lst)
    return final_df


def win_loss_map(ac, vill_shp1, final1, ac_shape_file, ac_name, election_year, election_type,
                 final_map_folder_path):
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    df_final1 = vill_shp1.merge(final1, how='left', on='V_ID')

    condition_list_1 = [df_final1['Rank 1 Party'] == 'BJP',
                        df_final1['Rank 1 Party'] == 'INC',
                        df_final1['Rank 1 Party'] == 'BSP',
                        ~df_final1['Rank 1 Party'].isin(['BJP', 'INC', 'BSP'])]

    choice_list_1 = ['#FF9900', '#00FFFF', '#E75480', '#D3D3D3']

    df_final1['Hexcode_Rank 1 Party'] = np.select(condition_list_1, choice_list_1)
    color_dict = dict(df_final1[['Rank 1 Party', 'Hexcode_Rank 1 Party']].values)
    color_dict = OrderedDict(sorted(color_dict.items()))

    # plotting win loss df
    df_final1.plot(ax=ax, column='Rank 1 Party', color=df_final1['Hexcode_Rank 1 Party'], linewidth=0.25,
                   edgecolor='grey')

    # plotting Mandal Boundary
    ac_shape_file_shp = ac_shape_file.dissolve('MANDAL', as_index=False)
    ac_shape_file_shp.plot(ax=ax, color='None', linewidth=1.2, edgecolor='black')

    # Adding Title
    plt.title(
        f'{election_type} {election_year} Elections || AC -{ac} ({ac_name}) || Village level WinLoss with Mandal Boundary')

    # Adding legend
    lines = [Line2D([0], [0], marker="s", markersize=10,
                    markeredgecolor='black', linewidth=0, color=c) for c in color_dict.values()]
    labels = [x for x in color_dict.keys()]

    plt.legend(lines, labels, prop={'size': 8}, framealpha=0, handletextpad=0.1,
               bbox_to_anchor=(1.05, 0), loc="lower left", labelspacing=1.2)

    # Adding Level
    df_final1['rep'] = df_final1['geometry'].representative_point()
    df_final1['centroid'] = df_final1['geometry'].centroid
    za_points_1 = df_final1.copy()
    za_points_1.set_geometry('rep', inplace=True)
    za_points_2 = df_final1.copy()
    za_points_2.set_geometry('centroid', inplace=True)

    texts = []
    for x, y, label in zip(za_points_1.geometry.x,
                           za_points_1.geometry.y,
                           za_points_1["V_ID"]):  # +za_points_2.geometry.x)/2,+za_points_2.geometry.y)/2

        fp = matplotlib.font_manager.FontProperties(fname=r"fonts/FiraSans-ExtraBold.ttf")

        texts.append(plt.text(x, y, label, fontproperties=fp, horizontalalignment='center',
                              fontsize=2.3,  # ))
                              path_effects=[pe.withStroke(linewidth=0.6,
                                                          foreground="white")]))

    ax.axis('off')
    st.pyplot(fig)
    # Save the map into mandal boundary folder
    if not os.path.exists(final_map_folder_path + "\\" + "win loss map"):
        os.makedirs(final_map_folder_path + "\\" + "win loss map")
        plt.savefig(final_map_folder_path + "\\" + "win loss map" + "\\" + str(ac) + ".png",
                    bbox_inches='tight', dpi=600)
    else:
        plt.savefig(final_map_folder_path + "\\" + "win loss map" + "\\" + str(ac) + ".png",
                    bbox_inches='tight', dpi=600)
        
def vs_maps(ac, final1, vill_shp1, ac_shape_file, ac_name, election_year, election_type, final_map_folder_path):
    final1['vs category'] = final1['BJP Vote Share %'].apply(lambda x: vs_category(x))
    final1['hex_vs'] = final1['vs category'].apply(lambda x: vs_color(x))
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))

    df_final1 = vill_shp1.merge(final1, how='left', on='V_ID')
    color_dict = dict(df_final1[['vs category', 'hex_vs']].values)
    color_dict = OrderedDict(sorted(color_dict.items()))
    # Plotting VS df
    df_final1.plot(ax=ax, column='vs category', color=df_final1['hex_vs'], linewidth=0.15, edgecolor='grey')

    # Adding mandal Boundary
    ac_shape_file_shp = ac_shape_file.dissolve('MANDAL', as_index=False)
    ac_shape_file_shp.plot(ax=ax, color='None', linewidth=1.2, edgecolor='black')

    # Adding title
    plt.title(
        f'{election_type} {election_year} Elections || AC -{ac} ({ac_name}) || Village Level BJP VS with Mandal Boundary')

    # Adding legend
    lines = [Line2D([0], [0], marker="s", markersize=10,
                    markeredgecolor='black', linewidth=0, color=c) for c in color_dict.values()]
    labels = [x for x in color_dict.keys()]

    plt.legend(lines, labels, prop={'size': 8}, framealpha=0, handletextpad=0.1, bbox_to_anchor=(1.05, 0),
               loc="lower left", labelspacing=1.2)

    # Adding level
    df_final1['rep'] = df_final1['geometry'].representative_point()
    df_final1['centroid'] = df_final1['geometry'].centroid
    za_points_1 = df_final1.copy()
    za_points_1.set_geometry('rep', inplace=True)
    za_points_2 = df_final1.copy()
    za_points_2.set_geometry('centroid', inplace=True)

    texts = []
    for x, y, label in zip(za_points_1.geometry.x,
                           za_points_1.geometry.y,
                           za_points_1["V_ID"]):
        fp = matplotlib.font_manager.FontProperties(fname=r"fonts/FiraSans-ExtraBold.ttf")

        texts.append(plt.text(x, y, label, fontproperties=fp, horizontalalignment='center',
                              fontsize=2.3, path_effects=[pe.withStroke(linewidth=0.6,
                                                                        foreground="white")]))

    ax.axis('off')
    st.pyplot(fig)
    # Save the map into mandal boundary folder
    if not os.path.exists(final_map_folder_path + "\\" + "vs map"):
        os.makedirs(final_map_folder_path + "\\" + "vs map")
        plt.savefig(final_map_folder_path + "\\" + "vs map" + "\\" + str(ac) + ".png", bbox_inches='tight',
                    dpi=600)
    else:
        plt.savefig(final_map_folder_path + "\\" + "vs map" + "\\" + str(ac) + ".png", bbox_inches='tight',
                    dpi=600)



def win_loss_maps(ac_shape_file,base_retro_1,vill_shp1,ac,ac_name,election_type,election_year,final_map_folder_path):    
    # exploding final df via booth no. so we can easily merge it with base retro
    ac_shape_file['BOOTH_NO'] = ac_shape_file['BOOTH_NO'].astype('str')
    df_ = ac_shape_file.groupby(['V_ID'], as_index=False).agg(
                    {'BOOTH_NO': lambda x: "+".join(list(map(str, x)))})
    df_['BOOTH_NO'] = df_['BOOTH_NO'].apply(lambda x: list(map(str, x.split('+'))))
    df_ex = df_.explode('BOOTH_NO', ignore_index=True)
    df_ex['BOOTH_NO'] = df_ex['BOOTH_NO'].astype('float')
    df_ex['BOOTH_NO'] = df_ex['BOOTH_NO'].astype('int')
    # merging base retro data with final df
    df_retro = pd.merge(df_ex, base_retro_1, right_on='booth 2022', left_on='BOOTH_NO', how='left')
    # Base retro function for calculating Rank1, VS, Margin
    final1 = vs_margin_win_loss(df_retro, ac, election_year)
    # WinLoss map function
    win_loss_map(ac, vill_shp1, final1, ac_shape_file, ac_name, election_year, election_type,
                                 final_map_folder_path)
def vs_category(vs):
    if (vs >= 0) and (vs <= 20):
        return "0% to 20%"
    elif (vs > 20) and (vs <= 40):
        return "20% to 40%"
    elif (vs > 40) and (vs <= 60):
        return "40% to 60%"
    elif (vs > 60) and (vs <= 80):
        return "60% to 80%"
    else:
        return "80% to 100%"


def vs_color(vc):
    if vc == "0% to 20%":
        return '#FF0000'
    elif vc == "20% to 40%":
        return '#FF5C5C'
    elif vc == "40% to 60%":
        return '#D0F0C0'
    elif vc == "60% to 80%":
        return '#90EE90'
    else:
        return '#138808'
    
def vs_maps_creation(ac_shape_file,base_retro_1,vill_shp1,ac,ac_name,election_type,election_year,final_map_folder_path):
    # exploding final df via booth no. so we can easily merge it with base retro
    ac_shape_file['BOOTH_NO'] = ac_shape_file['BOOTH_NO'].astype('str')
    df_ = ac_shape_file.groupby(['V_ID'], as_index=False).agg(
                    {'BOOTH_NO': lambda x: "+".join(list(map(str, x)))})
    df_['BOOTH_NO'] = df_['BOOTH_NO'].apply(lambda x: list(map(str, x.split('+'))))
    df_ex = df_.explode('BOOTH_NO', ignore_index=True)
    df_ex['BOOTH_NO'] = df_ex['BOOTH_NO'].astype('float')
    df_ex['BOOTH_NO'] = df_ex['BOOTH_NO'].astype('int')
    # merging base retro data with final df
    df_retro = pd.merge(df_ex, base_retro_1, right_on='booth 2022', left_on='BOOTH_NO', how='left')
    # Base retro function for calculating Rank1, VS, Margin
    final1 = vs_margin_win_loss(df_retro, ac, election_year)
    vs_maps(ac, final1, vill_shp1, ac_shape_file, ac_name, election_year, election_type,
                            final_map_folder_path)

def margin_maps_creation(ac_shape_file,base_retro_1,vill_shp1,ac,ac_name,election_type,election_year,final_map_folder_path):
    # exploding final df via booth no. so we can easily merge it with base retro
    ac_shape_file['BOOTH_NO'] = ac_shape_file['BOOTH_NO'].astype('str')
    df_ = ac_shape_file.groupby(['V_ID'], as_index=False).agg(
                    {'BOOTH_NO': lambda x: "+".join(list(map(str, x)))})
    df_['BOOTH_NO'] = df_['BOOTH_NO'].apply(lambda x: list(map(str, x.split('+'))))
    df_ex = df_.explode('BOOTH_NO', ignore_index=True)
    df_ex['BOOTH_NO'] = df_ex['BOOTH_NO'].astype('float')
    df_ex['BOOTH_NO'] = df_ex['BOOTH_NO'].astype('int')
    # merging base retro data with final df
    df_retro = pd.merge(df_ex, base_retro_1, right_on='booth 2022', left_on='BOOTH_NO', how='left')
    # Base retro function for calculating Rank1, VS, Margin
    final1 = vs_margin_win_loss(df_retro, ac, election_year)
    margin_maps(ac, final1, vill_shp1, ac_shape_file, ac_name, election_year, election_type,
                                final_map_folder_path)




def rename(vill_shp,ac_mapping_file):
            vill_shp = vill_shp[['OID_','AC_POST','AC_NAME_PO','NAME11','geometry']]
            vill_shp = vill_shp.rename(columns={'OID_':'V_ID','AC_POST':'AC','AC_NAME_PO':'AC NAME','NAME11':'V_NAME'})
            ac_mapping_file = ac_mapping_file[['AC','Village Id','Village Name','Mapped Locality','AC.1','booth 2022','Locality','Mandal 01-Dec-22']]  
            ac_mapping_file = ac_mapping_file.rename(
        columns={
            'Village Id':'V_ID',
            'Village Name':'V_NAME',
            'booth 2022':'BOOTH_NO',
            'Locality':'LOCALITY',
            'Mapped Locality':'MAPPED LOCALITY',
            'Mandal 01-Dec-22':'MANDAL'})
            return ac_mapping_file,vill_shp


def mandal_maps(ac, ac_shape_file, ac_name, final_map_folder_path):
    fig, ax = plt.subplots(1, 1, figsize=(8, 10))
    cmap = plt.cm.Set1

    # Plotting mandal and color each category via cmap
    ac_shape_file_shp = ac_shape_file.dissolve('MANDAL', as_index=False)
    ac_shape_file_shp.plot(ax=ax, cmap=cmap, linewidth=1.2, edgecolor='black')
    (ac_shape_file.plot(ax=ax, color='None', linewidth=0.1, edgecolor='grey'))

    # Adding legend
    legend_labels = ac_shape_file_shp['MANDAL'].to_list()
    legend_colors = cmap(np.linspace(0, 1, len(legend_labels)))
    lines = [Line2D([0], [0], marker="s", markersize=10, markeredgecolor='black', linewidth=0, color=c) for c in
             legend_colors]

    plt.legend(lines, legend_labels, prop={'size': 8}, framealpha=0, handletextpad=0.1,
               bbox_to_anchor=(1.05, 0), loc="lower left", labelspacing=1.2)

    # Adding level
    ac_shape_file['rep'] = ac_shape_file['geometry'].representative_point()
    ac_shape_file['centroid'] = ac_shape_file['geometry'].centroid
    za_points_1 = ac_shape_file.copy()
    za_points_1.set_geometry('rep', inplace=True)
    za_points_2 = ac_shape_file.copy()
    za_points_2.set_geometry('centroid', inplace=True)

    texts = []
    for x, y, label in zip(za_points_1.geometry.x,
                           za_points_1.geometry.y,
                           za_points_1["V_ID"]):  # +za_points_2.geometry.x)/2,+za_points_2.geometry.y)/2

        fp = matplotlib.font_manager.FontProperties(
            fname=r"fonts/FiraSans-ExtraBold.ttf")

        texts.append(plt.text(x, y, label, fontproperties=fp, horizontalalignment='center',
                              fontsize=2.3,  # ))
                              path_effects=[pe.withStroke(linewidth=0.6,
                                                          foreground="white")]))

    # Adding title
    plt.title(f'AC -{ac} ({ac_name}) || Mandal Boundary')
    ax.axis('off')
    st.pyplot(fig)
    # Save the map into mandal boundary folder
    if not os.path.exists(final_map_folder_path + "\\" + "mandal boundary map"):
        os.makedirs(final_map_folder_path + "\\" + "mandal boundary map")
        plt.savefig(final_map_folder_path + "\\" + "mandal boundary map" + "\\" + str(ac) + ".png",
                    bbox_inches='tight', dpi=600)
    else:
        plt.savefig(final_map_folder_path + "\\" + "mandal boundary map" + "\\" + str(ac) + ".png",
                    bbox_inches='tight', dpi=600)


class mapping_files():
    def __init__(self,base_retro,ac_mapping_file,vill_shp):
        self.base_retro = base_retro
        self.ac_mapping_file = ac_mapping_file
        self.vill_shp = vill_shp
        
    
    def rename(self):
            vill_shp = vill_shp[['OID_','AC_POST','AC_NAME_PO','NAME11','geometry']]
            vill_shp = vill_shp.rename(columns={'OID_':'V_ID','AC_POST':'AC','AC_NAME_PO':'AC NAME','NAME11':'V_NAME'})
            ac_mapping_file = ac_mapping_file[['AC','Village Id','Village Name','Mapped Locality','AC.1','booth 2022','Locality','Mandal 01-Dec-22']]  
            ac_mapping_file = ac_mapping_file.rename(
        columns={
            'Village Id':'V_ID',
            'Village Name':'V_NAME',
            'booth 2022':'BOOTH_NO',
            'Locality':'LOCALITY',
            'Mapped Locality':'MAPPED LOCALITY',
            'Mandal 01-Dec-22':'MANDAL'})
            return ac_mapping_file,vill_shp
    ##  Creation of two df from mapping file with required columns and dropping NaN values from df_man and df_vill
    ## (Mapping File DataFrame)->(df_man,df_vill)(done)
    def basic_correction_and_explode(self):
        
        def mapped_locality(df_vill_ex, df_man, vill_shp):
            df_loc_man = df_vill_ex.merge(
                df_man, how='left', left_on='MAPPED LOCALITY', right_on='LOCALITY')
            df_loc_man = df_loc_man.drop_duplicates()
            df_loc_man['V_ID'] = df_loc_man['V_ID'].astype(
                'int')
            
            for i in df_loc_man[df_loc_man['MANDAL'].isnull()].index:
                df_loc_man.loc[i, 'MANDAL'] = 'unmapped' + \
                    "_" + str(df_loc_man.loc[i, 'V_ID'])
            df_final = vill_shp.merge(df_loc_man, how='left', on='V_ID')
            df1 = df_final.drop(
                columns=['AC_y', 'V_NAME_y', 'MAPPED LOCALITY'])
            ac_name = df1['AC NAME'].unique()[0]
            return df1, ac_name
        
        def add_centroid(v_shp):
            v_shp['centroid'] = v_shp['geometry'].to_crs(epsg=3857).centroid.to_crs(epsg=4326)
            v_shp = v_shp.to_crs(epsg=4326)
            return v_shp
    
        def nearest(v_shp_unmapped, merged_file):
            # Finding the nearest PS stations from the t_merged_gdf and v_info_unmapped
            na = np.array(
                list(v_shp_unmapped['centroid'].apply(lambda x: (x.x, x.y))))
            nb = np.array(
                list(merged_file['centroid'].apply(lambda x: (x.x, x.y))))
            
            btree = cKDTree(nb)
            dist, idx = btree.query(na, k=1)
            gdb_nearest_v = merged_file.iloc[idx].drop(
                columns="geometry").reset_index(drop=True)
            gdf = pd.concat(
                [gdb_nearest_v, v_shp_unmapped.reset_index(drop=True)], axis=1)
            return gdf
    

        def implement_nearest_neighbour(df1):
                unmapped_vill_ps_shp = df1[df1['LOCALITY'].isnull() == True]
                ps_cord_gdf = df1.dropna()
                unmapped_vill_shp = add_centroid(
                    unmapped_vill_ps_shp)
                ps_cord_gdf_shp = add_centroid(ps_cord_gdf)
                mapped_vill_ps_cord = nearest(unmapped_vill_shp, ps_cord_gdf_shp)
                mapped_vill_ps_cord.columns = ['VILL_ID_', 'AC_POST_x_', 'AC_NAME_PO', 'NAME11_x_', 'booth_no', 'Locality', 'MANDAL', 'centroid_', 'Village Id', 'AC_POST_x', 'AC_NAME_PO_', 'NAME11_x', 'geometry', 'booth_no_', 'Locality_', 'Mandal_', 'centroid']
                mapped_vill_ps_cord = mapped_vill_ps_cord[[
                        'Village Id', 'AC_POST_x', 'AC_NAME_PO', 'NAME11_x', 'geometry', 'booth_no', 'Locality', 'MANDAL']]
                ps_cord_gdf = ps_cord_gdf.rename(columns={'AC_x':'AC','V_NAME_x':'V_NAME' })
                mapped_vill_ps_cord = mapped_vill_ps_cord.rename(columns={
        'Village Id':'V_ID',
        'AC_POST_x':'AC',
        'AC_NAME_PO':'AC NAME',
        'NAME11_x':'V_NAME',
        'booth_no':'BOOTH_NO',
        'Locality':'LOCALITY',
        
    }
)
                ac_shape_file = pd.concat([mapped_vill_ps_cord, ps_cord_gdf]).reset_index(
                        drop=True).drop(columns=['centroid'])
                return ac_shape_file

        

        #! Make sure to standardize the column names of ac mapping file
        df_vill = self.ac_mapping_file[['V_ID', 'AC','V_NAME', 'MAPPED LOCALITY']]
        df_man = self.ac_mapping_file[['BOOTH_NO', 'LOCALITY', 'MANDAL']]
        # dropping all rows with na valu
        df_vill = df_vill.dropna(how='all', axis=0)
        df_man = df_man.dropna(how='all', axis=0)
         ##   Exploding and Separated "Mapped Locality" Column on 'special_character':(done)
         ##   (df_vill)->(df_vill)
        df_vill['MAPPED LOCALITY'] = df_vill['MAPPED LOCALITY'].astype('str')  # Converting Mapped Locality Column to type 'str'
        df_vill['MAPPED LOCALITY'] = df_vill['MAPPED LOCALITY'].apply(lambda x: list(map(str, x.split('&&'))))  # Splitting the Mapped Locality which has '&&' value in df_vill
        # Exploding the df_vill on Mapped Locality
        df_vill_ex = df_vill.explode('MAPPED LOCALITY', ignore_index=True)
        # Dropping the duplicates from df_vill
        df_vill_ex = df_vill_ex.drop_duplicates()
        vill_shp = self.vill_shp

        df1,ac_name = mapped_locality(df_vill_ex,df_man,vill_shp)
        ac_shape_file = implement_nearest_neighbour(df1)
        
        return ac_shape_file,ac_name
