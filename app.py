import pandas as pd 
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely import wkt
import numpy as np
import contextily as ctx


from shiny import App, reactive, render, ui
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select(id='neighborhood', label='Choose a neighborhood:', choices=[])
    ),
    ui.layout_column_wrap(
        ui.value_box(
            "Value", 
            ui.output_text("top_roads"),
        ),
        fill=False, 
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Road Map of Neighborhood by Number of Pedestrians Severely or Fatally Injured In Crash"),
            ui.output_plot("road_map"),
        ),
        ui.card(
            ui.card_header("Chicago Neighborhoods by Number of Pedestrians Severely or Fatally Injured In Crash"),
            ui.output_plot("neighborhood_plot"),
        ),
    ),
    title="Severe Pedestrian Crashes by Chicago Neighborhood",
    fillable=True,  
)

def server(input, output, session):
    @reactive.calc
    def roads_data():
        df = gpd.read_file("Data/roads_gdf.shp")
        return df[df['COMMUNITY'] == input.neighborhood()]
    @reactive.calc
    def crashes_data():
        df = gpd.read_file("Data/crash_gdf.shp")
        return df[df['COMMUNITY'] == input.neighborhood()]
    @reactive.calc
    def community_data():
        df = gpd.read_file("Data/comm_areas_gdf.shp")
        return df[df['COMMUNITY'] == input.neighborhood()]
    @reactive.calc
    def top_road_data():
        df_crash = crashes_data
        df = df_crash.groupby("STREET_NAM")[["n_peds_total", "n_peds_severe"]].sum().reset_index()
        df["share_severe"] = df["n_peds_severe"]/df["n_peds_total"]
        return df
    @reactive.calc
    def mode(series):
        return series.mode().iloc[0] if not series.mode().empty else None
    @render.text
    def top_roads():
        df1=crashes_data()
        df2=top_road_data()
        neighborhood = input.neighborhood()
        most_frequent_speed = df1.groupby("STREET_NAM")["binned_posted_speed"].apply(mode).reset_index()
        top_roads = df2.sort_values(by="n_peds_severe", ascending=False)[["STREET_NAM", "n_peds_severe"]].head(3)
        top_roads = pd.merge(top_roads, most_frequent_speed, on="STREET_NAM", how="left")
        top_roads = top_roads.rename(columns={
            "STREET_NAM": "Street Name",
            "n_peds_severe": "Number of Severe Ped Crashes",
            "binned_posted_speed": "Speed Limit"
        })
        print(f"The most dangerous roads in {neighborhood} for pedestrians are:")
        print(top_roads)
        return top_roads

    @render.plot
    def road_map():
        df1=roads_data()
        df2=community_data()
        fig, ax = plt.subplots(figsize=(10, 8))
        df2.plot(ax=ax, facecolor="none", edgecolor="black")
        df1.plot(column="n_peds_severe", legend=True, cmap="RdYlGn_r", ax=ax,
                  legend_kwds={"label": "Number of Severe Pedestrian Crashes", "orientation": "horizontal"})
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
        ax.set_axis_off()
        ax.set_title("Roadway Locations of Severe Pedestrian Crashes in Hyde Park", fontsize=14)
        plt.show()      
    @reactive.effect
    def _():
        neighborhood_list = roads_data()['COMMUNITY'].unique().tolist()
        neighborhood_list = sorted(neighborhood_list)
        ui.update_select("neighborhood", choices=neighborhood_list)
    

app = App(app_ui, server)
