"""Utilities file for making plotters.

Authors: Genevieve Flaspohler and Victoria Preston
Update: August 2022
Contact: {geflaspo, vpreston}@mit.edu
"""

import os
import time
import pandas as pd

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
