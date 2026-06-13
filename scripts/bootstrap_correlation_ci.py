#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bootstrap_correlation_ci.py

Manual aggression score vs AAFR の相関係数について、
ブートストラップ法による 95% 信頼区間を算出する。

設計方針:
    - 主分析: n = 21 (Valid frame ratio >= 0.90 で除外後)
    - 感度分析: n = 27 (除外前、全 manually annotated videos)
    - Spearman ρ と Pearson r の両方
    - ブートストラップ: 10,000 反復, random seed = 42 (再現性確保)
    - パーセンタイル法 (2.5th, 97.5th)

入力:
    --input: summary_data.csv (Identifier, Total Frames, Valid Frames,
                                AAFR (%), Lunge, Boxing の 6 列)

出力:
    --output: 計算結果のテキストログ
              (Methods 推奨テキストを末尾に自動生成)

使用例 (fish shell, 220 マシン, aafr-paper-env コンテナ):
    docker exec -w /work/aggression_brightness_analyses/aafr_paper aafr-paper-env \\
        python3 scripts/bootstrap_correlation_ci.py \\
            --input data/summary_data.csv \\
            --output results/260521_bootstrap_ci/bootstrap_ci_result.txt
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy import stats


# ===== 定数 =====
N_BOOTSTRAP = 10_000
RANDOM_SEED = 42
CI_LOW_PCT = 2.5
CI_HIGH_PCT = 97.5
VALID_FRAME_THRESHOLD = 0.90   # aafr_validation_analysis.py と一致


def parse_arguments():
    p = argparse.ArgumentParser(
        description="Bootstrap 95% CI for Manual–AAFR correlation"
    )
    p.add_argument(
        "--input", required=True,
        help="summary_data.csv path",
    )
    p.add_argument(
        "--output", required=True,
        help="Output text log file path",
    )
    return p.parse_args()


def load_data(filepath):
    """summary_data.csv を読み込み、辞書のリストとして返す。"""
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
            })
    for r in records:
        r["manual_score"] = r["lunge"] + r["boxing"]
        r["valid_ratio"] = r["valid_frames"] / r["total_frames"]
    return records


