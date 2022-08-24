# auv_listener
Simple python scripts for listening to acoustic data packet returns from underwater vehicles.

## Workflow
The `listener.py` utility is the only tool that requires a connection to a local network serving the AUV/USBL or other target data packets (this implies that it must be run ship-side if doing remote operations). This tool logs ALL messages that are passed over UDP on the network by running:

```python listener.py -i 127.0.0.1 -p 100 -f ./ -n dive614 -v```

where the the IP address (`-i`) and port (`-p`) are used to indicate the network address to listen to, and a filepath and filename are specified (`-f`, `-n`)for where you would like those messages logged (in this example, it will be in the running directory in a script called `raw_dive614.txt`). All messages recieved over the port can be optionally printed to the executing terminal for monitoring using `-v`. For remote operations, the filepath and filename that the logs are written could be on a synced server which can be polled from shore.

With `listener.py` running, for parsing and visualizing data, a `filter` and `plotter` are necessary. In this repo, we provide specific examples `usbl_filter.py`, `sentry_filter.py`, and `sentry_plotter.py` which can parse USBL mesages, and parse and plot messages from AUV Sentry. Both of the `_filter.py` utilities will read in a pointer to a raw UDP listener log file, and sort messages into new log files under different queue names (e.g., *science*, *status*, *ship*, *jason*, and so on). The USBL filter seperates location information between different ID objects (like SENTRY, JASON, the ship, a CTD Rosette) and the SENTRY filter seperates based on type of queue message. To run a filter, the following form can be used:

```python sentry_filter.py -t ./raw_dive614.txt -f ./ -n dive614```

which would read in data written to `raw_dive614.txt` and save parsed data to `./proc_dive614_science.txt` and `./proc_dive614_status.txt`. The equivalent format can be used for the `usbl_filter`.

The new files created by the filter utilities can then be visualized by a `plotter`. Here, we provide a `sentry_plotter.py` which reads in different queue targets and displays either time or spatial plots which can be updated live if the listener, filter, and plotter are all simultaneously running. The plots have a rudimentary "zoom" feature which can be used to look more closely at a subset of the most recent data messages. To run the plotter, use:

```python sentry_plotter.py -t ./proc_dive614_science.txt -x 0 -y 1,2,3,4,5,6 -n O2,OBS,ORP,Temperature,Salinity,Depth -s```

which will create a plot with 6 subplots with a shared time axis. The time axis is targeted with `-x`, and the data columns to plot against time are indicated by `-y`. The names of the data plots are indicated with `-n` and `-s` is a flag to render all data points as a scatter plot (as opposed to a connected line plot).

Examples of how to run all utilities in a terminal are provided at the top of each script.

To test the workflow, a `spoofer.py` is provided which can generate or read out messages of the right format for the SENTRY or USBL services. To run the spoofer, simply use:

```python spoofer.py -i 127.0.0.1 -p 100 -r 20```

which will publish random messages every 20 seconds at the address 127.0.0.1 on port 100. The spoofer can additionally accept saved data structures to "replay", to provide a list of messages you would like the spoofer to read, use:

```python spoofer.py -i 127.0.0.1 -p 100 -f ./messages_to_spoof.txt -r 20```.

## Running a Spoofed Instance
In seperate terminals, run the following:
```python spoofer.py```
```python listener.py```
```python sentry_filter.py```
```python sentry_plotter.py```

This is the simplest working example, and should result in an updating plot. You may configure these commands as you see fit to test filters, plotters, or other configurations.

## Running on a Network
To run on a network, you will not run your `spoofer`. With your `listener`, you will also need to set the network IP address (it will *not* be 127.0.0.1) and port to listen to. Depending on the acoustic queues or message IDs you want to use, small edits may need to be made in the `filter` and `plotter` utilities provided here. Otherwise, the workflow will be the same as in the case of a spoofed instance.

## Troubleshooting
If a plot is not being generated or updated, common problems are:
- the chain of file reading is not correct; double check the file target names you are using at each stage of the scripts
- connection to the network has been lost; check your network connection and with the engineering teams to confirm
- there is no data being published over the queues you are listening to; check with engineering teams to confirm
- an unhandled exception has been caught by the filter you are using; check that terminal for error messages and restart if necessary

## Dependencies
These tools are written in Python 3.5+ and have been tested on an Ubuntu 18.04 operating system. Libraries necessary are:
* socket
* argparse
* datetime
* pandas
* numpy
* matplotlib
* yaml
* bagpy

## Contact
For questions or comments on this work, please contact Victoria Preston (vpreston) or Genevieve Flaspohler (geflaspohler). An MIT license is applied to this work.
