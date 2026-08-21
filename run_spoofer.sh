#!/bin/bash
# Runs a specifed set of python commands to set up Sentry science watchstanding
# Modify the top variables to set up repo/etc. properly

SENTRY_LOG_NAME='test_dive_1'  # the name you would like to append to all Sentry data logs, recommended: dive_###
USBL_LOG_NAME='test_usbl_1'  # the name you would like to append to all USBL data logs, recommended: usbl_###
BATHY_FILE='./data/axial.xyz'  # a file of bathymetry for displaying; required

VENT_FILE='./data/CASM_ventsite.txt'  # set to "None" if no vent locations to plot
EQUIPMENT_FILE='None'  # set to "None" if no equipment locations to plot
CURRENT_FILE='None'  # set to "None" is no additional current data to plot

SAGE_SENSOR='False'  # set to True if there is a SAGE sensor onboard
METS_SENSOR='False'  # set to True if there is a METS sensor onboard
OBS_SENSOR='False'  # set to Trye if there is an extra OBS sensor onboard

IP_ADDRESS='127.0.0.1'  # this is your network address (likely formatted as 192.168.X.X)
SENTRY_PORT='1234'  # this is the port over the network publishing Sentry SDQ messages
USBL_PORT='2345'  # this is the port over the network publishing USBL messages

SENTRY_SAVE_TARGET='./'  # where to save your processed Sentry messages
USBL_SAVE_TARGET='./'  # where to save your processed USBL messages

KEYS='Turbidity,ORP,Depth,Temperature,Salinity,Oxygen,dORPdt_log'  # dataset keys for dashboard
# Available keys are Oxygen, Turbidity, ORP, Temperature, Salinity, Depth, dORPdt, dORPdt_log, spice, potential_density
# If SAGE: methane_ppm, and specialized engineering data
# If METS: methane_mets, and specialized engineering data
# If extra OBS: turbidity_obs_5x, and specialized engineering data
# If Current data: true_veast, true_vnorth, and other data
NUM_TO_DISPLAY=6  # the first N elements of KEYS for streaming display on the home page

##########
# Parse Variables
##########
if [ ${SAGE_SENSOR} == 'True' ]; then
    X_TARGET=${SENTRY_SAVE_TARGET}/proc_${SENTRY_LOG_NAME}_experimental.txt
else
    X_TARGET='None'
fi

if [ ${METS_SENSOR} == 'True' ]; then
    METS_TARGET=${SENTRY_SAVE_TARGET}/proc_${SENTRY_LOG_NAME}_mets.txt
else
    METS_TARGET='None'
fi

if [ ${OBS_SENSOR} == 'True' ]; then
    OBS_TARGET=${SENTRY_SAVE_TARGET}/proc_${SENTRY_LOG_NAME}_obs.txt
else
    OBS_TARGET='None'
fi


##########
# Execution Code
##########
read -p "Wait! Did you change the log names and bathy target? If not, press Ctrl+C to cancel and fix. Else press Enter."
read -p "Press enter to start the spoofer messages"
python spoofer.py -i $IP_ADDRESS -p $SENTRY_PORT -r 2 &
python usbl_spoofer.py -i $IP_ADDRESS -p $USBL_PORT -r 2 &
read -p "Press Enter to start listening over the network."
python listener.py -i $IP_ADDRESS -p $SENTRY_PORT -f $SENTRY_SAVE_TARGET -n $SENTRY_LOG_NAME &
python listener.py -i $IP_ADDRESS -p $USBL_PORT -f $USBL_SAVE_TARGET -n $USBL_LOG_NAME &
read -p "Now listening...After a few minutes, press Enter to start filters and dashboard."
python sentry_filter.py -t ${SENTRY_SAVE_TARGET}/raw_${SENTRY_LOG_NAME}.txt -f $SENTRY_SAVE_TARGET -n proc_${SENTRY_LOG_NAME} &
python usbl_filter.py -t ${USBL_SAVE_TARGET}/raw_${USBL_LOG_NAME}.txt -f ${USBL_SAVE_TARGET} -n proc_${USBL_LOG_NAME} &
python sentry_dashboard.py -t ${SENTRY_SAVE_TARGET}/proc_${SENTRY_LOG_NAME}_science.txt \
                           -x ${X_TARGET} \
                           -m ${METS_TARGET} \
                           -o ${OBS_TARGET} \
                           -c ${CURRENT_FILE} \
                           -u ${USBL_SAVE_TARGET}/proc_${USBL_LOG_NAME}_sentry.txt \
                           -v ${VENT_FILE} \
                           -e ${EQUIPMENT_FILE} \
                           -b ${BATHY_FILE} \
                           -k ${KEYS} \
                           -n ${NUM_TO_DISPLAY}

