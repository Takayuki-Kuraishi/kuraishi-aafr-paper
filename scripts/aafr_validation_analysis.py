"""
AAFR Validation Analysis
=========================
Manual aggression score (Lunge + Boxing count) vs
Aggression-Associated Frame Ratio (AAFR) の相関分析。

Usage:
    python aafr_validation_analysis.py --input summary_data.csv --output-dir results/

入力CSVに必要な列:
    - Identifier
    - Total Frames
    - Valid Frames
    - AAFR (%)           ... Percentage among Valid Frames
    - Lunge              ... Lunge count
    - Boxing             ... Boxing (foreleg strike) count

出力:
    - correlation_analysis.txt  ... 統計結果テキスト
"""

import argparse
import csv
import os

from scipy import stats


# ===== パラメータ =====
VALID_FRAME_THRESHOLD = 0.90   # Valid frame ratio の除外基準


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="AAFR validation: correlation with manual aggression score"
    )
    parser.add_argument(
        "--input", required=True,
        help="CSV file with columns: Identifier, Total Frames, Valid Frames, "
             "AAFR (%), Lunge, Boxing"
    )
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory for output files"
    )
    return parser.parse_args()


def run_analysis(data, output_dir):
    """相関分析を実行し、結果をテキストファイルに出力する。"""

    lines = []   # テキスト出力用バッファ

    def log(text=""):
        lines.append(text)
        print(text)

    # ----- 1. トラッキング品質による除外 -----
    log("=" * 60)
    log("1. TRACKING QUALITY CONTROL")
    log("=" * 60)
    log(f"Criterion: Valid frame ratio >= {VALID_FRAME_THRESHOLD*100:.0f}%")
    log()

    included = []
    excluded = []
    for d in data:
        vr = d["valid_frames"] / d["total_frames"]
        d["valid_ratio"] = vr
        if vr >= VALID_FRAME_THRESHOLD:
            included.append(d)
        else:
            excluded.append(d)
            log(f"  EXCLUDED: {d['identifier']}  "
                f"(Valid ratio = {vr*100:.1f}%)")

    log(f"\nTotal videos: {len(data)}")
    log(f"Excluded: {len(excluded)}")
    log(f"Retained: {len(included)}")

    if len(included) < 5:
        log("\nERROR: Too few videos retained for analysis.")
        return lines

    # ----- 2. データ概要 (保持された動画) -----
    manual_scores = [d["manual_score"] for d in included]
    aafr_values = [d["aafr"] for d in included]

    log()
    log("=" * 60)
    log("2. DATA SUMMARY (retained videos)")
    log("=" * 60)
    log(f"{'Identifier':>40} {'Valid%':>7} {'Manual':>7} {'AAFR%':>8}")
    log("-" * 66)
    for d in included:
        log(f"{d['identifier']:>40} {d['valid_ratio']*100:>6.1f}% "
            f"{d['manual_score']:>7} {d['aafr']:>8.3f}")

    # ----- 3. 相関分析 -----
    log()
    log("=" * 60)
    log("3. CORRELATION ANALYSIS")
    log("=" * 60)
    log(f"n = {len(included)}")

    r_pearson, p_pearson = stats.pearsonr(manual_scores, aafr_values)
    r_spearman, p_spearman = stats.spearmanr(manual_scores, aafr_values)

    log(f"Pearson  r = {r_pearson:.4f}  (p = {p_pearson:.6f})")
    log(f"Spearman ρ = {r_spearman:.4f}  (p = {p_spearman:.6f})")

    # ----- テキスト出力 -----
    txt_path = os.path.join(output_dir, "correlation_analysis.txt")
    with open(txt_path, "w") as f:
        f.write("\n".join(lines))
    print(f"\nFull results saved to: {txt_path}")

    return lines


def load_csv(filepath):
    """CSVを読み込み、辞書のリストとして返す。"""
    records = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                "identifier": row["Identifier"].strip(),
                "total_frames": int(row["Total Frames"]),
                "valid_frames": int(row["Valid Frames"]),
                "aafr": float(row["AAFR (%)"]),
                "lunge": int(row["Lunge"]),
                "boxing": int(row["Boxing"]),
                "manual_score": int(row["Lunge"]) + int(row["Boxing"]),
            })
    return records


def main():
    args = parse_arguments()
    os.makedirs(args.output_dir, exist_ok=True)
    data = load_csv(args.input)
    print(f"Loaded {len(data)} videos from {args.input}")
    run_analysis(data, args.output_dir)


if __name__ == "__main__":
    main()
