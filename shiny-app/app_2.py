import pandas as pd 
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely import wkt
import numpy as np
import contextily as ctx
from shiny import App, reactive, render, ui


# Load data and check for errors
try:
    roads = gpd.read_file("shiny-app/roads.shp")
    crashes = gpd.read_file("shiny-app/ped_crashes.shp")
    community = gpd.read_file("shiny-app/comm_areas.shp")
    print("Data loaded successfully")
except Exception as e:
    print(f"Error loading shapefiles: {e}")

roads['community_fixed'] = roads['COMMUNITY'].astype(str).str.strip()
crashes['community_fixed'] = crashes['COMMUNITY'].astype(str).str.strip()
community['community_fixed'] = community['COMMUNITY'].astype(str).str.strip()


app_ui = ui.page_fluid(
    ui.input_select(id="neighborhood", label='Choose a neighborhood:', choices=[]),
    #ui.panel(ui.output_text("top_roads")),
    ui.output_text("road_stats"),  
    ui.output_plot("road_map")
)

def server(input, output, session):
     @reactive.calc
     def roads_list():
          df = roads
          return df
        
     @reactive.calc
     def roads_data():
          df = roads
          return df[df['community_fixed'] == input.neighborhood()]

     @reactive.calc
     def community_data():
          df = community
          return df[df['community_fixed'] == input.neighborhood()]

     @reactive.calc
     def crashes_data():
          df = crashes
          return df[df['community_fixed'] == input.neighborhood()]

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
     def top_roads():
          road_df = roads_data()
          crash_df = crashes_data()

          #group by street and calculate number of crashes
          severe_crashes_by_road = crash_df.groupby("STREET_NAM")[
               ["n_peds_tot", "n_peds_sev"]].sum().reset_index()

          #calculate share of severe ped crashes by speed
          severe_crashes_by_road["share_severe"] = severe_crashes_by_road[
               "n_peds_sev"]/severe_crashes_by_road["n_peds_tot"]
          return severe_crashes_by_road

          
    
     def mode(series):
          return series.mode().iloc[0] if not series.mode().empty else None


     @render.text
     def road_stats():
          crash_df = crashes_data()
          road_df = top_roads()

          #calculate speed limit on road by finding most frequent recorded speed
          most_frequent_speed = crash_df.groupby("STREET_NAM")["binned_pos"].apply(mode).reset_index()
          
          #find 3 highest ped crash roads and merge to speed limit
          road_stats = road_df.sort_values(by="n_peds_sev", ascending=False)[
               ["STREET_NAM", "n_peds_sev"]].head(3)
          road_stats = pd.merge(road_stats, most_frequent_speed, on="STREET_NAM", how="left")
          
          #rename columns for displaying
          road_stats = road_stats.rename(columns={
            "STREET_NAM": "Street Name",
            "n_peds_sev": "Number of Severe Ped Crashes",
            "binned_pos": "Speed Limit"})
          return road_stats

     @render.plot
     def road_map():
          roads = crashes_by_road()
          comm_areas = community_data()
        
          #reproject roads and communities so basemap plots correctly
          comm_areas = comm_areas.to_crs(epsg=3857)
          roads = roads.to_crs(epsg=3857)

          #plot roads by severe ped crashes
          fig, ax = plt.subplots(figsize=(5, 5))
          comm_areas.plot(ax=ax, facecolor="none", edgecolor="black")
          roads.plot(column="n_peds_sev", legend=True, cmap="RdYlGn_r", ax=ax,
          legend_kwds={"label": "Number of Severe Pedestrian Crashes", "orientation": "horizontal"})
          ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
          ax.set_axis_off()
          ax.set_title(f"Roadway Locations of Severe Pedestrian Crashes in {input.neighborhood()}", fontsize=14)
          return fig

     @reactive.effect
     def _():
          neighborhood_list = roads_list()["community_fixed"].dropna().unique().tolist()
          neighborhood_list = sorted(neighborhood_list)
          ui.update_select("neighborhood", choices=neighborhood_list)

app = App(app_ui, server)

