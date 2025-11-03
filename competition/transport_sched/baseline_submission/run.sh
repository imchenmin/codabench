#!/bin/bash

# Transport Scheduling Baseline Submission
# This script serves as an alternative entry point for the baseline submission

# Check if the required arguments are provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <input_directory> <output_file>"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_FILE="$2"

# Run the Python baseline submission
python3 run.py --input "$INPUT_DIR" --output "$OUTPUT_FILE"