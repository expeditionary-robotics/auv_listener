"""Utilities file for making plotters.

Authors: Genevieve Flaspohler and Victoria Preston
Update: August 2023
Contact: {geflaspo, vpreston}@mit.edu
"""

import os
import time
import utm
import gsw
import pandas as pd
import numpy as np
from scipy.interpolate import griddata

from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import dash
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.animation as animation
from matplotlib.widgets import Button
from matplotlib import style

style.use('fivethirtyeight')


class CallbackXlim(object):
    def __init__(self, obj, idx):
        self.idx = idx
        self.obj = obj
        self.callback_time = time.time()

    def __call__(self, event_ax):
        xloc = matplotlib.dates.num2date(event_ax.xdata)
        self.obj.prev_xlim[self.idx] = self.obj.xlim[self.idx]
        self.obj.xlim[self.idx] = [xloc, None]
        self.obj.live_mode[self.idx] = False
        self.obj.new_xlim[self.idx] = self.obj.xlim[self.idx]


class CallbackXlimArbitrary(object):
    def __init__(self, obj, idx):
        self.idx = idx
        self.obj = obj
        self.callback_time = time.time()

    def __call__(self, event_ax):
        xloc = event_ax.xdata
        self.obj.prev_xlim[self.idx] = self.obj.xlim[self.idx]
        self.obj.xlim[self.idx] = [xloc, None]
        self.obj.live_mode[self.idx] = False
        self.obj.new_xlim[self.idx] = self.obj.xlim[self.idx]


class LiveTimePlot(object):
    """Creates a plot that live updates when data is written to file."""

    def __init__(self, file, time_index=1, col_index=[2, 3],
                 col_names=["X", "Y"], scatter=False, max_pts=3600):
        """Initializes a live plot.

        Arguments:
            file (str): filepointer to data
            time_index (int): part of message with timestamp
            col_index (list(int)): part of message to display
            col_names (list(str)): what to call those data
            scatter (bool): whether to connect points
            max_pts (int): maximum number of plotted points
        """
        self.fig = plt.figure()
        self.file = file
        self.time_index = time_index
        self.col_index = col_index
        self.col_names = col_names
        self.num = len(col_index)  # number of subplots
        self.scatter = scatter
        self.max_pts = max_pts
        self.axs = []
        self.callback_xlim = []
        self.callback_ylim = []

        # Initialize button
        buttonax = self.fig.add_axes([0.45, 0.9, 0.19, 0.075])
        self.button = Button(buttonax, "Home View")

        self.live_mode = [True]*self.num
        self.xlim = [None]*self.num
        self.ylim = [None]*self.num
        self.prev_xlim = [None]*self.num
        self.prev_ylim = [None]*self.num
        self.new_xlim = [None]*self.num
        self.new_ylim = [None]*self.num
        self.button_time = time.time()

        # Initialize date string format
        self.xfmt = mdates.DateFormatter("%H:%M:%S")

        # Create the subplots and their callbacks
        for i in range(1, self.num+1):
            self.axs.append(self.fig.add_subplot(self.num, 1, i))
            self.callback_xlim.append(CallbackXlim(self, i-1))

        # Create the refreshing plot
        ani = animation.FuncAnimation(
            self.fig, self.animate, interval=50, repeat=False)
        plt.show()

    def callback_button(self, event_ax):
        """Resets the window viewing when the Home button is clicked."""
        self.button_time = time.time()
        self.live_mode = [True]*self.num
        self.new_xlim = [None]*self.num
        self.new_ylim = [None]*self.num

    def animate(self, i):
        """How the plot should refresh over time."""
        # Grab the data being written to file
        if os.path.isfile(self.file):
            lines = pd.read_csv(self.file, sep=",", header=None)
            lines[self.time_index] = pd.to_datetime(lines[self.time_index],
                                                    utc=True)
            lines = lines.set_index(self.time_index).sort_index()

            # Capture only the most recent max_pts
            if len(lines) > self.max_pts:
                lines = lines.tail(self.max_pts)

            # Format the axes for the live time plot
            for i, ax in enumerate(self.axs):
                ax.clear()
                ax.xaxis.set_major_formatter(self.xfmt)
                ax.xaxis.set_major_locator(plt.MaxNLocator(10))
                ax.yaxis.set_major_locator(plt.MaxNLocator(10))
                ax.set_title(self.col_names[i])

            # Plot the time plots
            time = lines.index

            # Use color to notify whether time stamp has dropped
            if time[-1] == time[-2]:
                color = "r"
            else:
                color = "b"

            for i, ax in enumerate(self.axs):
                if self.scatter is False:
                    ax.plot(time, lines[self.col_index[i]], c=color)
                else:
                    ax.plot(time, lines[self.col_index[i]], c=color,
                            marker="o", linestyle="")

                if self.new_xlim[i] is not None and not self.live_mode[i]:
                    # Set the new xlimit
                    ax.set_xlim(self.new_xlim[i])

                    # Compute the new y axis spread for all columns
                    max_lim = lines[lines.index >=
                                    self.new_xlim[i][0]].max(axis=0).values
                    min_lim = lines[lines.index >=
                                    self.new_xlim[i][0]].min(axis=0).values
                    PAD = (max_lim - min_lim) * 0.05  # pad 5% of range
                    # Set y limits with padding
                    self.new_ylim[i] = (min_lim[i]-PAD[i], max_lim[i]+PAD[i])
                    ax.set_ylim(self.new_ylim[i])

            self.button.on_clicked(self.callback_button)
            for i, ax in enumerate(self.axs):
                self.fig.canvas.mpl_connect(
                    'button_press_event', self.callback_xlim[i])


