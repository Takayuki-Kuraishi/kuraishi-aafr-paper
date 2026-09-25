#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Function to print section header
print_header() {
    echo "================================================================"
    echo "  $1"
    echo "================================================================"
}

# Function to print progress
print_progress() {
    echo "-> $1"
}

# Check if at least one argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <folder_pattern1> [folder_pattern2 ...]"
    echo "Examples:"
    echo "  $0 test_data*"
    echo "  $0 folder1 folder2 folder3"
    echo "  $0 experiment_*/data"
    exit 1
fi

# Function to process a single folder
process_folder() {
    local FOLDER_NAME=$1
    local TOTAL_FOLDERS=$2
    local FOLDER_INDEX=$3
    
    # Verify if it's a directory
    if [ ! -d "$FOLDER_NAME" ]; then
        echo "Warning: '$FOLDER_NAME' is not a directory. Skipping..."
        return 1
    fi
    
    TOTAL_STEPS=4
    CURRENT_STEP=0
    
    print_header "Processing Folder ${FOLDER_INDEX}/${TOTAL_FOLDERS}: ${FOLDER_NAME}"
    print_progress "Target folder: ${FOLDER_NAME}"
    print_progress "Total steps to execute: ${TOTAL_STEPS}"
    echo ""
    
    # Function to replace folder names in Python scripts
    replace_folder_name() {
        local script=$1
        local description=$2
        local temp_script="temp_${FOLDER_INDEX}_${script}"
        
        # Update progress
        CURRENT_STEP=$((CURRENT_STEP + 1))
        print_header "Step ${CURRENT_STEP}/${TOTAL_STEPS}: ${description}"
        
        # Create temporary file with replaced folder name
        print_progress "Creating modified version of ${script}..."
        python3 -c 'import sys; from pathlib import Path; src=Path(sys.argv[1]).read_text(); Path(sys.argv[2]).write_text(src.replace("your_folder_name", sys.argv[3]))' "${SCRIPT_DIR}/${script}" "$temp_script" "$FOLDER_NAME"
        
        # Run the modified script and always clean up the temporary file
        print_progress "Executing ${script}..."
        if python3 "$temp_script"; then
            print_progress "Cleaning up temporary files..."
            rm -f "$temp_script"
        else
            status=$?
            print_progress "Cleaning up temporary files..."
            rm -f "$temp_script"
            return "$status"
        fi

        echo "Step ${CURRENT_STEP} completed successfully!"
        echo ""
    }
    
    # Run scripts in sequence
    replace_folder_name "1_RGB_to_B_2401218.py" "RGB to Blue Channel Conversion"
    replace_folder_name "2_subtract_byAveImage_240416_1.py" "Background Subtraction"
    replace_folder_name "3_thresholding_2401218.py" "Image Thresholding"
    replace_folder_name "4_difference_240416_1.py" "Brightness Difference Calculation"
    
    print_header "Analysis Pipeline Completed for ${FOLDER_NAME}"
    print_progress "All ${TOTAL_STEPS} steps have been executed successfully"
    print_progress "Results are saved in the respective output directories"
    echo ""
}

# Expand all arguments to handle wildcards
expanded_folders=()
for pattern in "$@"; do
    # Use compgen to expand wildcards
    if [[ $pattern == *\** ]]; then
        while IFS= read -r folder; do
            expanded_folders+=("$folder")
        done < <(compgen -G "$pattern")
    else
        expanded_folders+=("$pattern")
    fi
done

# Get total number of folders to process
TOTAL_FOLDERS=${#expanded_folders[@]}

if [ $TOTAL_FOLDERS -eq 0 ]; then
    echo "Error: No matching folders found"
    exit 1
fi

print_header "Starting Analysis Pipeline"
print_progress "Total folders to process: ${TOTAL_FOLDERS}"
echo ""

# Process each folder
for ((i=0; i<${TOTAL_FOLDERS}; i++)); do
    FOLDER_INDEX=$((i + 1))
    process_folder "${expanded_folders[$i]}" "$TOTAL_FOLDERS" "$FOLDER_INDEX"
done

print_header "Complete Analysis Pipeline Finished"
print_progress "Outputs were left next to their corresponding input folders."
print_progress "No automatic file organization was performed."

# Automatic cleanup is intentionally disabled.
# Input and intermediate directories are preserved by default.
print_header "Analysis Finished"
print_progress "No input or intermediate directories were removed."
print_progress "Review the outputs before deleting intermediate files manually."
