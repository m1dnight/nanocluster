#!/bin/bash

# Script to create a tmux session with panes connected to all nanocluster hosts

SESSION_NAME="nanocluster"
HOSTS=(
    "woz.localdomain"
    "haskell.localdomain"
    "joe.localdomain"
    "robert.localdomain"
    "mike.localdomain"
    "jose.localdomain"
    "agner.localdomain"
)
USER="pi"

# Check if tmux session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Session '$SESSION_NAME' already exists. Attaching..."
    tmux attach-session -t "$SESSION_NAME"
    exit 0
fi

# Create new tmux session with first host
echo "Creating tmux session '$SESSION_NAME'..."
tmux new-session -d -s "$SESSION_NAME" -n "cluster" "ssh ${USER}@${HOSTS[0]}"

# Add additional panes for remaining hosts
for i in "${!HOSTS[@]}"; do
    if [ $i -gt 0 ]; then
        tmux split-window -t "$SESSION_NAME:cluster" "ssh ${USER}@${HOSTS[$i]}"
        tmux select-layout -t "$SESSION_NAME:cluster" tiled
    fi
done

# Set synchronize-panes on (optional - allows typing to all panes at once)
tmux set-window-option -t "$SESSION_NAME:cluster" synchronize-panes on

# Attach to the session
tmux attach-session -t "$SESSION_NAME"