class Live2DPlot(LiveTimePlot):
    """Reads in arbitrary column data and plots onto a graph."""

    def __init__(self, file, x_index=1, y_index=[2, 3],
                 ax_names=["X", "Y1", "Y2"], scatter=False, max_pts=3600):
        """Initializes a live plot.

            Arguments:
                file (str): filepointer to data
                x_index (int): The x-axis
                y_index (list(int)): The y-axis displays (allows multiplots)
                y_names (list(str)): what to call those data
                scatter (bool): whether to connect points
                max_pts (int): maximum number of plotted points
            """
        self.fig = plt.figure()
        self.file = file
        self.x_index = x_index
        self.y_index = y_index
        self.ax_names = ax_names
        self.num = len(y_index)  # number of subplots
        self.scatter = scatter
        self.max_pts = max_pts
        self.axs = []
        self.callback_xlim = []
        self.callback_ylim = []

        # Initialize button
        buttonax = self.fig.add_axes([0.45, 0.9, 0.19, 0.075])
        self.button = Button(buttonax, "Home View")

        self.live_mode = [True]*self.num
        self.xlim = [None]*self.num
        self.ylim = [None]*self.num
        self.prev_xlim = [None]*self.num
        self.prev_ylim = [None]*self.num
        self.new_xlim = [None]*self.num
        self.new_ylim = [None]*self.num
        self.button_time = time.time()

        # Create the subplots and their callbacks
        for i in range(1, self.num+1):
            self.axs.append(self.fig.add_subplot(self.num, 1, i))
            self.callback_xlim.append(CallbackXlimArbitrary(self, i-1))

        # Create the refreshing plot
        ani = animation.FuncAnimation(
            self.fig, self.animate, interval=50, repeat=False)
        plt.show()

    def animate(self, i):
        """How the plot should refresh over time."""
        # Grab the data being written to file
        if os.path.isfile(self.file):
            lines = pd.read_csv(self.file, sep=",", header=None)
            cols_to_keep = [self.x_index]
            for y in self.y_index:
                cols_to_keep.append(y)
            lines = lines.loc[:, cols_to_keep]
            lines = lines.set_index(self.x_index)

            # Capture only the most recent max_pts
            if len(lines) > self.max_pts:
                lines = lines.tail(self.max_pts)

            # Format the axes for the live time plot
            for i, ax in enumerate(self.axs):
                ax.clear()
                ax.xaxis.set_major_locator(plt.MaxNLocator(10))
                ax.yaxis.set_major_locator(plt.MaxNLocator(10))
                ax.set_xlabel(self.ax_names[0])
                ax.set_ylabel(self.ax_names[i+1])

            # Plot the time plots
            x = lines.index

            for i, ax in enumerate(self.axs):
                if self.scatter is False:
                    ax.plot(x, lines[self.y_index[i]])
                else:
                    ax.plot(x, lines[self.y_index[i]],
                            marker="o", linestyle="")

                if self.new_xlim[i] is not None and not self.live_mode[i]:
                    # Set the new xlimit
                    ax.set_xlim(self.new_xlim[i])

                    # Compute the new y axis spread for all columns
                    max_lim = lines[lines.index >=
                                    self.new_xlim[i][0]].max(axis=0).values
                    min_lim = lines[lines.index >=
                                    self.new_xlim[i][0]].min(axis=0).values

                    def PAD(ma, mi): return (ma - mi) * 0.05  # pad 5% of range
                    pad = PAD(max_lim[i], min_lim[i])
                    # Set y limits with padding
                    self.new_ylim[i] = (min_lim[i]-pad, max_lim[i]+pad)
                    ax.set_ylim(self.new_ylim[i])

            self.button.on_clicked(self.callback_button)
            for i, ax in enumerate(self.axs):
                self.fig.canvas.mpl_connect(
                    'button_press_event', self.callback_xlim[i])


class LiveSpatialPlot(Live2DPlot):
    """Reads in USBL location and data of interest to generate live spatial map overviews."""

    def __init__(self, loc_file, data_file, map_time_index=0, map_index=[1, 2], data_time_index=0,
                 data_index=[1, 2], ax_names=["Y1", "Y2"], max_pts=3600):
        """Initializes a live spatial plot.

            Arguments:
                loc_file (str): filepointer to relevant USBL data
                data_file (str): filepointer to relevant SENTRY data
                map_time_index (int): time index for USBL data
                map_index (list(int)): columns with location data
                data_time_index (int): time index for SENTRY data
                data_index (list(int)): what quantities for SENTRY data to plot
                ax_names (list(str)): names of the data to plot
                max_pts (int): maximum number of plotted points
            """
        self.fig = plt.figure()
        self.loc_file = loc_file
        self.data_file = data_file
        self.map_time_index = map_time_index
        self.data_time_index = data_time_index
        self.map_index = map_index
        self.data_index = data_index
        self.ax_names = ax_names
        self.num = len(ax_names)  # number of subplots
        self.max_pts = max_pts
        self.axs = []
        self.callback_reset = []

        # Initialize button
        buttonax = self.fig.add_axes([0.45, 0.9, 0.19, 0.075])
        self.button = Button(buttonax, "Home View")

        self.live_mode = [True]*self.num
        self.xlim = [None]*self.num
        self.ylim = [None]*self.num
        self.prev_xlim = [None]*self.num
        self.prev_ylim = [None]*self.num
        self.new_xlim = [None]*self.num
        self.new_ylim = [None]*self.num
        self.button_time = time.time()

        # Create the subplots and their callbacks
        for i in range(1, self.num+1):
            self.axs.append(self.fig.add_subplot(self.num, 1, i))
            self.callback_reset.append(CallbackXlimArbitrary(self, i-1))

        # Create the refreshing plot
        ani = animation.FuncAnimation(
            self.fig, self.animate, interval=50, repeat=False)
        plt.show()

    def animate(self, i):
        """How the plot should refresh over time."""
        # Grab the data being written to file
        if os.path.isfile(self.loc_file):
            locs = pd.read_csv(self.loc_file, sep=",", header=None)
            locs[self.map_time_index] = pd.to_datetime(locs[self.map_time_index],
                                                       utc=True)
            cols_to_keep = [self.map_time_index]
            for y in self.map_index:
                cols_to_keep.append(y)
            locs = locs.loc[:, cols_to_keep]
            locs = locs.set_index(self.map_time_index).sort_index()
            locs.columns = ["lat", "long", "depth"]

        if os.path.isfile(self.data_file):
            data = pd.read_csv(self.data_file, sep=",", header=None)
            data[self.data_time_index] = pd.to_datetime(data[self.data_time_index],
                                                        utc=True)
            cols_to_keep = [self.data_time_index]
            for y in self.data_index:
                cols_to_keep.append(y)
            data = data.loc[:, cols_to_keep]
            data = data.set_index(self.data_time_index).sort_index()
            data.columns = self.ax_names

        merged = pd.merge_asof(locs, data, left_index=True, right_index=True)

        # Capture only the most recent max_pts
        if len(merged) > self.max_pts:
            merged = merged.tail(self.max_pts)

        # Format the axes for the live time plot
        for i, ax in enumerate(self.axs):
            ax.clear()
            ax.xaxis.set_major_locator(plt.MaxNLocator(10))
            ax.yaxis.set_major_locator(plt.MaxNLocator(10))
            ax.set_title(self.ax_names[i])

            for i, ax in enumerate(self.axs):
                scat = ax.scatter(merged["lat"],
                                  merged["long"],
                                  c=merged[self.ax_names[i]],
                                  cmap="viridis")

                from mpl_toolkits.axes_grid1 import make_axes_locatable
                divider = make_axes_locatable(ax)
                cax = divider.append_axes('right', size='5%', pad=0.05)
                self.fig.colorbar(scat, cax=cax, orientation='vertical')


