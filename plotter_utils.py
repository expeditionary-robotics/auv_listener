"""Utilities file for making plotters.

Authors: Genevieve Flaspohler and Victoria Preston
Update: August 2023
Contact: {geflaspo, vpreston}@mit.edu
"""

import os
import time
import pandas as pd
import numpy as np

from dash import Dash, html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import dash
import plotly.express as px
import plotly.graph_objects as go

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
            print("Here")
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

    def __init__(self, datafile, bathyfile, liveplot):
        self.datafile = datafile
        self.bathyfile = bathyfile
        self.liveplot = liveplot

        # read in the continuous data and set timing loop if we are liveplotting
        self.df = pd.read_csv(self.datafile, sep=",", header=None, names=[
                              "Time", "Oxygen", "Turbidity", "ORP", "Temperature", "Salinity", "Depth"])
        self.df["Time"] = pd.to_datetime(self.df["Time"], utc=True)
        self.df = self.df.set_index("Time").sort_index()

        app = Dash(__name__, use_pages=True, pages_folder="",
                   external_stylesheets=[dbc.themes.BOOTSTRAP])
        dash.register_page(
            "home", path="/", layout=self._create_timeseries_layout())
        dash.register_page(
            "correlations", layout=self._create_threshold_layout())
        dash.register_page("map", layout=self._create_map_layout())

        app.layout = self._create_app_layout()

        @callback(Output("graph-content-oxygen", "figure"),
                  Output("graph-content-turbidity", "figure"),
                  Output("graph-content-orp", "figure"),
                  Output("graph-content-temperature", "figure"),
                  Output("graph-content-salinity", "figure"),
                  Output("graph-content-depth", "figure"),
                  Input("graph-update", "n_intervals"))
        def stream(n):
            self.df = pd.read_csv(self.datafile, sep=",", header=None, names=[
                                  "Time", "Oxygen", "Turbidity", "ORP", "Temperature", "Salinity", "Depth"])
            self.df["Time"] = pd.to_datetime(self.df["Time"], utc=True)
            self.df = self.df.set_index("Time").sort_index()
            figo2 = px.line(self.df, x=self.df.index, y=self.df.Oxygen)
            figo2.update_layout(uirevision=True)
            figturb = px.line(self.df, x=self.df.index, y=self.df.Turbidity)
            figturb.update_layout(uirevision=True)
            figorp = px.line(self.df, x=self.df.index, y=self.df.ORP)
            figorp.update_layout(uirevision=True)
            figtemp = px.line(self.df, x=self.df.index, y=self.df.Temperature)
            figtemp.update_layout(uirevision=True)
            figsalt = px.line(self.df, x=self.df.index, y=self.df.Salinity)
            figsalt.update_layout(uirevision=True)
            figdepth = px.line(self.df, x=self.df.index, y=self.df.Depth)
            figdepth.update_layout(uirevision=True)
            return(figo2, figturb, figorp, figtemp, figsalt, figdepth)

        @callback(Output("graph-content-correlations", "figure"),
                  Output("graph-content-anomaly-x", "figure"),
                  Output("graph-content-anomaly-y", "figure"),
                  Input("x-axis-selection", "value"),
                  Input("y-axis-selection", "value"),
                  Input("anomaly-control", "value"))
        def plot_thresholds(xval, yval, sdscale):
            # compute standard deviation and mean
            df_copy = self.df
            xvalmean, xvalstd = df_copy[xval].mean(), df_copy[xval].std()
            yvalmean, yvalstd = df_copy[yval].mean(), df_copy[yval].std()
            df_copy.loc[:, f"{xval}_meandiff"] = df_copy.apply(
                lambda x: np.fabs(x[xval] - xvalmean), axis=1)
            df_copy.loc[:,
                        f"{xval}_outside"] = (df_copy[f"{xval}_meandiff"] >= xvalstd * sdscale).astype(float)
            df_copy.loc[:, f"{yval}_meandiff"] = df_copy.apply(
                lambda x: np.fabs(x[yval] - yvalmean), axis=1)
            df_copy.loc[:,
                        f"{yval}_outside"] = (df_copy[f"{yval}_meandiff"] >= yvalstd * sdscale).astype(float)
            df_copy.loc[:, f"anomaly_correspondence"] = df_copy[f"{yval}_outside"].astype(
                float) + df_copy[f"{xval}_outside"].astype(float)

            fig = px.scatter(df_copy, x=xval, y=yval, color="anomaly_correspondence", marginal_x="violin",
                             marginal_y="violin")
            # fig.update_yaxes(scaleanchor="x", scaleratio=1)
            fig.update_layout(uirevision=True)

            scatx = px.scatter(df_copy, x=df_copy.index,
                               y=xval, color=f"{xval}_outside")
            scaty = px.scatter(df_copy, x=df_copy.index,
                               y=yval, color=f"{yval}_outside")
            return(fig, scatx, scaty)
        

        @callback(Output("overhead-map", "figure"),
                  Output("3d-map", "figure"),
                  Input("map-selection", "value"),
                  State("bathy-toggle", "value"))
        def plot_maps(vtarg, nclicks):
            """Render the maps on the maps page."""
            # get the bathy underlay
            # if nclicks % 2 == 0:
            #     figs2D = []
            #     figs3D = []
            # else:
            #     bathy = self.get_bathy_data()
            #     figs2d = [px.scatter(bathy, x="lat", y="lon")]
            #     figs3d = [px.scatter3d(bathy, x="lat", y="lon", z="depth")]

            # get the usbl data
            # usbl_df = self.get_usbl_data()
            # df_copy = self.df

            # interpolate together
            # df_copy = df_copy.merge(usbl_df)

            # display
            fig = px.scatter(self.df, x=self.df.index, y=self.df[vtarg])
            return(fig, fig)

        app.run(debug=True)

    def _create_app_layout(self):
        """Creates the overall app layout."""
        layout = html.Div([html.Div([html.Div(dcc.Link(
            f"{page['name']}", href=page["relative_path"])) for page in dash.page_registry.values()]), dash.page_container, ])
        return(layout)

    def _create_timeseries_layout(self):
        """Create the dashboard scene."""
        layout = html.Div([html.H1(children="Sentry Dashboard", style={"textAlign": "center"}),
                           dcc.Graph(id="graph-content-oxygen"),
                           dcc.Graph(id="graph-content-turbidity"),
                           dcc.Graph(id="graph-content-orp"),
                           dcc.Graph(id="graph-content-temperature"),
                           dcc.Graph(id="graph-content-salinity"),
                           dcc.Graph(id="graph-content-depth"),
                           dcc.Interval(id="graph-update", interval=1*1000, n_intervals=0)])
        return(layout)

    def _create_threshold_layout(self):
        """Create the ability to examine thresholds in a dashboard."""
        layout = dbc.Container([dbc.Row([html.Div(children=[html.H1(children="Thresholds Dashboard", style={"textAlign": "center"})]),
                                         html.Div(children=["Select x variable:",
                                                            dcc.Dropdown(self.df.columns.unique(), "Oxygen", id="x-axis-selection")]),
                                         html.Div(children=["Select y variable:",
                                                            dcc.Dropdown(self.df.columns.unique(), "Turbidity", id="y-axis-selection")],
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
                           html.Div(children=[html.Button("Toggle Bathy",
                                                          id="bathy-toggle",
                                                          n_clicks=0,
                                                          style={"align": "center", "width": 100})]),
                           html.Div(children=["Select variable to visualize:",
                                              dcc.Dropdown(self.df.columns.unique(), "Oxygen", id="map-selection")], style={"margin-top": 20}),
                           html.Div(children=[dcc.Graph(id="overhead-map")]),
                           html.Div(children=[dcc.Graph(id="3d-map")])])
        return(layout)

    def get_bathy_data(self):
        """Read in the data from a bathy file, if any."""
        pass