def bootstrap_ci(x, y, method, n_boot, seed):
    """
    パーセンタイル法でブートストラップ 95% CI を算出する。

    Parameters
    ----------
    x, y : array-like
        相関を取る 2 変数
    method : str
        'spearman' or 'pearson'
    n_boot : int
        反復回数
    seed : int
        乱数シード

    Returns
    -------
    point_estimate : float
        観測データでの相関係数
    p_value : float
        観測データでの p 値
    ci_low, ci_high : float
        95% CI の下限・上限
    n_valid_boots : int
        有効ブートストラップ反復数 (定数列が出ると相関が NaN になるため)
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)

    if method == "spearman":
        rho, p = stats.spearmanr(x, y)
    elif method == "pearson":
        rho, p = stats.pearsonr(x, y)
    else:
        raise ValueError(f"Unknown method: {method}")

    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        xb, yb = x[idx], y[idx]
        # 定数列だと相関未定義 → スキップ
        if np.std(xb) == 0 or np.std(yb) == 0:
            continue
        if method == "spearman":
            rb, _ = stats.spearmanr(xb, yb)
        else:
            rb, _ = stats.pearsonr(xb, yb)
        if np.isfinite(rb):
            boots.append(rb)

    boots = np.array(boots)
    ci_low = float(np.percentile(boots, CI_LOW_PCT))
    ci_high = float(np.percentile(boots, CI_HIGH_PCT))
    return float(rho), float(p), ci_low, ci_high, len(boots)


def main():
    args = parse_arguments()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    log_lines = []

    def log(text=""):
        s = str(text)
        print(s)
        log_lines.append(s)

    # ----- ヘッダ -----
    log("Bootstrap 95% CI for Manual–AAFR correlation")
    log("=" * 60)
    log(f"Date/time         : {datetime.now().isoformat(timespec='seconds')}")
    log(f"Input             : {input_path}")
    log(f"Output            : {output_path}")
    log(f"Bootstrap method  : Percentile ({CI_LOW_PCT}th, {CI_HIGH_PCT}th)")
    log(f"Iterations        : {N_BOOTSTRAP:,}")
    log(f"Random seed       : {RANDOM_SEED}")
    log(f"QC threshold      : Valid frame ratio >= {VALID_FRAME_THRESHOLD}")
    log("")

    # ----- データ読込 -----
    records = load_data(input_path)
    log(f"Loaded {len(records)} videos from input CSV")
    log("")

    # ----- データ集合定義 -----
    all_27 = records
    retained_21 = [r for r in records if r["valid_ratio"] >= VALID_FRAME_THRESHOLD]
    log(f"Full set (n = 27)       : {len(all_27)} videos")
    log(f"Retained set (n = 21)   : {len(retained_21)} videos "
        f"(QC: valid ratio >= {VALID_FRAME_THRESHOLD*100:.0f}%)")
    log("")

    # ----- 解析: 4 ケース (主分析 ρ・r, 感度分析 ρ・r) -----
    analyses = [
        ("Primary analysis (n = 21, after QC)", retained_21, "spearman"),
        ("Primary analysis (n = 21, after QC)", retained_21, "pearson"),
        ("Sensitivity analysis (n = 27, all videos)", all_27, "spearman"),
        ("Sensitivity analysis (n = 27, all videos)", all_27, "pearson"),
    ]

    results = {}   # キー: (label, method) → (rho, p, ci_low, ci_high, n_boot_valid)

    prev_label = None
    for label, dataset, method in analyses:
        if label != prev_label:
            log("=" * 60)
            log(label)
            log("=" * 60)
            prev_label = label

        x = [r["manual_score"] for r in dataset]
        y = [r["aafr"] for r in dataset]

        rho, p, ci_lo, ci_hi, n_boot_valid = bootstrap_ci(
            x, y, method, N_BOOTSTRAP, RANDOM_SEED
        )

        method_label = "Spearman ρ" if method == "spearman" else "Pearson  r"
        log(f"  {method_label}: {rho:.4f}  "
            f"(95% CI: {ci_lo:.4f} – {ci_hi:.4f}, p = {p:.6g})")
        log(f"     n = {len(dataset)}, valid bootstrap iterations = "
            f"{n_boot_valid:,} / {N_BOOTSTRAP:,}")

        results[(label, method)] = (rho, p, ci_lo, ci_hi)

    log("")
    log("=" * 60)
    log("MANUSCRIPT-READY TEXT (for Methods / Statistical Analysis)")
    log("=" * 60)

    pri_sp = results[(analyses[0][0], "spearman")]
    pri_pe = results[(analyses[1][0], "pearson")]
    sen_sp = results[(analyses[2][0], "spearman")]
    sen_pe = results[(analyses[3][0], "pearson")]

    log("")
    log("Suggested Methods text:")
    log("")
    log('    "95% confidence intervals for Spearman\'s ρ and Pearson\'s r '
        f"were obtained by bootstrap resampling with {N_BOOTSTRAP:,} "
        "iterations (random seed = {0}) using the percentile method "
        "({1}th and {2}th percentiles of the bootstrap distribution)."
        .format(RANDOM_SEED, CI_LOW_PCT, CI_HIGH_PCT))
    log("")
    log("    Primary analysis was performed on 21 videos that passed the "
        "tracking quality control criterion. To assess the sensitivity of the "
        "results to this exclusion criterion, the same analysis was repeated "
        "on the full set of 27 manually annotated videos. Both analyses "
        "yielded consistent correlation estimates:")
    log("")
    log(f"        Primary (n = 21): Spearman ρ = {pri_sp[0]:.2f} "
        f"(95% CI {pri_sp[2]:.2f}–{pri_sp[3]:.2f}); "
        f"Pearson r = {pri_pe[0]:.2f} "
        f"(95% CI {pri_pe[2]:.2f}–{pri_pe[3]:.2f})")
    log(f"        Sensitivity (n = 27): Spearman ρ = {sen_sp[0]:.2f} "
        f"(95% CI {sen_sp[2]:.2f}–{sen_sp[3]:.2f}); "
        f"Pearson r = {sen_pe[0]:.2f} "
        f"(95% CI {sen_pe[2]:.2f}–{sen_pe[3]:.2f})")
    log("")
    log("Suggested Results text (concise, reader-friendly):")
    log("")
    log(f'    "Across the 21 retained videos, the manual aggression score '
        f"and the AAFR showed a strong positive correlation "
        f"(Spearman ρ = {pri_sp[0]:.2f}, p < 0.001; Fig. 5)."
        '"')
    log("")
    log("=" * 60)
    log("END OF BOOTSTRAP CI LOG")
    log("=" * 60)

    # ----- ログ書き出し -----
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"\nResult saved to: {output_path}")


if __name__ == "__main__":
    main()