class SentryDashboard(object):
    """Creates a plotly dashboard that updates with streamed data."""

    def __init__(self, sentryfile, sensorfile, metsfile, backscatterfile, usblfile, bathyfile, currentfile, keys, numkeys):
        self.datafile = sentryfile  # base case sentry data
        self.bathyfile = bathyfile  # bathy underlay
        self.keys = keys.split(",")  # keys to display on charts
        self.numkeys = numkeys  # number of keys to display on quickviews

        self.sensorfile = sensorfile  # experimental data
        if self.sensorfile == 'None':
            self.sensorfile = None
        self.metsfile = metsfile  # mets methane sensor data
        if self.metsfile == 'None':
            self.metsfile = None
        self.backscatterfile = backscatterfile  # aux OBS data
        if self.backscatterfile == 'None':
            self.backscatterfile = None
        self.usblfile = usblfile  # usbl nav data
        if self.usblfile == 'None':
            self.usblfile = None
        self.currentfile = currentfile  # caux current data
        if self.currentfile == "None":
            self.currentfile = None
        

        # read in the initial sentry science and extra sensor data
        self.df = self.read_and_combine_dataframes(include_location=False)
        self.last_t = np.nanmax(self.df.t)
        self.last_current_t = np.nanmax(self.df.t)

        # create a dictionary of sliders
        self.sliders = {}
        self.current_sliders = {}
        for key in self.keys:
            self.sliders[key] = dcc.RangeSlider(np.nanmin(self.df[key]),
                                                np.nanmax(self.df[key]),
                                                value=[np.nanmin(self.df[key]), np.nanmax(self.df[key])],
                                                id='maptime-slider')
            self.current_sliders[key] = dcc.RangeSlider(np.nanmin(self.df[key]),
                                                        np.nanmax(self.df[key]),
                                                        value=[np.nanmin(self.df[key]), np.nanmax(self.df[key])],
                                                        id='current-slider')

        # cache the bathy underlay in memory
        self.bathy = self.get_bathy_data()
        self.bathy_3dplot = go.Mesh3d(x=self.bathy.lon[0::10],
                                      y=self.bathy.lat[0::10],
                                      z=self.bathy.depth[0::10],
                                      intensity=self.bathy.depth[0::10],
                                      colorscale='Viridis',
                                      opacity=0.50,
                                      name="Bathy")
        lonmin, lonmax = self.bathy.lon.min(), self.bathy.lon.max()
        latmin, latmax = self.bathy.lat.min(), self.bathy.lat.max()
        xlon = np.linspace(lonmin, lonmax, 200)
        ylat = np.linspace(latmin, latmax, 200)
        xlon, ylat = np.meshgrid(xlon, ylat)
        Z = griddata((self.bathy.lon, self.bathy.lat),
                     self.bathy.depth, (xlon, ylat), method="cubic")
        self.bathy_2dplot = go.Contour(x=xlon[0],
                                       y=ylat[:, 0],
                                       z=Z,
                                       contours=dict(
                                           start=-2800., end=-2000., size=20),
                                       contours_coloring="lines",
                                       colorscale="Greys",
                                       line=dict(width=0.5),
                                       name="Bathy")
        # vent_sites_lon = [-129.0662, -129.0756, -
        #                   129.0894, -129.0981, -129.1082]
        # vent_sites_lat = [47.9969, 47.9822, 47.9666, 47.9487, 47.9233]
        vent_sites_lon = [-129.0981, -129.0894]
        vent_sites_lat = [47.9487, 47.9666]
        self.vents_plot = go.Scatter(x=vent_sites_lon,
                                     y=vent_sites_lat,
                                     mode="markers",
                                     name="Vents")
        vent_sites_easting, vent_sites_northing, _, _ = utm.from_latlon(
            np.asarray(vent_sites_lat), np.asarray(vent_sites_lon))
        self.vents_m_plot = go.Scatter(x=vent_sites_easting,
                                       y=vent_sites_northing,
                                       mode="markers",
                                       marker=dict(size=20, color="green"),
                                       name="Vents")
        # moorings_lon = [-129.0823, -129.0875, -129.0989, -129.1067]
        # moorings_lat = [47.9737, 47.9747, 47.9334, 47.9355]
        moorings_lon = []  # [-129.0823, -129.0875]#, -129.0989, -129.1067]
        moorings_lat = []  # [47.9737, 47.9747]#, 47.9334, 47.9355]
        self.moorings_plot = go.Scatter(x=moorings_lon,
                                        y=moorings_lat,
                                        mode="markers",
                                        name="Moorings")

        # create the dash app and register layout
        app = Dash(__name__, use_pages=True, pages_folder="",
                   external_stylesheets=[dbc.themes.BOOTSTRAP])
        dash.register_page(
            "home", path="/", layout=self._create_home_layout())
        dash.register_page("extended_timeseries",
                           layout=self._create_timeseries_layout())
        dash.register_page(
            "simple_exploration", layout=self._create_threshold_layout())
        dash.register_page("3D_map", layout=self._create_map_layout())
        dash.register_page("overhead_map_with_time",
                           layout=self._create_maptime_layout())
        if self.sensorfile is not None:
            dash.register_page("sage_engineering",
                               layout=self._create_SAGE_layout())
        if self.currentfile is not None:
            dash.register_page("ocean_currents_data",
                               layout=self._create_current_layout())

        app.layout = self._create_app_layout()

        ############
        # create dashboard callbacks
        ############

        # callback for quickview home page with autorefresh timelines
        @callback(Output("graph-home-quickview", "figure"),
                  Input("graph-home-update", "n_intervals"))
        def plot_quickview(n):
            self.df = self.read_and_combine_dataframes(include_location=True)
            time_plots = make_subplots(rows=self.numkeys, cols=1, shared_xaxes=True, vertical_spacing=0.025, subplot_titles=self.keys)
            for i in range(0, self.numkeys):
                time_plots.add_trace(go.Scatter(x=self.df.index,
                                                y=self.df[self.keys[i]],
                                                mode="lines",
                                                name=self.keys[i],), row=i+1, col=1)
            time_plots.update_layout(
                height=1900, uirevision=True, showlegend=False, margin=dict(t=20), font=dict(size=20), hoverlabel=dict(font_size=20))
            return(time_plots)

        # callback for main page/autorefreshing timelines
        @callback(Output("graph-content-turbidity", "figure"),
                  Output("graph-content-orp", "figure"),
                  Output("graph-content-depth", "figure"),
                  Output("graph-content-methane", "figure"),
                  Output("graph-content-potden", "figure"),
                  Output("graph-content-spice", "figure"),
                  Output("graph-content-temperature", "figure"),
                  Output("graph-content-salinity", "figure"),
                  Output("graph-content-oxygen", "figure"),
                  Input("graph-update", "n_intervals"))
        def stream(n):
            self.df = self.read_and_combine_dataframes(include_location=True)
            figturb = px.line(self.df, x=self.df.index, y=self.df.Turbidity,  hover_data=[
                              "lat", "lon", "Depth"])
            figturb.update_layout(uirevision=True, font=dict(size=20))
            figorp = px.line(self.df, x=self.df.index,
                             y=self.df.ORP, hover_data=["lat", "lon", "Depth"])
            figorp.update_layout(uirevision=True, font=dict(
                size=20), hoverlabel=dict(font_size=20))
            figtemp = px.line(self.df, x=self.df.index, y=self.df.Temperature, hover_data=[
                              "lat", "lon", "Depth"])
            figtemp.update_layout(uirevision=True, font=dict(
                size=20), hoverlabel=dict(font_size=20))
            if self.sensorfile is not None:
                figmethane = px.line(self.df, x=self.df.index, y=self.df.methane_ppm, hover_data=[
                                     "lat", "lon", "Depth"], markers=True)
                figmethane.update_layout(uirevision=True, font=dict(
                    size=20), hoverlabel=dict(font_size=20))
            else:
                figmethane = px.line(
                    x=self.df.index, y=np.zeros_like(self.df.t))
                figmethane.update_layout(uirevision=True, font=dict(size=20))
            if self.metsfile is not None:
                figmethane = px.line(self.df, x=self.df.index, y=self.df.methane_mets, hover_data=[
                                     "lat", "lon", "Depth"], markers=True)
                figmethane.update_layout(uirevision=True, font=dict(
                    size=20), hoverlabel=dict(font_size=20))
            else:
                figmethane = px.line(
                    x=self.df.index, y=np.zeros_like(self.df.t))
                figmethane.update_layout(uirevision=True, font=dict(size=20))
            figdepth = px.line(self.df, x=self.df.index, y=-self.df.Depth, hover_data=[
                               "lat", "lon", "Depth"])
            figdepth.update_layout(uirevision=True, font=dict(
                size=20), hoverlabel=dict(font_size=20))
            figo2 = px.line(self.df, x=self.df.index, y=self.df.Oxygen, hover_data=[
                            "lat", "lon", "Depth"])
            figo2.update_layout(uirevision=True, font=dict(
                size=20), hoverlabel=dict(font_size=20))
            figsalt = px.line(self.df, x=self.df.index, y=self.df.Salinity, hover_data=[
                              "lat", "lon", "Depth"])
            figsalt.update_layout(uirevision=True, font=dict(
                size=20), hoverlabel=dict(font_size=20))
            figpotden = px.line(self.df, x=self.df.index, y=-self.df.potential_density, hover_data=[
                "lat", "lon", "Depth"])
            figpotden.update_layout(uirevision=True, font=dict(
                size=20), hoverlabel=dict(font_size=20))
            figspice = px.line(self.df, x=self.df.index, y=self.df.spice, hover_data=[
                "lat", "lon", "Depth"])
            figspice.update_layout(uirevision=True, font=dict(
                size=20), hoverlabel=dict(font_size=20))
            return(figturb, figorp, figmethane, figdepth, figpotden, figspice, figtemp, figsalt, figo2)

        # callback for SAGE engineering page
        @callback(Output("graph-content-sage", "figure"),
                  Input("sage-graph-update", "n_intervals"))
        def plot_sage_engineering(n):
            """Create streaming plots of the critical SAGE engineering data."""
            sensor_df = self.read_sensorfile()
            time_plots = make_subplots(rows=6, cols=1, shared_xaxes=True, vertical_spacing=0.025, subplot_titles=[
                                       "Methane (ppm)", "Inlet Temperature (C)", "Junction Temperature (C)", "Housing Pressure (mbar)", "Junction Humidity (%)", "Average PD Voltage"])

            if sensor_df is not None:
                time_plots.add_trace(go.Scatter(
                    x=sensor_df.index, y=sensor_df.methane_ppm, mode="lines", name="Methane"), row=1, col=1)
                time_plots.add_trace(go.Scatter(
                    x=sensor_df.index, y=sensor_df.inletTemperature_C, mode="lines", name="Inlet Temperature"), row=2, col=1)
                time_plots.add_trace(go.Scatter(
                    x=sensor_df.index, y=sensor_df.junctionTemperature_C, mode="lines", name="Junction Temperature"), row=3, col=1)
                time_plots.add_trace(go.Scatter(
                    x=sensor_df.index, y=sensor_df.housingPressure_mbar, mode="lines", name="Housing Pressure"), row=4, col=1)
                time_plots.add_trace(go.Scatter(
                    x=sensor_df.index, y=sensor_df.junctionHumidity_per, mode="lines", name="Junction Humidity"), row=5, col=1)
                time_plots.add_trace(go.Scatter(
                    x=sensor_df.index, y=sensor_df.avgPDVolts, mode="lines", name="Average PD Voltage"), row=6, col=1)

            time_plots.update_layout(
                height=1800, uirevision=True, showlegend=False, font=dict(size=20), hoverlabel=dict(font_size=20))
            return(time_plots)

        # callback for correlations/threshold examination page

        @callback(Output("graph-content-correlations", "figure"),
                  Output("graph-content-anomaly-x", "figure"),
                  Output("graph-content-anomaly-y", "figure"),
                  Input("x-axis-selection", "value"),
                  Input("y-axis-selection", "value"),
                  Input("c-axis-selection", "value"),
                  Input("anomaly-control", "value"))
        def plot_thresholds(xval, yval, cval, sdscale):
            # compute standard deviation and mean
            df_copy = self.read_and_combine_dataframes(include_location=True)

            if cval == "Anomaly":
                xvalmean, xvalstd = df_copy[xval].mean(), df_copy[xval].std()
                yvalmean, yvalstd = df_copy[yval].mean(), df_copy[yval].std()

                # classify data based on standard deviation threshold
                df_copy.loc[:, f"{xval}_meandiff"] = df_copy.apply(
                    lambda x: np.fabs(x[xval] - xvalmean), axis=1)
                df_copy.loc[:,
                            f"{xval}_outside"] = (df_copy[f"{xval}_meandiff"] >= xvalstd * sdscale).astype(float)
                df_copy.loc[:, f"{yval}_meandiff"] = df_copy.apply(
                    lambda x: np.fabs(x[yval] - yvalmean), axis=1)
                df_copy.loc[:,
                            f"{yval}_outside"] = (df_copy[f"{yval}_meandiff"] >= yvalstd * sdscale).astype(float)
                df_copy.loc[:, f"Anomaly"] = df_copy[f"{yval}_outside"].astype(
                    float) + df_copy[f"{xval}_outside"].astype(float)

            # create plots
            fig = px.scatter(df_copy, x=xval, y=yval, color=cval, marginal_x="violin",
                             marginal_y="violin", hover_data=["lat", "lon", "Depth"])
            fig.update_layout(uirevision=True, font=dict(
                size=20), hoverlabel=dict(font_size=20))

            if cval == "Anomaly":
                scatx = px.scatter(df_copy, x=df_copy.index,
                                   y=xval, color=f"{xval}_outside", hover_data=["lat", "lon", "Depth"])
                scaty = px.scatter(df_copy, x=df_copy.index,
                                   y=yval, color=f"{yval}_outside", hover_data=["lat", "lon", "Depth"])
            else:
                scatx = px.scatter(df_copy, x=df_copy.index,
                                   y=xval, color=f"{cval}", hover_data=["lat", "lon", "Depth"])
                scaty = px.scatter(df_copy, x=df_copy.index,
                                   y=yval, color=f"{cval}", hover_data=["lat", "lon", "Depth"])
            scatx.update_layout(font=dict(size=20),
                                hoverlabel=dict(font_size=20))
            scaty.update_layout(font=dict(size=20),
                                hoverlabel=dict(font_size=20))
            return(fig, scatx, scaty)

        # callback for map rendering page
        @callback(Output("3d-map", "figure"),
                  Input("map-selection", "value"))
        def plot_maps(vtarg):
            """Render the maps on the maps page."""
            # get the usbl relevant data
            map_df = self.read_and_combine_dataframes(include_location=True)
            map_plots = make_subplots(rows=1, cols=2, specs=[
                                      [{"type": "scatter3d"}, {"type": "scatter3d"}]])
            map_plots.add_trace(self.bathy_3dplot, row=1, col=1)
            map_plots.add_trace(go.Scatter3d(x=map_df['lon'],
                                             y=map_df['lat'],
                                             z=map_df['Depth'],
                                             mode="markers",
                                             marker=dict(size=2,
                                                         color=map_df[vtarg],
                                                         opacity=0.7,
                                                         colorscale="Inferno",
                                                         cmin=np.nanpercentile(
                                                             map_df[vtarg], 10),
                                                         cmax=np.nanpercentile(
                                                             map_df[vtarg], 90),
                                                         colorbar=dict(thickness=30, x=-0.1)),
                                             hovertext=map_df.index,
                                             hoverinfo="name+x+y+z+text"), row=1, col=1)
            map_plots.add_trace(go.Scatter3d(x=map_df['lon'],
                                             y=map_df['lat'],
                                             z=map_df['t'],
                                             mode="markers",
                                             marker=dict(size=2,
                                                         color=map_df[vtarg],
                                                         opacity=0.7,
                                                         colorscale="Inferno",
                                                         cmin=np.nanpercentile(
                                                             map_df[vtarg], 10),
                                                         cmax=np.nanpercentile(
                                                             map_df[vtarg], 90),
                                                         colorbar=dict(thickness=30, x=-0.1)),
                                             hovertext=map_df.index,
                                             hoverinfo="name+x+y+z+text"), row=1, col=2)
            return(map_plots)

        @callback(Output("maptime-slider-time", "min"),
                  Output("maptime-slider-time", "max"),
                  Output("maptime-slider-time", "value"),
                  Input("maptime-timer-update", "n_intervals"),
                  Input("maptime-slider-time", "value"))
        def update_maptime_time_slider(n, tlims):
            slide_max = tlims[-1]
            self.df = self.read_and_combine_dataframes(include_location=True)
            if slide_max >= self.last_t:
                self.last_t = np.nanmax(self.df.t)
                return(np.nanmin(self.df.t), np.nanmax(self.df.t), [tlims[0], np.nanmax(self.df.t)])
            else:
                return(np.nanmin(self.df.t), np.nanmax(self.df.t), tlims)
        

        @callback(Output("maptime-rangeslider-slider", "children"),
                  Input("maptime-selection", "value"))
        def make_maptime_slider(val):
            return(self.sliders[val])
        
        @callback(Output("graph-maptime-time", "figure"),
                  Output("graph-maptime-map", "figure"),
                  Input("maptime-selection", "value"),
                  Input("maptime-slider", "value"),
                  Input("maptime-slider-time", "value"),
                  Input("graph-maptime-map", "clickData"),
                  Input("graph-maptime-time", "clickData"))
        def plot_maptime(vtarg, sliders, time_lims, hovermap, hovertime):
            """Render the map and timeline on the Map-time page."""
            self.df = self.read_and_combine_dataframes(include_location=True)
            df = self.df.copy()
            df = df[(df.t >= time_lims[0]) & (df.t <= time_lims[1])]
            
            # make sure the rendering options for the overhead colorbar are updated
            slider_min = np.nanmin(df[vtarg])
            if vtarg == "dORPdt":
                slider_max = 0
            else:
                slider_max = np.nanmax(df[vtarg])
            
            if sliders[0] >= slider_min and sliders[1] <= slider_max and sliders[0] < sliders[1]:
                sliders = sliders
            elif sliders[0] >= slider_min and sliders[0] < slider_max:
                sliders = [sliders[0], slider_max]
            elif sliders[1] <= slider_max and sliders[0] < sliders[1]:
                sliders = [slider_min, sliders[1]]
            else:
                sliders = [slider_min, slider_max]
            self.sliders[vtarg].value = sliders
            self.sliders[vtarg].min = np.nanmin(df[vtarg])
            self.sliders[vtarg].max = np.nanmax(df[vtarg])

            # plot the overhead map
            if vtarg is not None:
                tfig = go.Scatter(x=df.index, y=df[vtarg], mode="lines")
                mfig = go.Scatter(x=df.lon,
                                  y=df.lat,
                                  mode="markers",
                                  marker=dict(size=5,
                                              color=df[vtarg],
                                              colorscale="Inferno",
                                              cmin=sliders[0],
                                              cmax=sliders[1],
                                              colorbar=dict(thickness=20,
                                                            x=-0.2,
                                                            tickfont=dict(size=20))))
            map_fig = [self.bathy_2dplot,
                       self.vents_plot, self.moorings_plot, mfig]
            time_fig = [tfig]

            # add click-interface information
            if hovertime is not None:
                hdata = hovertime["points"][0]
                loc = df[(df.index == hdata["x"])]
                map_fig.append(go.Scatter(x=loc.lon,
                                          y=loc.lat,
                                          mode="markers",
                                          marker=dict(size=20)))
            if hovermap is not None:
                hdata = hovermap["points"][0]
                time = df[(df.lon == hdata["x"]) & (df.lat == hdata["y"])]
                time_fig.append(go.Scatter(
                    x=time.index, y=time[vtarg], mode="markers", marker=dict(size=10, color=['#EF553B'])))

            # create the final map
            final_map_fig = go.Figure(map_fig)
            final_map_fig.update_yaxes(scaleanchor="x", scaleratio=1)
            final_map_fig.update_layout(uirevision=True, font=dict(
                size=20), hoverlabel=dict(font_size=20))
            final_time_fig = go.Figure(time_fig)
            final_time_fig.update_layout(uirevision=True, showlegend=False, font=dict(
                size=20), hoverlabel=dict(font_size=20))

            return(final_time_fig, final_map_fig)

        
        @callback(Output("current-slider-time", "min"),
                  Output("current-slider-time", "max"),
                  Output("current-slider-time", "value"),
                  Input("current-timer-update", "n_intervals"),
                  Input("current-slider-time", "value"))
        def update_current_time_slider(n, tlims):
            slide_max = tlims[-1]
            self.df = self.read_and_combine_dataframes(include_location=True)
            if slide_max >= self.last_current_t:
                self.last_current_t = np.nanmax(self.df.t)
                return(np.nanmin(self.df.t), np.nanmax(self.df.t), [tlims[0], np.nanmax(self.df.t)])
            else:
                return(np.nanmin(self.df.t), np.nanmax(self.df.t), tlims)

        @callback(Output("current-rangeslider-slider", "children"),
                  Input("current-selection", "value"))
        def make_current_slider(val):
            return(self.current_sliders[val])

        @callback(Output("graph-content-currentmap", "figure"),
                  Output("graph-content-currentx", "figure"),
                  Output("graph-content-currenty", "figure"),
                  Input("current-selection", "value"),
                  Input("current-slider", "value"),
                  Input("current-slider-time", "value"))
        def plot_ocean_currents(vtarg, sliders, time_lims):
            """Create the visualizations of ocean current from file."""
            self.df = self.read_and_combine_dataframes(include_location=True)
            df = self.df.copy()
            df = df[(df.t >= time_lims[0]) & (df.t <= time_lims[1])]
           
           # make sure the rendering options for the overhead colorbar are updated
            slider_min = np.nanmin(df[vtarg])
            if vtarg == "dORPdt":
                slider_max = 0
            else:
                slider_max = np.nanmax(df[vtarg])
            if sliders[0] >= slider_min and sliders[1] <= slider_max and sliders[0] < sliders[1]:
                sliders = sliders
            elif sliders[0] >= slider_min and sliders[0] < slider_max:
                sliders = [sliders[0], slider_max]
            elif sliders[1] <= slider_max and sliders[0] < sliders[1]:
                sliders = [slider_min, sliders[1]]
            else:
                sliders = [slider_min, slider_max]
            self.current_sliders[vtarg].value = sliders
            self.current_sliders[vtarg].min = np.nanmin(df[vtarg])
            self.current_sliders[vtarg].max = np.nanmax(df[vtarg])
            
            quiv = ff.create_quiver(df.easting[::10], df.northing[::10], df.true_veast[::10],
                                    df.true_vnorth[::10], scale=3000, arrow_scale=0.1, name='quiver', line_width=2)
            quiv.add_trace(go.Scatter(x=df.easting,
                                      y=df.northing,
                                      mode="markers",
                                      marker=dict(size=5,
                                                  color=df[vtarg],
                                                  colorscale="Inferno",
                                                  cmin=sliders[0],
                                                  cmax=sliders[1],
                                                  colorbar=dict(thickness=20,
                                                                x=-0.2,
                                                                tickfont=dict(size=20)))))
            quiv.add_trace(self.vents_m_plot)
            currentx_fig = go.Figure(go.Scatter(x=df.index,
                                      y=df.true_veast,
                                      mode="markers",
                                      marker=dict(size=3),
                                      name="Current Magnitude - True East"))
            currenty_fig = go.Figure(go.Scatter(x=df.index,
                                      y=df.true_vnorth,
                                      mode="markers",
                                      marker=dict(size=3),
                                      name="Current Magnitude - True North"))
            quiv.update_yaxes(scaleanchor="x", scaleratio=1)
            quiv.update_layout(showlegend=False, uirevision=True)
            currentx_fig.update_layout(title="Current Magnitude - True East", uirevision=True)
            currenty_fig.update_layout(title="Current Magnitude - True North", uirevision=True)
            return(quiv, currentx_fig, currenty_fig)

        app.run(debug=True)

    def _create_app_layout(self):
        """Creates the overall app layout."""
        layout = html.Div([html.Div([html.Div(dcc.Link(
            f"{page['name']}", href=page["relative_path"]), style={"display": "inline-block", "font-size": "24px", "padding": "1vh"}) for page in dash.page_registry.values()]), dash.page_container, ])
        return(layout)

    def _create_home_layout(self):
        """Create the small-timeseries viewer."""
        layout = html.Div(children=[html.H1(children="Sentry Dash Quickview", style={"textAlign": "center"}),
                                    dcc.Graph(id="graph-home-quickview"),
                                    dcc.Interval(id="graph-home-update", interval=30*1000, n_intervals=0)])
        return(layout)

    def _create_timeseries_layout(self):
        """Create the dashboard scene."""
        layout = html.Div([html.H1(children="Extended Timeseries Dashboard", style={"textAlign": "center"}),
                           dcc.Graph(id="graph-content-turbidity"),
                           dcc.Graph(id="graph-content-orp"),
                           dcc.Graph(id="graph-content-methane"),
                           dcc.Graph(id="graph-content-depth"),
                           dcc.Graph(id="graph-content-potden"),
                           dcc.Graph(id="graph-content-spice"),
                           dcc.Graph(id="graph-content-temperature"),
                           dcc.Graph(id="graph-content-salinity"),
                           dcc.Graph(id="graph-content-oxygen"),
                           dcc.Interval(id="graph-update", interval=30*1000, n_intervals=0)])
        return(layout)

    def _create_SAGE_layout(self):
        """Creates a SAGE engineering page."""
        layout = html.Div([html.H1(children="SAGE Engineering Data", style={"textAlign": "center"}),
                           dcc.Graph(id="graph-content-sage"),
                           dcc.Interval(id="sage-graph-update", interval=30*1000, n_intervals=0)])
        return(layout)

    def _create_threshold_layout(self):
        """Create the ability to examine thresholds in a dashboard."""
        layout = dbc.Container([dbc.Row([html.Div(children=[html.H1(children="Simple Data Exploration Dashboard", style={"textAlign": "center"})]),
                                         html.Div(children=["Select x variable:",
                                                            dcc.Dropdown(self.keys, "Turbidity", id="x-axis-selection")]),
                                         html.Div(children=["Select y variable:",
                                                            dcc.Dropdown(self.keys, "Temperature", id="y-axis-selection")],
                                                  style={'margin-top': 20}),
                                         html.Div(children=["Select color variable:",
                                                            dcc.Dropdown(self.keys+["Anomaly"], "Anomaly", id="c-axis-selection")],
                                                  style={'margin-top': 20}),
                                         html.Div(children=["Set anomaly detection threshold (standard deviations):",
                                                            dcc.Slider(0, 4, 0.5, value=1,
                                                                       tooltip={
                                                                           "placement": "bottom", "always_visible": True},
                                                                       id="anomaly-control")],
                                                  style={'margin-top': 20})]),
                                dbc.Row([dbc.Col([dcc.Graph(id="graph-content-correlations", style={'width': '45vw', 'height': '60vh'})]),
                                         dbc.Col([dcc.Graph(id="graph-content-anomaly-x", style={'width': '50vw', 'height': '30vh'}),
                                                  dcc.Graph(id="graph-content-anomaly-y", style={'width': '50vw', 'height': '30vh'})]), ], style={'display': 'flex'})], fluid=True)
        return(layout)

    def _create_map_layout(self):
        """Create the map dashboard scene."""
        layout = html.Div([html.H1(children="Map Dashboard", style={"textAlign": "center"}),
                           html.Div(children=["Select variable to visualize:",
                                              dcc.Dropdown(self.keys, self.keys[0], id="map-selection")], style={"margin-top": 20}),
                           html.Div(children=[dcc.Graph(id="3d-map", style={'height': '90vh'})])])
        return(layout)

    def _create_maptime_layout(self):
        """Create a map and timeline with hover capabilities."""
        layout = dbc.Container([dbc.Row([html.Div(children=[html.H1(children="Map-Time Dashboard", style={"textAlign": "center"}),
                                                            dcc.Interval(id="maptime-timer-update", interval=30*1000, n_intervals=0),]),
                                         html.Div(children=["Select variable:",
                                                            dcc.Dropdown(self.keys, self.keys[0], id="maptime-selection")]),
                                         html.Div(children=["Set rendering scale:"], style={"margin-top": 20}),
                                         html.Div(id='maptime-rangeslider-slider'),
                                         html.Div(children=["Set times to display:",
                                                            dcc.RangeSlider(np.nanmin(self.df.t),
                                                                            np.nanmax(self.df.t),
                                                                            value=[np.nanmin(self.df.t), np.nanmax(self.df.t)+24*3600.],
                                                                            marks={int(date): {"label": str(pd.to_datetime(
                                                                                date, unit="s"))} for each, date in enumerate(self.df.t[::100])},
                                                                            id='maptime-slider-time')],
                                                  style={"margin-top": 20})
                                         ]),
                                dbc.Row([dbc.Col([dcc.Graph(id="graph-maptime-time", style={"width": "50vw", "height": "60vh"})]),
                                         dbc.Col([dcc.Graph(id="graph-maptime-map", style={"width": "45vw", "height": "80vh"})]), ], style={"display": "flex"})], fluid=True)
        return(layout)

    def _create_current_layout(self):
        """Create the layout for plotting current data over plotted points."""
        layout = dbc.Container([dbc.Row([html.Div(children=[html.H1(children="Ocean Currents Dashboard", style={"textAlign": "center"}),
                                                            dcc.Interval(id="current-timer-update", interval=30*1000, n_intervals=0)]),
                                         html.Div(children=["Select variable:",
                                                            dcc.Dropdown(self.keys, self.keys[0], id="current-selection")]),
                                         html.Div(children=["Set rendering scale:"], style={"margin-top":20}),
                                         html.Div(id="current-rangeslider-slider"),
                                         html.Div(children=["Set times to display:",
                                                            dcc.RangeSlider(np.nanmin(self.df.t),
                                                                            np.nanmax(
                                                                                self.df.t),
                                                                            value=[
                                                                                np.nanmin(self.df.t), np.nanmax(self.df.t) + 24 * 3600.],
                                                                            marks={int(date): {"label": str(pd.to_datetime(
                                                                                date, unit="s"))} for each, date in enumerate(self.df.t[::100])},
                                                                            id='current-slider-time')],
                                                  style={"margin-top": 20})
                                         ]),
                                dbc.Row([dbc.Col([dcc.Graph(id="graph-content-currentmap", style={'width': '45vw', 'height': '60vh'})]),
                                         dbc.Col([dcc.Graph(id="graph-content-currentx", style={'width': '50vw', 'height': '30vh'}),
                                                  dcc.Graph(id="graph-content-currenty", style={'width': '50vw', 'height': '30vh'})]), ], style={'display': 'flex'})], fluid=True)
        return(layout)

    def get_bathy_data(self):
        """Read in the data from a bathy file, if any."""
        bathy_df = pd.read_table(self.bathyfile, names=[
            "lon", "lat", "depth"], sep=",").dropna()
        eb, nb, _, _ = utm.from_latlon(
            bathy_df.lat.values, bathy_df.lon.values)
        bathy_df.loc[:, "northing"] = nb
        bathy_df.loc[:, "easting"] = eb
        return bathy_df

    def compute_potential_density_and_spice(self, salt, temp, depth, lat, lon):
        """Computed oceanographic measurements."""
        press = gsw.p_from_z(-depth, lat=lat)
        SA = gsw.SA_from_SP(SP=salt, p=press, lat=lat, lon=lon)
        dp = gsw.pot_rho_t_exact(SA=SA, t=temp, p=press, p_ref=0)
        CT = gsw.CT_from_t(SA=SA, t=temp, p=press)
        spice = gsw.spiciness2(SA=SA, CT=CT)
        return dp, spice

    def read_and_combine_dataframes(self, include_location=False):
        """Helper to constantly create new DF objects for plotting."""
        # combine only the sentry and sensor dataframes
        df = pd.read_csv(self.datafile, sep=",", header=None, names=[
            "Time", "Oxygen", "Turbidity", "ORP", "Temperature", "Salinity", "Depth"])
        df["Depth"] = -df["Depth"]
        df["Time"] = pd.to_datetime(df["Time"])
        df.loc[:, "t"] = (
            df["Time"] - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")
        df.loc[:, "dORPdt"] = df.ORP.rolling(window=2).apply(lambda x: (x.iloc[-1] - x.iloc[0])/(2))
        dORPdt_mask = df.dORPdt < 0.0
        df.loc[:, "dORPdt_log"] = np.log(np.fabs(df.dORPdt * dORPdt_mask))
        df["dORPdt_log"].replace([-np.inf, np.inf], -15, inplace=True)

        merge_df = df
        sentry_data_index = merge_df.t.values[0]

        # read in the methane sensor data
        if self.sensorfile is not None:
            self.sensor = pd.read_table(self.sensorfile,
                                        sep=",",
                                        header=None,
                                        names=["msgTime",
                                               "sensorTime",
                                               "onboardFileNum",
                                               "methane_ppm",
                                               "inletPressure_mbar",
                                               "inletTemperature_C",
                                               "housingPressure_mbar",
                                               "waterTemperature_C",
                                               "junctionTemperature_C",
                                               "junctionHumidity_per",
                                               "avgPDVolts",
                                               "inletHeaterState",
                                               "junctionHeaterState"])
            self.sensor["methaneTime"] = pd.to_datetime(
                self.sensor["sensorTime"], format="%Y%m%dT%H%M%S")
            self.sensor.loc[:, "t"] = (self.sensor["methaneTime"] -
                                       pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")

            # interpolate the methane sensor data onto the sentry data
            merge_df = merge_df.merge(self.sensor, how="outer", on="t")
        else:
            pass
        
        if self.metsfile is not None:
            self.mets = pd.read_table(self.metsfile,
                                        sep=",",
                                        header=None,
                                        names=["msgTimeMets",
                                               "sensorTimeMets",
                                               "instrument_name_mets",
                                               "process_from_volts",
                                               "temp_mets_count",
                                               "temperature_mets",
                                               "methane_mets_count",
                                               "methane_mets"])
            self.mets["methaneTimeMets"] = pd.to_datetime(self.mets["sensorTimeMets"])
            self.mets.loc[:, "t"] = (self.mets["methaneTimeMets"] -
                                       pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")
            self.mets["methane_mets"] = self.mets.apply(lambda x: float(x.methane_mets.strip(" ").strip("?"))*1000., axis=1)

            # interpolate the methane sensor data onto the sentry data
            merge_df = merge_df.merge(self.mets[["t", "methane_mets"]], how="outer", on="t")
        else:
            pass
            
        if self.backscatterfile is not None:
            # SDQ 102:2023-09-12T17:38:44 +0.0342 +0.0000 +0.0000 +0.0000???
            self.backscatter = pd.read_table(self.backscatterfile,
                                        sep=",| ",
                                        engine="python",
                                        header=None,
                                        names=["msgDate",
                                               "msgTime",
                                               "sensorDate",
                                               "sensorTime",
                                               "turbidity_obs_5x",
                                               "temp1",
                                               "temp2",
                                               "temp3"])
            self.backscatter["sensorTimeObs"] = self.backscatter.apply(lambda x: f"{x.sensorDate} {x.sensorTime}",axis=1)
            self.backscatter["TimeObs"] = pd.to_datetime(self.backscatter["sensorTimeObs"])
            self.backscatter.loc[:, "t"] = (self.backscatter["TimeObs"] -
                                       pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")

            # interpolate the methane sensor data onto the sentry data
            merge_df = merge_df.merge(self.backscatter[["t", "turbidity_obs_5x"]], how="outer", on="t")
        else:
            pass

        if include_location is True and self.usblfile is not None:
            # include the usbl location information
            self.usbl = pd.read_table(self.usblfile, sep=",", header=None, names=[
                "timestamp", "lon", "lat", "depth_usbl"])
            self.usbl.loc[:, "usblTime"] = pd.to_datetime(
                self.usbl["timestamp"])
            self.usbl.loc[:, "t"] = (
                self.usbl["usblTime"] - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")
            merge_df = merge_df.merge(self.usbl, how="outer", on="t")
        else:
            merge_df.loc[:, "lat"] = np.zeros_like(merge_df.t)
            merge_df.loc[:, "lon"] = np.zeros_like(merge_df.t)
            merge_df.loc[:, "depth_usbl"] = np.zeros_like(merge_df.t)

        if self.currentfile is not None:
            df = pd.read_csv(self.currentfile,
                             sep=",")
            df = df[(df.t > merge_df.t.values[0]) &
                    (df.t < merge_df.t.values[-1])]
            merge_df = merge_df.merge(df, how="outer", on="t")

        # index by time for consistency
        merge_df = merge_df.sort_values(by="t")
        merge_df = merge_df.drop_duplicates(subset=["t"], keep="first")
        merge_df = merge_df[merge_df.t >= sentry_data_index]
        merge_df.loc[:, "Global_Time"] = pd.to_datetime(
            merge_df["t"], unit="s")
        merge_df = merge_df.set_index("Global_Time")
        merge_df = merge_df.interpolate(method="ffill")
        pot_den, spice = self.compute_potential_density_and_spice(merge_df.Salinity.values,
                                                                  merge_df.Temperature.values,
                                                                  -merge_df.Depth.values,
                                                                  merge_df.lat.values,
                                                                  merge_df.lon.values)
        merge_df.loc[:, "spice"] = spice
        merge_df.loc[:, "potential_density"] = pot_den

        if self.usblfile is not None:
            merge_df = merge_df.dropna(subset=["lat", "lon"])
            easting, northing, _, _ = utm.from_latlon(
                merge_df.lat.values, merge_df.lon.values)
            merge_df.loc[:, "northing"] = northing
            merge_df.loc[:, "easting"] = easting

        return(merge_df)  # return the single, combined dataframe

    def read_sensorfile(self):
        """Reads in a separate dataframe for sensor data."""
        # read in the methane sensor data
        if self.sensorfile is not None:
            df = pd.read_table(self.sensorfile,
                               sep=",",
                               header=None,
                               names=["msgTime",
                                      "sensorTime",
                                      "onboardFileNum",
                                      "methane_ppm",
                                      "inletPressure_mbar",
                                      "inletTemperature_C",
                                      "housingPressure_mbar",
                                      "waterTemperature_C",
                                      "junctionTemperature_C",
                                      "junctionHumidity_per",
                                      "avgPDVolts",
                                      "inletHeaterState",
                                      "jSunctionHeaterState"])
            df["methaneTime"] = pd.to_datetime(
                df["sensorTime"], format="%Y%m%dT%H%M%S")
            df.loc[:, "t"] = (df["methaneTime"] -
                              pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")
            df = df.set_index("methaneTime")
            return(df)
        else:
            return(None)
