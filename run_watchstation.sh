#!/bin/bash
# Runs a specifed set of python commands to set up Sentry science watchstanding
# Modify the top variables to set up repo/etc. properly

SENTRY_LOG_NAME='dive_686'
USBL_LOG_NAME='usbl_686'
BATHY_FILE='./AT50-15/bathy_files/dive_686.txt'

IP_ADDRESS='192.168.100.226'
# IP_ADDRESS='127.0.0.1'
SENTRY_PORT='52466'
USBL_PORT='52467'
SENTRY_SAVE_TARGET='./AT50-15/sentry_data'
USBL_SAVE_TARGET='./AT50-15/usbl_data'

read -p "Wait! Did you change the log names and bathy target?"
python listener.py -i $IP_ADDRESS -p $SENTRY_PORT -f $SENTRY_SAVE_TARGET -n $SENTRY_LOG_NAME &
python listener.py -i $IP_ADDRESS -p $USBL_PORT -f $USBL_SAVE_TARGET -n $USBL_LOG_NAME &
read -p "Press to start filters and dashboard (recommend waiting for a few minutes)"
python sentry_filter.py -t ${SENTRY_SAVE_TARGET}/raw_${SENTRY_LOG_NAME}.txt -f $SENTRY_SAVE_TARGET -n proc_${SENTRY_LOG_NAME} &
python usbl_filter.py -t ${USBL_SAVE_TARGET}/raw_${USBL_LOG_NAME}.txt -f ${USBL_SAVE_TARGET} -n proc_${USBL_LOG_NAME} &
python sentry_dashboard.py -t ${SENTRY_SAVE_TARGET}/proc_${SENTRY_LOG_NAME}_science.txt -x ${SENTRY_SAVE_TARGET}/proc_${SENTRY_LOG_NAME}_experimental.txt -u ${USBL_SAVE_TARGET}/proc_${USBL_LOG_NAME}_sentry.txt -b ${BATHY_FILE}
# python sentry_dashboard.py -t ${SENTRY_SAVE_TARGET}/proc_${SENTRY_LOG_NAME}_science.txt -x None -u ${USBL_SAVE_TARGET}/proc_${USBL_LOG_NAME}_sentry.txt -b ${BATHY_FILE}

