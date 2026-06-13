#!/bin/bash

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
        sed "s/your_folder_name/${FOLDER_NAME}/g" "$script" > "$temp_script"
        
        # Run the modified script
        print_progress "Executing ${script}..."
        python3 "$temp_script"
        
        # Remove temporary file
        print_progress "Cleaning up temporary files..."
        rm "$temp_script"
        
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

print_header "Organizing Output Files"

# Extract prefix from the first argument pattern
# Remove trailing wildcard if present
PREFIX=$(echo "${expanded_folders[0]}" | sed -E 's/^([0-9]+)_.+$/\1_/')

# Create directories if they don't exist
mkdir -p "${PREFIX}brightness_results"
mkdir -p "${PREFIX}stack_average"

print_progress "Creating directories with prefix: ${PREFIX}"

# Move files to respective directories
print_progress "Moving CSV files..."
mv ${PREFIX}*.csv "${PREFIX}brightness_results/"

print_progress "Moving stack average images..."
mv ${PREFIX}*_stack_average.png "${PREFIX}stack_average/"

print_header "File Organization Complete"
print_progress "Files have been organized into their respective directories"
echo "- CSVs: ${PREFIX}brightness_results/"
echo "- Stack average images: ${PREFIX}stack_average/"

print_progress "Processed ${TOTAL_FOLDERS} folders successfully"

# Cleanup phase
print_header "Starting Cleanup Phase"
print_progress "Removing processed folders while preserving results..."

# Store the pattern used for matching folders
PATTERN=$1

# Remove all matching directories except the brightness_results directory
for dir in ${PREFIX}*; do
    # Skip if it's the brightness_results directory
    if [ "$dir" != "${PREFIX}brightness_results" ] && [ -d "$dir" ]; then
        print_progress "Removing directory: $dir"
        rm -rf "$dir"
    fi
done

print_header "Cleanup Complete"
print_progress "All processed folders have been removed"
print_progress "Analysis results are preserved in ${PREFIX}brightness_results/"