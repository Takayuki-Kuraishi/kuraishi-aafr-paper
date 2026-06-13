"""
compute_aafr.py - AAFR (Aggression-Associated Frame Ratio) 計算スクリプト

distance_threshold と brightness_threshold を CLI 引数で受け取り、
summary_data.csv 形式 (Identifier, Total Frames, Valid Frames, AAFR (%), Lunge, Boxing)
で出力する。

入力:
    --brightness-dir: 輝度差分 CSV ディレクトリ (例: 250425_brightness_results/)
    --distance-dir: 距離 CSV ディレクトリ (例: 250425_csv_distance/)
    --aggression-counts: 手動アノテーション CSV (必須)
        列: Identifier, Lunge, Boxing
        この CSV の Identifier 集合が処理対象になる
    --brightness-threshold: ΔI 閾値 (デフォルト 45000)
    --distance-threshold: Dt 閾値 (pixel, デフォルト 70)
    --output: 出力 summary_data CSV

使い方:
    docker exec -w /work/aggression_brightness_analyses/aafr_paper aafr-paper-env \\
        python3 scripts/compute_aafr.py \\
            --brightness-dir /work/aggression_brightness_analyses/250425_brightness_results \\
            --distance-dir /work/aggression_brightness_analyses/250425_csv_distance \\
            --aggression-counts data/aggression_counts.csv \\
            --brightness-threshold 45000 \\
            --distance-threshold 70 \\
            --output data/summary_data_d70.csv
"""

import os
import re
import argparse
import pandas as pd


def parse_arguments():
    p = argparse.ArgumentParser(description="Compute AAFR with configurable thresholds")
    p.add_argument("--brightness-dir", required=True)
    p.add_argument("--distance-dir", required=True)
    p.add_argument(
        "--aggression-counts",
        required=True,
        help="CSV with columns: Identifier, Lunge, Boxing. "
             "Identifiers in this CSV define the processing target."
    )
    p.add_argument("--brightness-threshold", type=float, default=45000)
    p.add_argument("--distance-threshold", type=float, default=70)
    p.add_argument("--output", required=True)
    return p.parse_args()


def find_matching_files(brightness_dir, distance_dir):
    """brightness CSV と distance CSV を Identifier で対応付ける。"""
    pairs = []
    for brightness_file in sorted(os.listdir(brightness_dir)):
        if not brightness_file.endswith("_brightness_differences.csv"):
            continue
        identifier = brightness_file.replace("_frames_brightness_differences.csv", "")
        for distance_file in os.listdir(distance_dir):
            if f"distance_{identifier}DLC" in distance_file:
                pairs.append({
                    "brightness_file": os.path.join(brightness_dir, brightness_file),
                    "distance_file": os.path.join(distance_dir, distance_file),
                    "identifier": identifier,
                })
                break
    return pairs


def sort_key(identifier):
    movie_match = re.search(r"movie(\d+)", identifier)
    tail_match = re.search(r"_(\d+)$", identifier)
    movie_num = int(movie_match.group(1)) if movie_match else 0
    tail_num = int(tail_match.group(1)) if tail_match else 0
    return movie_num * 100 + tail_num


def compute_aafr_for_pair(brightness_file, distance_file, b_thr, d_thr):
    """1 動画ぶんの AAFR を計算する。

    distance CSV の先頭 1 行をスキップして brightness と対応付ける。長さが
    一致しないペアでは短い方に切り詰めて計算する (警告を出す)。
    """
    brightness_df = pd.read_csv(brightness_file)
    distance_df = pd.read_csv(distance_file)

    # distance CSV の先頭 1 行をスキップして brightness と対応付ける
    distance_values = distance_df["distance"].iloc[1:].values

    # 長さを揃える (短い方に合わせる)
    n = min(len(brightness_df), len(distance_values))
    if len(brightness_df) != len(distance_values):
        print(f"  [warn] length mismatch: brightness={len(brightness_df)}, "
              f"distance(shifted)={len(distance_values)}, truncated to {n}")

    combined_df = pd.DataFrame({
        "Frame": range(1, n + 1),
        "Brightness_Difference": brightness_df["Brightness Difference"].iloc[:n].values,
        "Distance": distance_values[:n],
    })

    valid_df = combined_df.dropna()
    condition = (
        (valid_df["Brightness_Difference"] >= b_thr) &
        (valid_df["Distance"] <= d_thr)
    )
    matching_count = int(condition.sum())
    total_frames = len(combined_df)
    valid_frames = len(valid_df)
    aafr_pct = (matching_count / valid_frames * 100) if valid_frames > 0 else 0.0

    return {
        "Total Frames": total_frames,
        "Valid Frames": valid_frames,
        "AAFR (%)": round(aafr_pct, 3),
    }


def main():
    args = parse_arguments()
    print(f"[compute_aafr] brightness threshold = {args.brightness_threshold}")
    print(f"[compute_aafr] distance threshold   = {args.distance_threshold}")

    # aggression_counts.csv から処理対象 Identifier と Lunge/Boxing を取得
    counts_df = pd.read_csv(args.aggression_counts)
    target_identifiers = set(counts_df["Identifier"])
    counts_lookup = {
        row["Identifier"]: {
            "Lunge": int(row["Lunge"]),
            "Boxing": int(row["Boxing"]),
        }
        for _, row in counts_df.iterrows()
    }
    print(f"[compute_aafr] target identifiers from counts CSV: {len(target_identifiers)}")

    # ディレクトリ内の全ペアを取得し、Identifier フィルタを適用
    all_pairs = find_matching_files(args.brightness_dir, args.distance_dir)
    pairs = [p for p in all_pairs if p["identifier"] in target_identifiers]
    pairs.sort(key=lambda p: sort_key(p["identifier"]))
    print(f"[compute_aafr] found {len(all_pairs)} pairs total, "
          f"processing {len(pairs)} after filtering by counts CSV")

    # 欠けている Identifier をチェック
    found_idents = {p["identifier"] for p in pairs}
    missing = target_identifiers - found_idents
    if missing:
        print(f"[compute_aafr] WARNING: {len(missing)} identifiers in counts CSV "
              f"have no matching brightness/distance files:")
        for m in sorted(missing):
            print(f"  - {m}")

    rows = []
    for pair in pairs:
        print(f"  processing {pair['identifier']}")
        result = compute_aafr_for_pair(
            pair["brightness_file"],
            pair["distance_file"],
            args.brightness_threshold,
            args.distance_threshold,
        )
        counts = counts_lookup[pair["identifier"]]
        rows.append({
            "Identifier": pair["identifier"],
            "Total Frames": result["Total Frames"],
            "Valid Frames": result["Valid Frames"],
            "AAFR (%)": result["AAFR (%)"],
            "Lunge": counts["Lunge"],
            "Boxing": counts["Boxing"],
        })

    out_df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    out_df.to_csv(args.output, index=False)
    print(f"[compute_aafr] wrote {len(rows)} rows -> {args.output}")


if __name__ == "__main__":
    main()
