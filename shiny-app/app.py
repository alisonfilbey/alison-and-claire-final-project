import pandas as pd 
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely import wkt
import numpy as np
import contextily as ctx


from shiny import App, reactive, render, ui
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select(id="neighborhood", label='Choose a neighborhood:', choices=[])
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
            full_screen=True,
        ),
        ui.card(
            ui.card_header("Chicago Neighborhoods by Number of Pedestrians Severely or Fatally Injured In Crash"),
            ui.output_plot("neighborhood_plot"),
            full_screen=True,
        ),
    ),
    title="Severe Pedestrian Crashes by Chicago Neighborhood",
    fillable=True,  
)


def server(input, output, session):

    @reactive.calc
    def roads_data():
        df = gpd.read_file("shiny-app/roads.shp")
        return df[df['COMMUNITY'] == input.neighborhood()]

    @reactive.calc
    def crashes_data():
        df = gpd.read_file("shiny-app/ped_crashes.shp")
        return df[df['COMMUNITY'] == input.neighborhood()]

    @reactive.calc
    def community_data():
        df = gpd.read_file("shiny-app/comm_areas.shp")
        return df[df['COMMUNITY'] == input.neighborhood()]

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

    #@reactive.calc
    #def top_road_data():
        #df_crash = crashes_data()
        #df = df_crash.groupby("STREET_NAM")[["n_peds_tot", "n_peds_sev"]].sum().reset_index()
        #df["share_severe"] = df["n_peds_sev"]/df["n_peds_tot"]
        #df_crash = pd.merge(df_crash, df, on="STREET_NAM", how="left")
        #return df_crash
     
    @reactive.calc
    def mode(series):
        return series.mode().iloc[0] if not series.mode().empty else None

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
        print(f"The most dangerous roads in {neighborhood} for pedestrians are:")
        print(top_roads)
        return top_roads

    @render.plot
    def road_map():
        roads = crashes_by_road()
        comm_areas = community_data()

        #reproject so that basemap can plot
        comm_areas = comm_areas.to_crs(epsg=3857)
        roads = roads.to_crs(epsg=3857)

        fig, ax = plt.subplots(figsize=(10, 8))
        comm_areas.plot(ax=ax, facecolor="none", edgecolor="black")
        roads.plot(column="n_peds_sev", legend=True, cmap="RdYlGn_r", ax=ax,
                  legend_kwds={"label": "Number of Severe Pedestrian Crashes", "orientation": "horizontal"})
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
        ax.set_axis_off()
        ax.set_title("Roadway Locations of Severe Pedestrian Crashes in Hyde Park", fontsize=14)
        return fig

    @reactive.effect
    def _():
        neighborhood_list = community_data()['COMMUNITY'].unique().tolist()
        neighborhood_list = sorted(neighborhood_list)
        ui.update_select("neighborhood", choices=neighborhood_list)
    

app = App(app_ui, server)
