import pandas as pd
import numpy as np
import os
import re
import sys

# Command-line arguments
if len(sys.argv) == 2:
    # Backward-compatible mode
    date_str = sys.argv[1]
    input_folder = f"{date_str}_csv"
    distance_folder = f"{date_str}_csv_distance"
elif len(sys.argv) == 3:
    # General mode: explicit input and output directories
    input_folder = sys.argv[1]
    distance_folder = sys.argv[2]
else:
    print("Usage:")
    print("  python process_csv.py YYMMDD")
    print("  python process_csv.py <input_dir> <output_dir>")
    sys.exit(1)

if not os.path.isdir(input_folder):
    print(f"Error: Input directory {input_folder} does not exist.")
    sys.exit(1)

if os.path.isdir(distance_folder) and os.listdir(distance_folder):
    print(f"Error: Output directory {distance_folder} is not empty.")
    sys.exit(1)

os.makedirs(distance_folder, exist_ok=True)

# 入力フォルダ内のCSVファイルを連番でソートして処理
def extract_sequence_number(filename):
    match = re.search(r"(\d{4})_", filename)
    return (0, int(match.group(1))) if match else (1, filename)

csv_files = [f for f in os.listdir(input_folder) if f.endswith(".csv")]
if not csv_files:
    print(f"Error: No CSV files found in {input_folder}")
    sys.exit(1)

sorted_files = sorted(csv_files, key=extract_sequence_number)

# ファイル処理
for filename in sorted_files:
    input_path = os.path.join(input_folder, filename)
    
    # CSVファイルを読み込み（3行スキップ）
    try:
        df = pd.read_csv(input_path, skiprows=3)
        if df.empty:
            print(f"Error: Empty file: {filename}")
            sys.exit(1)
    except Exception as e:
        print(f"Error reading file {filename}: {e}")
        sys.exit(1)

    # 必要な列を選択して処理
    df_processed = df.iloc[:, [1, 2, 4, 5]].copy()  # .copy()を追加
    df_processed.columns = ["x1", "y1", "x2", "y2"]

    # ユークリッド距離を計算
    df_processed["distance"] = np.sqrt(
        (df_processed["x2"] - df_processed["x1"]) ** 2 +
        (df_processed["y2"] - df_processed["y1"]) ** 2
    )

    # 距離データを保存
    distance_path = os.path.join(distance_folder, f"distance_{filename}")
    try:
        df_processed.to_csv(distance_path, index=False)
    except Exception as e:
        print(f"Error saving file {distance_path}: {e}")
        sys.exit(1)

    # 処理状況を表示
    print(f"Processed file: {filename}")
