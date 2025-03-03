import pandas as pd
import geopandas as gpd
from shapely import wkt
import numpy as np

#load raw crash and people data
'''
These raw files are too large to publish on github. They can be downloaded from the Google Drive folder linked below.
Once downloaded, you should add them to the Data/Raw folder
https://drive.google.com/drive/folders/16oqPjuMoqH9tWm7X-AmrYSy6ArX5mElg?usp=drive_link 
'''
crashes = pd.read_csv("Data/Raw/Traffic_Crashes_Crashes.csv")
people = pd.read_csv("Data/Raw/Traffic_Crashes_People.csv")

#load road and community area data
roads = pd.read_csv("Data/Raw/chicago_roads.csv")
comm_areas = pd.read_csv("Data/Raw/CommAreas.csv")

#basic cleaning for crashes data

#recode posted speed limits =99 as missing (affects 0.008% of obs)
crashes["POSTED_SPEED_LIMIT"] = crashes["POSTED_SPEED_LIMIT"].apply(
    lambda x: np.nan if x == 99 else x)

#define speed limit bins and labels
bins = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75]
labels = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75]

#assign each value to the correct bin
crashes["binned_posted_speed"] = pd.cut(crashes["POSTED_SPEED_LIMIT"], 
                                        bins=bins, 
                                        labels=labels, 
                                        right=True)

#drop missing and outlier locations
crashes = crashes[crashes["LATITUDE"] != 0]
crashes = crashes[crashes["LOCATION"].notna()]

#create geometry column
crashes["geometry"] = crashes["LOCATION"].apply(wkt.loads)

#clean people data to get pedestrians
ped_data = people.loc[people["PERSON_TYPE"]=="PEDESTRIAN"]

#keep severe crashes
ped_data_severe = ped_data.loc[(ped_data["INJURY_CLASSIFICATION"]=="INCAPACITATING INJURY") |
                                (ped_data["INJURY_CLASSIFICATION"]=="FATAL")]

#count number of pedestrians involved per each unique crash id
ped_crashes = ped_data["CRASH_RECORD_ID"].value_counts().reset_index()
ped_crashes = ped_crashes.rename({"count":"n_peds_total"}, axis=1)

#count number of pedestrians with severe injuries per each unique crash id
ped_severe_crashes = ped_data_severe["CRASH_RECORD_ID"].value_counts().reset_index()
ped_severe_crashes = ped_severe_crashes.rename({"count":"n_peds_severe"}, axis=1)

#merge counts
ped_counts = pd.merge(ped_crashes, ped_severe_crashes, on="CRASH_RECORD_ID", how="left")

#merge into crash data
ped_crashes = pd.merge(crashes, ped_counts, on="CRASH_RECORD_ID", how="inner")

#merge pedestrian actions into crash data
ped_actions = people[["PEDPEDAL_ACTION", "CRASH_RECORD_ID"]]
ped_crashes = pd.merge(ped_crashes, ped_actions, on="CRASH_RECORD_ID", how="left")

#create dictionary for new values of crash cause
crash_cause_xwalk = {"CELL PHONE USE OTHER THAN TEXTING":"Distraction", 
    "DISTRACTION - FROM INSIDE VEHICLE":"Distraction", "DISTRACTION - FROM OUTSIDE VEHICLE":
    "Distraction", "DISTRACTION - OTHER ELECTRONIC DEVICE (NAVIGATION DEVICE, DVD PLAYER, ETC.)":
    "Distraction", "TEXTING":"Distraction", "DISREGARDING OTHER TRAFFIC SIGNS":
    "Disregard of Traffic Signs/Signals", "DISREGARDING ROAD MARKINGS":
    "Disregard of Traffic Signs/Signals", "DISREGARDING STOP SIGN":
    "Disregard of Traffic Signs/Signals", "DISREGARDING TRAFFIC SIGNALS":
    "Disregard of Traffic Signs/Signals", "DISREGARDING YIELD SIGN":
    "Disregard of Traffic Signs/Signals", "FAILING TO YIELD RIGHT-OF-WAY":
    "Disregard of Traffic Signs/Signals", "RELATED TO BUS STOP":
    "Disregard of Traffic Signs/Signals", "TURNING RIGHT ON RED":
    "Disregard of Traffic Signs/Signals", 
    "UNDER THE INFLUENCE OF ALCOHOL/DRUGS (USE WHEN ARREST IS EFFECTED)": 
    "Under the Influence", "HAD BEEN DRINKING (USE WHEN ARREST IS NOT MADE)":"Under the Influence",
    "PHYSICAL CONDITION OF DRIVER": "Under the Influence", "EXCEEDING AUTHORIZED SPEED LIMIT":
    "Speeding", "EXCEEDING SAFE SPEED FOR CONDITIONS": "Speeding", 
    "FAILING TO REDUCE SPEED TO AVOID CRASH": "Speeding", 
    "OPERATING VEHICLE IN ERRATIC, RECKLESS, CARELESS, NEGLIGENT OR AGGRESSIVE MANNER":
    "Reckless/poor driving", "DRIVING ON WRONG SIDE/WRONG WAY":"Reckless/poor driving", 
    "FOLLOWING TOO CLOSELY":"Reckless/poor driving", "IMPROPER BACKING":"Reckless/poor driving",
    "IMPROPER LANE USAGE":"Reckless/poor driving", "IMPROPER OVERTAKING/PASSING":
    "Reckless/poor driving", "IMPROPER TURNING/NO SIGNAL":"Reckless/poor driving", 
    "PASSING STOPPED SCHOOL BUS":"Reckless/poor driving", 
    "DRIVING SKILLS/KNOWLEDGE/EXPERIENCE":"Reckless/poor driving", 
    "ANIMAL":"Obstruction", "OBSTRUCTED CROSSWALKS":"Obstruction", 
    "VISION OBSCURED (SIGNS, TREE LIMBS, BUILDINGS, ETC.)":"Obstruction", 
    "BICYCLE ADVANCING LEGALLY ON RED LIGHT":"Obstruction", 
    "EVASIVE ACTION DUE TO ANIMAL, OBJECT, NONMOTORIST":"Obstruction", 
    "ROAD CONSTRUCTION/MAINTENANCE":"Exterior condition", 
    "ROAD ENGINEERING/SURFACE/MARKING DEFECTS":"Exterior condition", 
    "WEATHER":"Exterior condition", "EQUIPMENT - VEHICLE CONDITION":"Exterior condition", 
    "NOT APPLICABLE":"Unclassified", "UNABLE TO DETERMINE":"Unclassified"}

