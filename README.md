# auv_listener
Simple python scripts for listening to acoustic data packet returns from underwater vehicles.

## Workflow
Prior to launching any script, check that the information in `port_config.yaml` is correct. This file contains some of the basic networking and acoustic queue information that is utilized by scripts in the repository to parse and display messages. This file can also be used to document additional information, such as IP addresses or port numbers, for later reference (although these are typically requested directly in terminal commands).

The `listener.py` utility is the only tool that requires a connection to a local network serving the AUV/USBL or other target data packets (this implies that it must be run ship-side if doing remote operations). This tool logs ALL messages that are passed over UDP on the network by running:

```python listener.py -i 127.0.0.1 -p 100 -f ./ -n dive614 -v```

where the the IP address (`-i`) and port (`-p`) are used to indicate the network address to listen to, and a filepath and filename are specified (`-f`, `-n`)for where you would like those messages logged (in this example, it will be in the running directory in a script called `raw_dive614.txt`). All messages recieved over the port can be optionally printed to the executing terminal for monitoring using `-v`. For remote operations, the filepath and filename that the logs are written could be on a synced server which can be polled from shore.

With `listener.py` running, for parsing and visualizing data, a `filter` and `plotter` are necessary. In this repo, we provide specific examples `usbl_filter.py`, `sentry_filter.py`, and `sentry_plotter.py` which can parse USBL mesages, and parse and plot messages from AUV Sentry. Both of the `_filter.py` utilities will read in a pointer to a raw UDP listener log file, and sort messages into new log files under different queue names (e.g., *science*, *status*, *ship*, *jason*, and so on). The USBL filter seperates location information between different ID objects (like SENTRY, JASON, the ship, a CTD Rosette) and the SENTRY filter seperates based on type of queue message. To run a filter, the following form can be used:

```python sentry_filter.py -t ./raw_dive614.txt -f ./ -n dive614```

which would read in data written to `raw_dive614.txt` and save parsed data to `./proc_dive614_science.txt` and `./proc_dive614_status.txt`. The equivalent format can be used for the `usbl_filter`.

The new files created by the filter utilities can then be visualized by either a rudimentary `plotter` utility, or a more feature rich `dashboard` utility. For the simple plotting features, we provide a `sentry_plotter.py` which reads in different queue targets and displays time plots which can be updated live if the listener, filter, and plotter are all simultaneously running. The plots have a simple "zoom" feature which can be used to look more closely at a subset of the most recent data messages. The plotter is primarily written to display `matplotlib` graphs. To run the plotter, use:

```python sentry_plotter.py -t ./proc_dive614_science.txt -x 0 -y 1,2,3,4,5,6 -n O2,OBS,ORP,Temperature,Salinity,Depth -s```

which will create a plot with 6 subplots with a shared time axis. The time axis is targeted with `-x`, and the data columns to plot against time are indicated by `-y`. The names of the data plots are indicated with `-n` and `-s` is a flag to render all data points as a scatter plot (as opposed to a connected line plot).

To run the more feature rich dashboard, which provides a fully interactive set of html webpages on `127.0.0.1:8050`, the following command can be run:

```python sentry_dashboard.py -t ./data/sentry/proc_dive_{divenum}_science.txt -b path/to/bathy/file```

This command points to the science data and a local bathy file. This is the minimum set of commands needed to launch a dashboard, and will show simple time-based streaming. For more detailed renderings, the following functionality is provided:

```python sentry_dashboard.py -t ./data/sentry/proc_dive_{divenum}_science.txt -x ./data/sentry/proc_dive_{divenum}_experimental.txt -u ./data/usbl/proc_usbl_{divenum}_usbl_sentry.txt -b path/to/bathy/file -m ./data/sentry/proc_dive_{divenum}_mets.txt -o ./data/sentry/proc_dive_{divenum}_obs.txt -c path/to/currents/file -k Turbidity,ORP,methane_ppm,Depth,spiciness,potential_density,Temperature,Salinity,Oxygen,dORPdt,dORPdt_log -n 9```

