#!/bin/bash
set -e

echo "Starting the project..."

# Run python as a subprocess of the shell. So that in container, the python process will not be the process with PID 1.
# You can easily kill the python process with kill command (`ps -eaf`) to restart the container.
python3.11 -u src/main.py