#replace new type variable
ped_crashes["updated_cause"] = ped_crashes["PRIM_CONTRIBUTORY_CAUSE"].replace(crash_cause_xwalk)

#keep relevant columns 
ped_crashes = ped_crashes[["CRASH_RECORD_ID", "PEDPEDAL_ACTION", "binned_posted_speed",
                            "n_peds_total", "n_peds_severe", "updated_cause",
                            "LATITUDE", "LONGITUDE", "geometry"]]

#output cleaned csv
ped_crashes.to_csv("Data/Clean/ped_crashes.csv", index=False)

# prep road and community area data for shiny app

#create geometry column to turn roads csv into geopandas object
roads["geometry"] = roads["the_geom"].apply(wkt.loads)
roads_gdf = gpd.GeoDataFrame(roads, geometry="geometry")
roads_gdf = roads_gdf.set_crs("EPSG:4326", inplace=True)

#keep relevant columns for road data
roads_gdf = roads_gdf[["OBJECTID", "STREET_NAM", "STREET_TYP", "SUF_DIR", "STREETNAME", "geometry"]]

#create geometry column to turn community areas csv into geopandas object
comm_areas["geometry"] = comm_areas["the_geom"].apply(wkt.loads)
comm_areas_gdf = gpd.GeoDataFrame(comm_areas, geometry="geometry")
comm_areas_gdf = comm_areas_gdf.set_crs("EPSG:4326", inplace=True)
comm_areas_gdf = comm_areas_gdf[["COMMUNITY", "geometry"]]

#turn ped crashes df geopandas object
ped_crashes_gdf = gpd.GeoDataFrame(ped_crashes, geometry="geometry")
ped_crashes_gdf = ped_crashes_gdf.set_crs("EPSG:4326", inplace=True)

#add community area to road and crash  data with spatial join
roads_gdf = gpd.sjoin(roads_gdf, comm_areas_gdf, how="left")
ped_crashes_gdf = gpd.sjoin(ped_crashes_gdf, comm_areas_gdf, how="left")

#define buffer distance around each road so that crash points lie within buffer
buffer_distance = 0.00025

#create buffer around roads for spatial join
roads_gdf["buffer"] = roads_gdf.geometry.buffer(buffer_distance)

#create new geodataframe for buffers
buffered_gdf = roads_gdf.set_geometry("buffer")
buffered_gdf = buffered_gdf[["buffer", "STREET_NAM"]]

#spatial join crashes with buffers to get street name where crash occured
ped_crashes_gdf = ped_crashes_gdf.drop(["index_right"], axis=1)
ped_crashes_gdf = gpd.sjoin(ped_crashes_gdf, buffered_gdf, how="left", predicate="within")

#drop buffer from road file
roads_gdf = roads_gdf.drop(["buffer"], axis=1)

#output shapefiles
ped_crashes_gdf.to_file("shiny-app/Data/ped_crashes.shp")
comm_areas_gdf.to_file("shiny-app/Data/comm_areas.shp")
roads_gdf.to_file("shiny-app/Data/roads.shp")