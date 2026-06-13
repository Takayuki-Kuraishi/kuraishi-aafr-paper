import os
import pandas as pd
import sys

# コマンドライン引数からディレクトリを取得
if len(sys.argv) != 2:
    print("Usage: python countrow_csv.py <directory_path>")
    sys.exit(1)

directory = sys.argv[1]

# 結果を格納するリスト
results = []
file_count = 0

# ディレクトリ内のCSVファイルを処理
if not os.path.exists(directory):
    print(f"Error: Directory {directory} does not exist.")
    sys.exit(1)

for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        file_count += 1
        filepath = os.path.join(directory, filename)
        try:
            # CSVファイルを読み込み
            df = pd.read_csv(filepath)
            results.append({
                'filename': filename,
                'rows': len(df)
            })
        except Exception as e:
            print(f"Error reading file {filename}: {e}")

# 結果を表示
for result in results:
    print(f"{result['filename']}: {result['rows']} rows")

# 解析したファイル数を表示
print(f"\nTotal files: {file_count}")

