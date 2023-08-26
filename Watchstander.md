# README for Operating Science Watch Stand

The dashboard in this repository is meant to assist with listening to and visualizing acoustic messages transmitted from AUV Sentry (i.e., the science queue) and from the USBL system. Functionality includes: 
- listening to sentry-network UDP ports and logging data to file
- parsing UDP messages into sentry status, sentry science, sentry experimental sensor, and usbl files
- simple time-series streaming (live updates) of Sentry sensors and select experimental sensors
- basic analysis of time-series data (property vs. property plots and distributions, outlier identification)
- spatial plotting over bathymetry of Sentry sensors and select experimental sensors


To run the dashboard locally (i.e., not on the "watchstander computer") you will need to do the following:
1. Make sure that `python` is installed; 3.7 or higher is recommended.
2. Install `pipenv` in your terminal (e.g., `pip install pipenv`), which is a virtual environment library that can be used to run the repository.
3. Clone the online git repository (ask Victoria for access to repo) or ask Victoria for copy of the source.
4. Install the `pipenv` environment with `pipenv install` in the home directory
5. Enter into the pipenv environment with `pipenv shell`.
6. Install the necessary dependencies by running `pip install -r requirements.txt`
7. Connect to the Sentry network, and make sure queue numbers and ports are correct per Sentry team configuration


On either the watchstander computer or your own computer, the workflow to initialize will be:
1. Enter into the pipenv environment with `pipenv shell` from the home directory of the repository
2. Start the Sentry listener
3. Start the USBL listener
4. Start the Sentry message filter
5. Start the USBL message filter
6. Start the dashboard

Details below will explain each of these steps and common troubleshooting. At the end of the watch, kill all tabs with `Ctrl + C` in each terminal. You can kill everything but the dashboard if you would like to leave the data up for looking over. If you kill the dashboard, you can always get back the last session by relaunching the script.


# Sentry and USBL Listener
The `listener.py` file defines a tool that will listen to a given UDP address and port, and log all of the messages received to a file. You can use the same code to listen to either the sentry or usbl messages as these two types of messages live on seperate ports. To run, you can type the following into the `pipenv shell` environment:

`python listener.py -i 127.0.0.1 -p 23344 -f ./ -n dive_default -v`

where `i` indicates the IP network address over which the messages are transmitted, `p` indicates the port to listen to, `f` asks for a filepath to store the logged data, `n` is the name that you want the data to be listed under, and `v` indicates whether you want to print everything received to terminal (helpful for debugging). In the above, a listener is created over the 127.0.0.1 network for port 23344. The file will be written from the directory the code is executed and called "dive_default.txt". All messages recieved will be printed to the terminal.

When executing for watch, it will be helpful to distinguish between listening to Sentry and listening to the USBL. Please run the following in two separate terminals:

`python listener.py -i 127.0.0.1 -p 23344 -f ./data/sentry -n dive_{divenum} -v`

`python listener.py -i 127.0.0.1 -p 25644 -f ./data/usbl -n usbl_{divenum} -v`

replacing the network and ports with the correct information provided by the Sentry team. Two files will be created in data folder.

# Sentry and USBL Filter
While messages are being logged, you can filter their contents to extract useful information that you may want to plot while at sea. These include:
- Sentry science queue (temperature, salinity, O2, turbidity, ORP, depth)
- Sentry experimental sensor queue (methane, sensor status)
- USBL fixes for different assets (e.g., Sentry, CTD, Ship)

The `sentry_filter.py` and `usbl_filter.py` utilities define these filters. When standing watch, please run, in two separate terminals:

`python sentry_filter.py -t ./data/sentry/raw_dive_{divenum}.txt -f ./data/sentry -n proc_dive_{divenum}`

`python usbl_filter.py -t ./data/usbl/raw_usbl_{divenum}.txt -f ./data/usbl -n proc_usbl_{divenum}`

The `sentry_filter` utility can create up to three new files called `proc_dive_{divenum}_status`, `proc_dive_{divenum}_science`, and `proc_dive_{divenum}_experimental`. The `usbl_filter` utility can create up to three new files as well, called `proc_usbl_{divenum}_ship`, `proc_usbl_{divenum}_sentry`, `proc_usbl_{divenum}_rosette`.


# Sentry Dashboard
Finally, you can visualize the data by running the data dashboard using the following command:

`python sentry_dashboard.py -t ./data/sentry/proc_dive_{divenum}_science.txt -x ./data/sentry/proc_dive_{divenum}_experimental.txt -u ./data/usbl/proc_usbl_{divenum}_usbl_sentry.txt -b path/to/bathy/file`

This points to the science data, experimental sensor data (if any), usbl data (if any), and a local bathy file for a mission on the computer. 

To then see the dashboard, navigate to a browser (you *do not need to be connected to the internet, just the Sentry network*) and open `127.0.0.1:8050`. You should see the dashboard, and if in continuous mode, the home page should contain occasionally-updating timeseries data of all the sensors. 

# Troubleshooting

## Plot not updating
Remember -- Sentry sends updates very occasionally, so it may be several minutes (up to 5) before you might see a change in the liveplots. You can check to make sure everything is functioning by watching a verbose listener terminal or verifying with the Sentry team that the queues have been "switched on" for broadcasting. You can also check to make sure that the raw and filtered messages are being generated in the `data` folder, and that you have correctly pointed to those files in your command. 

## No data received over UDP
If you cannot seem to get any messages, check that you are connected to the Sentry network and can ping yourself or another computer on the network (in the terminal, `ping [IP ADDRESS]`). 

If you are connected to the network, check that you have provided the correct ports to the functions (check with the Sentry team). 

If that seems right and you are getting raw messages, but not filtered ones, check that the queue numbers (defined in `port_config.yaml`) are correct for the science, status, and experimental sensor queues. You can confirm these with the Sentry team.

## Data labels and actual data appear mis-aligned
It may be the case that this in-development code made an error in parsing a given UDP message (for instance, switching the lat and the lon positions in the USBL messages). If you can diagnose what has been switched around, please consider updating the code in `plotter_utils.py` in the `Sentry_Dashboard` class, as well as any of the appropriate filter messages in `filter_utils.py` or `udp_utils.py`. 

