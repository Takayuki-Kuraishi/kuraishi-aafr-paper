#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Usage: process_data.sh <input_csv_dir> [output_dir]
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 <input_csv_dir> [output_dir]"
    exit 1
fi

INPUT_DIR=$1
OUTPUT_DIR=${2:-"${INPUT_DIR%/}_distance"}

if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory ${INPUT_DIR} does not exist."
    exit 1
fi

echo "Processing tracking CSV files..."
echo "  Input : ${INPUT_DIR}"
echo "  Output: ${OUTPUT_DIR}"
python3 "${SCRIPT_DIR}/process_csv.py" "$INPUT_DIR" "$OUTPUT_DIR"

echo "Analyzing processed CSV files with countrow_csv.py..."
python3 "${SCRIPT_DIR}/countrow_csv.py" "$OUTPUT_DIR"

echo "All processing completed!"
