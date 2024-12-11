import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point

us_counties = gpd.read_file('US_COUNTY_SHPFILE/US_county_cont.shp')
southwestern_state_list = ['Texas', 'New Mexico','Arizona', 'California'] 
southwestern_states = us_counties[us_counties['STATE_NAME'].isin(southwestern_state_list)].to_crs(4269)
boundaries = southwestern_states.dissolve(by='STATE_NAME')
roads = gpd.read_file('tl_2023_us_primaryroads/tl_2023_us_primaryroads.shp')
i_10 = roads[roads['FULLNAME'] == 'I- 10']
los_angeles = Point(-118.2426,34.0549)
houston = Point(-95.3701,29.7601)
hou_la = gpd.GeoDataFrame(geometry = [houston, los_angeles])
boundaries = boundaries.to_crs(4269)
southwest_i_10 = gpd.overlay(i_10, boundaries, how='intersection')

arizona_protected = gpd.read_file('arizona_protected/PADUS4_0_StateAZ.gdb', layer='PADUS4_0Fee_State_AZ').to_crs(epsg=4269)
california_protected = gpd.read_file('california_protected/PADUS4_0_StateCA.gdb', layer = 'PADUS4_0Fee_State_CA').to_crs(epsg=4269)
newmexico_protected = gpd.read_file('newmexico_protected/PADUS4_0_StateNM.gdb', layer = 'PADUS4_0Fee_State_NM').to_crs(epsg=4269)
texas_protected = gpd.read_file('texas_protected/PADUS4_0_StateTX.gdb', layer = 'PADUS4_0Fee_State_TX').to_crs(epsg=4269)
sw_protected_lands = gpd.GeoDataFrame(pd.concat([texas_protected, newmexico_protected, arizona_protected, california_protected], ignore_index=True))

def plot_map(requested_location):
    fig, ax = plt.subplots(figsize=(10, 10))
    boundaries.plot(ax=ax, edgecolor='black', facecolor='none')
    sw_protected_lands.plot(ax=ax)
    requested_location.plot(ax=ax, color='yellow', label="Requested Location")
    southwest_i_10.plot(ax=ax, color='red', label="I-10")
    hou_la.plot(ax=ax, color='green', label="Houston and Los Angeles")
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.legend()
    ax.set_title('Protected Lands and Requested Location')
    return fig

st.title("Hydrogen Infrastructure Location Eligibility Checker")

type_of_input = st.selectbox("Would you like to check if a county or if coordinates are eligible for hydrogen infrastructure construction?", ("County", "Coordinates"), index=None, placeholder="Select here...",)
if type_of_input == "county" or type_of_input == "County":
    requested_county = st.text_input("Please input your county name.", "")
    requested_state = st.text_input("Please input your state name.", "")
    if requested_county and requested_state:
        if requested_state not in southwestern_states["STATE_NAME"].tolist():
            st.write("Please try again with a different state.")
        elif requested_county not in southwestern_states[southwestern_states["STATE_NAME"] == requested_state]["NAME"].tolist():
            st.write("Requested county could not be found in your requested state.")
        county_geometry = southwestern_states[(southwestern_states["STATE_NAME"] == requested_state) & (southwestern_states["NAME"] == requested_county)].to_crs(3857)
        county_centroid = county_geometry.geometry.centroid
        county_centroid = county_centroid.to_crs(4269)
        intersects = county_centroid.apply(lambda x: sw_protected_lands.intersects(x).any())
        if intersects.iloc[0] == True:
            st.write("Unfortunately, the centroid of this county is not eligible for hydrogen infrastructure construction because it is located in protected lands.")
            placeholder = st.empty()
            with placeholder.container():
                fig = plot_map(county_centroid)
            st.pyplot(fig)
        elif intersects.iloc[0] == False:
            st.write("Success! The centroid of this county is eligible for hydrogen infrastructure construction!")
            placeholder = st.empty()
            with placeholder.container():
                fig = plot_map(county_centroid)
            st.pyplot(fig)
        else:
            st.write("The test was inconclusive. Please try again")
     
elif type_of_input == "coordinates" or type_of_input == "Coordinates":
    requested_coords = st.text_input("Please input your coordinates like [longitude, latitude]")
    if requested_coords:
        coords = requested_coords.strip('[]').split(',') 
        longitude, latitude = float(coords[0]), float(coords[1])
        requested_point = point = Point(longitude, latitude)
        intersects = sw_protected_lands.intersects(requested_point).any()
        if intersects:
            st.write("Unfortunately, this location is not eligible for hydrogen infrastructure construction because it is located in protected lands.")
            requested_point = gpd.GeoDataFrame(geometry = [requested_point])
            placeholder = st.empty()
            with placeholder.container():
                fig = plot_map(requested_point)
            st.pyplot(fig)
        elif not intersects:
            st.write("Success! This location is eligible for hydrogen infrastructure construction!")
            requested_point = gpd.GeoDataFrame(geometry = [requested_point])
            placeholder = st.empty()
            with placeholder.container():
                fig = plot_map(requested_point)
            st.pyplot(fig)

        else:
            st.write("The test was inconclusive. Please try again")