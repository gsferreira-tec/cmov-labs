#!/usr/bin/bash

if [ "$EUID" -eq 0 ]; then
    echo "Do not run this script as root."
    exit 1
fi

# For this script we will need to do a per study number case check because the arguments are not the same for every study...
STUDY_NO=$1

if [ $# -lt 1 ]; then
    echo "You need to provide the necessary arguments for the run."
    echo
    echo "Usage: $0 <study-number> <min-distance> <max-distance> <step> <duration> <nr_of_senders[2]/data_rate[3]>"
    exit 1
fi

LOG_DIR="/home/mobile/Share"
NS3_EXE_PATH="/home/mobile/ns-3.47/ns3"

# changing directories to where the command is meant to be run...
# cd $NS3_EXE_PATH
#
# { echo "Cannot enter ns-3 directory"; exit 1; }
#
# if [ ! -x ./ns3 ]; then
#     echo "Error: ./ns3 not found or not executable in $(pwd)"
#     exit 1
# fi

case "$STUDY_NO" in
    1|one|first|4|four|fourth)
    if [ $# -ne 5 ]; then
        echo "Usage: $0 <study-number> <min-distance> <max-distance> <step> <duration>"
        exit 1
    fi

    MIN_DIST=$2
    MAX_DIST=$3
    STEP=$4
    DUR=$5

    if [ "$STUDY_NO" == "1" ] || [ "$STUDY_NO" == "first" ] || [ "$STUDY_NO" == "one" ]; then
        STUDY_ID="first_study"
    elif [ "$STUDY_NO" == "4" ] || [ "$STUDY_NO" == "fourth" ] || [ "$STUDY_NO" == "four" ]; then
        STUDY_ID="fourth_study"
    else
        echo "The study number provided is not available. Aborting..."
        sleep 1
        exit 1
    fi

    # ------------- sanity checks on numeric values -------------------
    if ! [[ $MIN_DIST =~ ^[0-9]+$ && $MAX_DIST =~ ^[0-9]+$ && $STEP =~ ^[0-9]+$ && $DUR =~ ^[0-9]+$ ]]; then
        echo "All arguments except the optional step must be integers."
        sleep 1
        exit 1
    fi

    if (( MIN_DIST > MAX_DIST )); then
        echo "Error: min_dist ($MIN_DIST) is greater than max_dist ($MAX_DIST). Aborting..."
        sleep 1
        exit 1
    fi
    # -----------------------------------------------------------------
    sleep 1
    echo
    echo "Running the 1st study from ${MIN_DIST} to ${MAX_DIST}. This may take a while..."
    echo
    LOG_FILE="${LOG_DIR}/sim${STUDY_NO}.log"
    : > "$LOG_FILE"
    for dist in $(seq "$MIN_DIST" "$STEP" "$MAX_DIST"); do
        echo
        echo "Executing : ./ns3 run \"scratch/${STUDY_ID} --distance=${dist} --duration=${DUR}\""
        echo
        "$NS3_EXE_PATH" run "scratch/${STUDY_ID} --distance=${dist} --duration=${DUR}" >> "$LOG_FILE" 2>&1
    done
    ;;
    2|two|second)
    if [ $# -ne 4 ]; then
        echo "Usage: $0 <study-number> <duration> <init-nr-senders> <final-nr-sender>"
        exit 1
    fi

    STUDY_NO=$1
    DUR=$2
    INIT_SENDER_NO=$3
    FINAL_SENDER_NO=$4
    STEP=1 # this is default

    echo
    echo "Running the 2nd study from ${INIT_SENDER_NO} senders to ${FINAL_SENDER_NO} senders. This may take a while..."
    echo
    LOG_FILE="${LOG_DIR}/sim${STUDY_NO}.log"
    : > "$LOG_FILE"
    for send_nr in $(seq "$INIT_SENDER_NO" "$STEP" "$FINAL_SENDER_NO"); do
        echo
        echo "Executing : ./ns3 run \"scratch/second_study --nr_of_senders=${send_nr} --duration=${DUR}\""
        echo
        "$NS3_EXE_PATH" run "scratch/second_study --nr_of_senders=${send_nr} --duration=${DUR}" >> "$LOG_FILE" 2>&1
    done
    ;;
    3|three|third)
    if [ $# -ne 4 ]; then
        echo "Usage: $0 <study-number> <duration> <min_data_rate> <max_data_rate>"
        exit 1
    fi

    DUR=$2
    MIN_DATA_RATE=$3
    MAX_DATA_RATE=$4
    STEP=1 # fault increase is at 1Mbps per iteration

    sleep 1
    echo
    echo "Running the 3rd study from ${MIN_DATA_RATE} to ${MAX_DATA_RATE}. This may take a while..."
    echo
    LOG_FILE="${LOG_DIR}/sim${STUDY_NO}.log"
    : > "$LOG_FILE"
    for datarate in $(seq "$MIN_DATA_RATE" "$STEP" "$MAX_DATA_RATE"); do
        echo
        echo "Executing : ./ns3 run \"scratch/third_study --udp_data_rate=${datarate}Mbps --duration=${DUR}\""
        echo
        "$NS3_EXE_PATH" run "scratch/third_study --udp_data_rate=${datarate}Mbps --duration=${DUR}" >>  "$LOG_FILE" 2>&1
        sleep 1
    done
    ;;
    "") # for when the user might press enter duiring operation so that nothing happens
    ;;
    *)
        echo "Usage: $0 <study-number> <min-distance> <max-distance> <step> <duration> <nr_of_senders[2]/data_rate[3]>"
        sleep 1
        exit 1
    ;;
esac

echo
sleep 1
echo "Simulation study number ${STUDY_NO} has finished. Exiting..."
