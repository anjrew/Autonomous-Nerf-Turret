#!/bin/bash

# Define the function that will be executed when Control+C is pressed
handle_ctrl_c() {
    echo "Killing process"
    pids=$(ps aux | grep '[p]ython' | grep Autonomous-Nerf-Turret | awk '{print $2}')

    for pid in $pids; do
    echo "Killing process ID: $pid"
    kill -s SIGKILL "$pid"
    done
    exit 1
}

# Set up the trap to catch SIGINT (Control+C) and call the handle_ctrl_c function
trap handle_ctrl_c SIGINT

logging="INFO"

while getopts "l:" opt; do
  echo $opt
  case $opt in
    l) logging=$OPTARG;;
    \?)
      echo "Invalid option: -$OPTARG"
      ;;
    :)
      echo "Option -$OPTARG requires an argument."
      ;;
  esac
done

if [[ ! -z "$logging" ]]; then
  echo "The value of -l is: $logging"
else
  echo "No -ll option provided."
fi



SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$SCRIPT_DIR/components/orchestrator/run_turret.py --log-level $logging"
echo "Running python script: $SCRIPT"
python $SCRIPT



