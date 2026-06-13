#!/bin/bash
# 引数チェック
if [ $# -ne 1 ]; then
    echo "Usage: $0 YYMMDD"
    echo "Example: $0 240830"
    exit 1
fi

DATE=$1
MAIN_DIR="251110_0096-Takayuki-2025-01-14"
SOURCE_DIR="${MAIN_DIR}/videos/${DATE}"

# ソースディレクトリの存在確認
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory ${SOURCE_DIR} does not exist."
    exit 1
fi

# 一時ディレクトリ作成
echo "Creating directory ${DATE}_csv..."
mkdir -p "${DATE}_csv"

# CSVファイルのコピー
echo "Copying CSV files..."
cp "${SOURCE_DIR}"/*.csv "${DATE}_csv/"

# Pythonスクリプトの実行
echo "Processing CSV files..."
python3 process_csv.py "$DATE"

# 入力用のCSVディレクトリを削除
echo "Cleaning up temporary directory..."
rm -rf "${DATE}_csv"

# 出力フォルダの確認
distance_folder="${DATE}_csv_distance"
if [ ! -d "$distance_folder" ]; then
    echo "Error: ${distance_folder} does not exist."
    exit 1
fi

# countrow_csv.py を実行
echo "Analyzing processed CSV files with countrow_csv.py..."
python3 countrow_csv.py "$distance_folder"

echo "All processing completed!"
