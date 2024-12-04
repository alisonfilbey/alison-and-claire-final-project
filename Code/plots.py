import pandas as pd
import geopandas as gpd
from shapely import wkt
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import contextily as ctx

ped_crashes = pd.read_csv("Data/Clean/ped_crashes.csv")
#collapse by speed limit bin
severe_crashes_by_speed = ped_crashes.groupby("binned_posted_speed")[
    ["n_peds_total", "n_peds_severe"]].sum().reset_index()

#calculate share of severe ped crashes by speed
severe_crashes_by_speed["share_severe"] = severe_crashes_by_speed[
    "n_peds_severe"]/severe_crashes_by_speed["n_peds_total"]

#plot share of severe ped crashes by posted speed limit
speed_chart = alt.Chart(severe_crashes_by_speed).mark_bar(color="seagreen", opacity=0.85
).transform_filter(alt.datum.binned_posted_speed < 50
).encode(
    x=alt.X("binned_posted_speed:O", title="Posted Speed Limit"),
    y=alt.Y("share_severe", title="Share of Pedestrian Involved Crashes (%)")
).properties(title={
        "text": ["Severe or Fatal Pedestrian Injuries", "by Posted Speed Limit"]},
        height=300, width=300)
speed_chart.save("Pictures/severe_ped_by_speed.png", scale_factor=3)

ped_action = ped_crashes[ped_crashes['n_peds_total']==1]

#subset to top ten actions 
ped_action = ped_action[ped_action['PEDPEDAL_ACTION'].isin([
    'CROSSING - WITH SIGNAL',
    'OTHER ACTION',
    'CROSSING - NO CONTROLS (NOT AT INTERSECTION)',
    'NO ACTION',
    'CROSSING - NO CONTROLS (AT INTERSECTION)',
    'CROSSING - AGAINST SIGNAL',
    'CROSSING - CONTROLS PRESENT (NOT AT INTERSECTION)',
    'UNKNOWN/NA',
    'STANDING IN ROADWAY',
    'WITH TRAFFIC'
])]

#groupby ped action and count number of severe pedestrian injuries
ped_action = ped_action.groupby("PEDPEDAL_ACTION")["n_peds_severe"].sum(
    ).reset_index(name="n_peds_total")

#alt.data_transformers.enable("vegafusion")
#plot number of severe ped crashes by action
ped_act_chart = alt.Chart(ped_action).mark_bar(color="seagreen", opacity=0.85).encode(
    x=alt.Y("n_peds_total", axis=alt.Axis(title= "")),
    y=alt.X('PEDPEDAL_ACTION:O', sort='x', axis=alt.Axis(title= 'Action of Pedestrian',         
        labelFontSize=6))
).properties(title= "Number of Crashes with Severe or Fatal Pedestrian Injuries by the Action of the Pedestrian")
ped_act_chart.save("Pictures/severe_ped_by_action.png", scale_factor=3)

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

#collapse by cause of crash
severe_crashes_by_cause = ped_crashes.groupby("updated_cause")[
    ["n_peds_total", "n_peds_severe"]].sum().reset_index()

#calculate share of severe ped crashes by cause
severe_crashes_by_cause["share_severe"] = severe_crashes_by_cause[
    "n_peds_severe"]/severe_crashes_by_cause["n_peds_total"]

#plot share of severe ped crashes by posted cause of crash
cause_plot = alt.Chart(severe_crashes_by_cause).mark_bar(color="seagreen", opacity=0.85
).encode(
    y=alt.Y("updated_cause", title="", sort="-x"),
    x=alt.X("share_severe", title="Share of Pedestrian Involved Crashes (%)")
).properties(title="Severe or Fatal Pedestrian Injuries by Cause of Crash", height=300, width=300)
cause_plot.save("Pictures/severe_ped_by_crash_cause.png", scale_factor=3)