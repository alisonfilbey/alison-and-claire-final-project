import pandas as pd 
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely import wkt
import numpy as np
import contextily as ctx
from shiny import App, reactive, render, ui


try:
    roads = gpd.read_file("c:/Users/aliso/OneDrive/Documents/Second Year First Quarter/Python II/alison-and-claire-final-project/shiny-app/roads.shp")
    crashes = gpd.read_file("c:/Users/aliso/OneDrive/Documents/Second Year First Quarter/Python II/alison-and-claire-final-project/shiny-app/ped_crashes.shp")
    community = gpd.read_file("c:/Users/aliso/OneDrive/Documents/Second Year First Quarter/Python II/alison-and-claire-final-project/shiny-app/comm_areas.shp")
    print("Data loaded successfully")
except Exception as e:
    print(f"Error loading shapefiles: {e}")

roads['neighborhood'] = roads['COMMUNITY'].astype(str).str.strip()
crashes['neighborhood'] = crashes['COMMUNITY'].astype(str).str.strip()
community['neighborhood'] = community['COMMUNITY'].astype(str).str.strip()

app_ui = ui.page_fluid(
    ui.input_select(id="neighborhood", label='Choose a neighborhood:', choices=[]),
    #ui.panel(ui.output_text("top_roads")),
    ui.output_table("roads_data_table"),  # Display roads data
    ui.output_plot("road_map"),
    ui.output_text("top_roads"),
)

def server(input, output, session):
   @reactive.calc
   def roads_list():
        df = roads
        return df
   def roads_data():
        df = roads
        return df[df['neighborhood'] == input.neighborhood()]
   @reactive.calc
   def community_data():
        df = community
        return df[df['neighborhood'] == input.neighborhood()]
   @reactive.calc
   def crashes_data():
        df = crashes
        return df[df['neighborhood'] == input.neighborhood()]
   @render.table
   def  roads_data_table():
        df = roads_data()  # Get the roads data
        return df.head() 

   @reactive.calc
   def crashes_by_road():
        road_df = roads_data()
        crash_df = crashes_data()
        #group by street and calculate number of crashes
        severe_crashes_by_road = crash_df.groupby("STREET_NAM")[
            ["n_peds_tot", "n_peds_sev"]].sum().reset_index()
        #calculate share of severe ped crashes by speed
        severe_crashes_by_road["share_severe"] = severe_crashes_by_road[
            "n_peds_sev"]/severe_crashes_by_road["n_peds_tot"]
        road_df = pd.merge(road_df, severe_crashes_by_road, on="STREET_NAM", how="left")
        return road_df

   @reactive.calc
   def top_road_data():
        df_crash = crashes_data()
        df = df_crash.groupby("STREET_NAM")[["n_peds_tot", "n_peds_sev"]].sum().reset_index()
        df["share_severe"] = df["n_peds_sev"]/df["n_peds_tot"]
        df_crash = pd.merge(df_crash, df, on="STREET_NAM", how="left")
        return df_crash
     
   @reactive.calc
   def mode(series):
    return series.mode().iloc[0] if not series.mode().empty else None

   @render.plot
   def road_map():
        roads = crashes_by_road()
        comm_areas = community_data()
        comm_areas = comm_areas.to_crs(epsg=3857)
        roads = roads.to_crs(epsg=3857)
        fig, ax = plt.subplots(figsize=(5, 5))
        comm_areas.plot(ax=ax, facecolor="none", edgecolor="black")
        roads.plot(column="n_peds_sev", legend=True, cmap="RdYlGn_r", ax=ax,
        legend_kwds={"label": "Number of Severe Pedestrian Crashes", "orientation": "horizontal"})
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
        ax.set_axis_off()
        ax.set_title("Roadway Locations of Severe Pedestrian Crashes in Neighborhood", fontsize=14)
        return fig
   
   @render.text
   def top_roads():
    crash_df = crashes_data()
    road_df = crashes_by_road()
    neighborhood = input.neighborhood()
    most_frequent_speed = crash_df.groupby("STREET_NAM")["binned_pos"].apply(mode).reset_index()
    top_roads = road_df.sort_values(by="n_peds_sev", ascending=False)[["STREET_NAM", "n_peds_sev"]].head(3)
    top_roads = pd.merge(top_roads, most_frequent_speed, on="STREET_NAM", how="left")
    top_roads = top_roads.rename(columns={
        "STREET_NAM": "Street Name",
        "n_peds_sev": "Number of Severe Ped Crashes",
        "binned_pos": "Speed Limit"
        })
    return top_roads

   @reactive.effect
   def _():
       neighborhood_list = roads_list()['neighborhood'].dropna().unique().tolist()
       neighborhood_list = sorted(neighborhood_list)
       ui.update_select("neighborhood", choices=neighborhood_list)

app = App(app_ui, server)