which adds "experimental" sensors (like SAGE methane sensor or other custom-defined sensor), usbl data, mets data, auxiliary optical backscatter data, external currents data, and lists the exact names of the data objects to render, and how many to render on the "home page" of the dashboard.

Examples of how to run all utilities in a terminal are provided at the top of each script. Additionally, a convience bash script, `run_watchstation.sh` has been provided which can be modified to run all the necessary commands to launch a full listening, filtering, and plotting mission.

To test the workflow, a `spoofer.py` is provided which can generate or read out messages of the right format for the SENTRY or USBL services. To run the spoofer, simply use:

```python spoofer.py -i 127.0.0.1 -p 100 -r 20```

which will publish random messages every 20 seconds at the address 127.0.0.1 on port 100. The spoofer can additionally accept saved data structures to "replay", to provide a list of messages you would like the spoofer to read, use:

```python spoofer.py -i 127.0.0.1 -p 100 -f ./messages_to_spoof.txt -r 20```.

## Running a Spoofed Instance
In seperate terminals, run a spoofer for both science data and usbl data, a listener for both science and usbl data, a filter for both science and usbl data, and either a plotter or dashboard. The default spoofer, listener, and filter commands should create reasonable targets that can then be passed to a plotter or dashboard. 

## Running on a Mission
To run on a real mission while connected to the Sentry network, you will not run your `spoofer`. With your `listener`, you will also need to set the network IP address (it will *not* be 127.0.0.1) and port to listen to. Depending on the acoustic queues or message IDs you want to use, small edits may need to be made in the `filter` and `plotter` utilities provided here. Otherwise, the workflow will be the same as in the case of a spoofed instance.

## Troubleshooting
If a plot is not being generated or updated, common problems are:
- the chain of file reading is not correct; double check the file target names you are using at each stage of the scripts
- connection to the network has been lost; check your network connection and with the engineering teams to confirm
- there is no data being published over the queues you are listening to; check with engineering teams to confirm
- an unhandled exception has been caught by the filter you are using; check that terminal for error messages and restart if necessary

## Dependencies
These tools are written in Python 3.5+ and have been tested on Ubuntu 18.04 and 22.04 operating systems. Python 3.7+ is recommended. Libraries necessary are:
* socket
* argparse
* datetime
* pandas
* numpy
* matplotlib
* yaml
* bagpy

An exhaustive list of requirements is noted in the `requirements.txt` file in the repo home directory.

A `pipenv` environment has been provided for convenience. To run the environment, install the latest pipenv in a terminal (e.g., `pip install pipenv`). Within the repository, install the pipenv environment with `pipenv install`. To then utilize the environment, you can run `pipenv shell`. Necessary dependencies can then be install by running `pip install -r requirements.txt` within the pipenv environment. 

## Known Limitations
Currently, this repository represents a very Sentry and sensor-specific approach to filtering and displaying data (the listening is largely agnostic of platform). New filters may need to be designed for other mission scenarios; examples in `usbl_filter.py`, `sentry_filter.py`, and `filter_utils.py` can serve as a template for extending this work.

For visualization, particularly the dashboard, the interface is heavily influenced by work performed at the Juan de Fuca Ridge during cruise AT50-15, including how methane data from multiple instruments, additional optical backscatter sensor, and external current data for co-located moorings, are included as options. As these are all optional inputs, adding new sensors can be done by copying the protocols used to include these sensors. Presently, some visualized features (like special mission targets like vents, moorings, or other points of interest) are hardcoded into the dashboard visualizer. Moving these to optional inputs is recommended for consistent use.

Some science features, like "spice" and "potential density," are only approximations computed from the data that can be transmitted via the scalar science queue circa August 2023. These should not be interpretted as true values, however their overall patterns are realistic. If observations, such as CTD conductivity, were transmitted, these values could be directly computed live and the functions that compute these values can be updated to reflect these changes. 

## Contact
For questions or comments on this work, please contact Victoria Preston (vpreston). An MIT license is applied to this work.
