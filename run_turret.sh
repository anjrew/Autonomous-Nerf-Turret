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



SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python $SCRIPT_DIR/components/orchestrator/run_turret.py 


