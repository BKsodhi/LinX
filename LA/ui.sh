#!/bin/bash

# Create dialog box to take input
dialog --title "LinX Assistant" \
--inputbox "Enter a Linux command character or task keyword (e.g., 'add user'):" \
8 60 2>temp_input.txt

# Read user input
input=$(<temp_input.txt)
clear

# Run the Python assistant with input
python3 assistant.py "$input"

# Clean up
rm -f temp_input.txt
