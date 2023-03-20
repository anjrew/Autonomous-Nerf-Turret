#!/bin/bash

# Define the function that will be executed when Control+C is pressed
handle_ctrl_c() {
    echo "Killing process"
    pids=$(ps aux | grep '[p]ython' | grep Autonomous-Nerf-Turret | awk '{print $2}')

    for pid in $pids; do
    echo "Killing process ID: $pid"
    kill "$pid"
    done
    exit 1
}

# Set up the trap to catch SIGINT (Control+C) and call the handle_ctrl_c function
trap handle_ctrl_c SIGINT

logging="INFO"

# Parse the options
while getopts ":ll:b:" opt; do
  case $opt in
    a)
      logging="$OPTARG"
      ;;
    # b)
    #   arg2="$OPTARG"
    #   ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python $SCRIPT_DIR/components/orchestrator/run_turret.py --log-level $logging


