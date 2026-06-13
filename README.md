# Automated Quantification of *Drosophila* Male Aggression — Analysis Code

This repository contains the analysis code for the *Aggression-Associated Frame Ratio* (AAFR),
an automated, interpretable measure of male–male aggression in *Drosophila melanogaster*.
The method combines two per-frame features extracted from ordinary top-view video:

- **ΔI** — frame-to-frame brightness change (a proxy for abrupt motion), and
- **Dₜ** — inter-fly distance, estimated from markerless tracking of the **thoracic center** of each fly with DeepLabCut.

A video frame is counted as *aggression-associated* when **ΔI ≥ xₜ** and **Dₜ ≤ yₜ** simultaneously.
The AAFR is the percentage of valid frames meeting both criteria, and it correlates with manually
counted close-contact aggressive actions (lunges + foreleg strikes).

> Numerical results (ρ, CI, p, n, AAFR) are produced by the Python code in this repository and are
> the single source of truth.

---

## Scope of this repository

This repository deposits the code that **defines the AAFR method and reproduces the reported
correlation**:

1. the video-preprocessing pipeline (video → ΔI; markerless-tracking coordinates → inter-fly distance),
2. the AAFR computation, and
3. the validation against manual annotation (Spearman/Pearson correlation and bootstrap 95% CIs).

Figures for the paper were produced separately in R (ggplot2) and only re-checked the Python values;
that plotting code is not included here. The input datasets are deposited separately (see the paper's
Data Availability statement).

---

## Software environment

**Python analysis (image processing, distance, AAFR, statistics).** A Dockerfile pinning all
dependencies is provided (`docker/Dockerfile`).

- Python 3.11.15
- NumPy 1.26.4, pandas 2.2.2, SciPy 1.15.3, matplotlib 3.9.0, OpenCV 4.8.1

**Markerless tracking (DeepLabCut).** Performed on a separate GPU workstation.

- DeepLabCut 2.3.7 (TensorFlow backend: TensorFlow 2.10.0, Keras 2.10.0, NumPy 1.26.4)
- Ubuntu 22.04, NVIDIA GeForce RTX 4090, driver 555, CUDA 11.8, cuDNN 8.6
- Network: DLCRNet_ms5 with a ResNet-101 backbone, multi-animal mode with identity tracking,
  one landmark (thoracic center) per fly, trained for 200,000 iterations (train error 0.95 px,
  test error 2.26 px)

All Python steps are run inside the provided container from the repository root.

---

## Repository layout

```
scripts/
├── pipeline/                       # video → ΔI → distance generation
│   ├── video_processor.py          # split a multi-well recording into 8 single-well videos
│   ├── frame_extractor.py          # extract all frames as PNG
│   ├── 1_RGB_to_B_*.py             # ΔI step 1: extract blue channel (grayscale)
│   ├── 2_subtract_byAveImage_*.py  # ΔI step 2: background subtraction (mean image)
│   ├── 3_thresholding_*.py         # ΔI step 3: binarization (fixed threshold = 50)
│   ├── 4_difference_*.py           # ΔI step 4: frame-to-frame difference -> brightness CSV
│   ├── process_csv.py              # DLC coordinates -> inter-fly Euclidean distance CSV
│   ├── countrow_csv.py             # row-count utility (QC helper)
│   ├── run_video_pipeline.sh       # orchestrator: video_processor -> frame_extractor
│   ├── run_koyama_analysis_batch.sh# orchestrator: ΔI steps 1->2->3->4 over folders
│   └── process_data.sh             # orchestrator: copy DLC CSVs -> process_csv -> countrow
├── compute_aafr.py                 # ** core: brightness + distance -> AAFR (summary_data) **
├── aafr_validation_analysis.py     # correlation of AAFR vs manual aggression score
└── bootstrap_correlation_ci.py     # bootstrap 95% CIs for the correlation
docker/
└── Dockerfile                      # pinned Python environment (aafr-paper-env)
```

---

## Attribution

The ΔI motion-intensity scripts (`pipeline/1_RGB_to_B_*.py` through `pipeline/4_difference_*.py`)
are adapted from original code by Hiroshi Koyama (NIBB), a co-author of this study.

---

## Pipeline overview (data flow)

```
raw multi-well video (.avi/.mp4)
   │  video_processor.py        split into 8 single-well videos
   ▼
single-well videos (.avi)
   │  frame_extractor.py        extract all frames as PNG
   ▼
per-frame PNGs ───────────────────────────────┐
   │                                           │  (transferred to a GPU workstation;
   │  ΔI branch                                │   tracked with DeepLabCut -> coordinate CSVs)
   │  1_RGB_to_B -> 2_subtract                 │   process_csv.py
   │    -> 3_thresholding (=50) -> 4_difference│   (skiprows=3; x1,y1,x2,y2 -> Euclidean distance)
   ▼                                           ▼
*_brightness_differences.csv (N-1 rows)    distance_*.csv (N rows)
   └───────────────────┬───────────────────────┘
                       ▼  compute_aafr.py
                          align: shift distance by one row (iloc[1:]), truncate to the
                                 shorter length, drop rows with missing coordinates (-> valid frames)
                          gate:  ΔI ≥ xₜ (45000)  AND  Dₜ ≤ yₜ (70 px)
                          AAFR(%) = gated frames / valid frames × 100
                       ▼
            summary_data_d70_final.csv
            (Identifier, Total Frames, Valid Frames, AAFR (%), Lunge, Boxing)
                       │
        ┌──────────────┴───────────────────┐
        ▼                                   ▼
 aafr_validation_analysis.py        bootstrap_correlation_ci.py
  (Spearman ρ, Pearson r;            (95% CI; n = 21 and n = 27)
   QC filter: valid frame ratio ≥ 0.90)
```

---

## Step-by-step

### A. Video preprocessing (`pipeline/`)

- **`video_processor.py <input_dir>`** — splits each raw multi-well recording into 8 single-well
  videos. Per-rig chamber coordinates are defined in the script and depend on the imaging layout.
- **`frame_extractor.py`** — extracts every frame of each single-well video as zero-padded PNGs
  (`<base>_NNNNNN.png`).

### B. Motion intensity ΔI (`pipeline/`, four ordered steps)

Original code by Hiroshi Koyama (NIBB), adapted for this study. Each step reads an input folder and
writes an output folder; `run_koyama_analysis_batch.sh` substitutes the real folder name and runs
steps 1→2→3→4 in order.

1. **`1_RGB_to_B_*.py`** — extract the blue channel and convert to grayscale.
2. **`2_subtract_byAveImage_*.py`** — compute the stack mean image and take the absolute difference
   of each frame from it (background subtraction).
3. **`3_thresholding_*.py`** — binarize the difference image with a fixed threshold of **50**.
4. **`4_difference_*.py`** — for successive binary images, compute `ΔI = Σ |imgₜ − imgₜ₊₁|`, written
   to `*_brightness_differences.csv` (columns: `Image Pair`, `Brightness Difference`).

Because the binary images take values 0 or 255, ΔI is proportional (×255) to the number of pixels
that changed state between two frames. For N frames the ΔI series has **N − 1** rows.

### C. Inter-fly distance Dₜ (`pipeline/`)

DeepLabCut tracking (thoracic center of each fly) is run on the GPU workstation, producing per-frame
coordinate CSVs. Then:

- **`process_csv.py <YYMMDD>`** — reads each DLC coordinate CSV (`skiprows=3`, columns interpreted as
  `x1, y1, x2, y2`) and computes `Dₜ = √((x2 − x1)² + (y2 − y1)²)`, written to `distance_*.csv`
  (one row per frame, **N** rows).
- **`countrow_csv.py <dir>`** — lists CSV row counts (QC helper).

### D. AAFR computation (`compute_aafr.py`, core)

```
python scripts/compute_aafr.py \
    --brightness-dir <dir of *_brightness_differences.csv> \
    --distance-dir   <dir of distance_*.csv> \
    --aggression-counts <CSV: Identifier, Lunge, Boxing> \
    --brightness-threshold 45000 \
    --distance-threshold 70 \
    --output data/summary_data_d70_final.csv
```

- The set of `Identifier`s in `--aggression-counts` defines which videos are processed.
- **Alignment:** the distance series (N rows) is shifted by one row (`iloc[1:]`) to match the ΔI
  series (N − 1 rows), both are truncated to the shorter length, and rows with missing coordinates
  are dropped; the remainder are the **valid frames**.
- **Gate:** a frame is aggression-associated when `ΔI ≥ 45000` **and** `Dₜ ≤ 70`.
- **Output:** `AAFR (%) = gated frames / valid frames × 100`, with columns
  `Identifier, Total Frames, Valid Frames, AAFR (%), Lunge, Boxing`.

### E. Validation and statistics (`scripts/`)

- **`aafr_validation_analysis.py`** — applies the QC filter (valid frame ratio ≥ 0.90) and computes
  Spearman ρ and Pearson r between AAFR and the manual aggression score (Lunge + Boxing).
- **`bootstrap_correlation_ci.py`** — bootstrap 95% CIs (10,000 resamples, random seed = 42,
  percentile method) for both Spearman ρ and Pearson r, for the primary analysis (n = 21) and the
  sensitivity analysis (n = 27).

---

## Key parameters

| Parameter | Value | Meaning |
|---|---|---|
| Binarization threshold | 50 | ΔI step 3 |
| ΔI threshold `xₜ` | 45000 (a.u.) | derived from `Q3 + 3 × IQR` of non-aggressive controls |
| Distance threshold `yₜ` | 70 px (≈ 3.86 mm ≈ 1.5 body lengths) | near-contact proximity |
| Valid frame ratio cutoff | ≥ 0.90 | tracking quality control |
| Bootstrap | 10,000 resamples, seed 42 | percentile 95% CIs |

---

## Minimal reproduction

1. Build the provided Docker image and run all Python commands from the repository root inside it.
2. Preprocess videos: `run_video_pipeline.sh <input_dir>`.
3. Generate ΔI: `run_koyama_analysis_batch.sh <frame_folders>`.
4. Track with DeepLabCut on a GPU workstation (thoracic center, multi-animal); export coordinate CSVs.
5. Generate distances: `process_data.sh <YYMMDD>` (or `process_csv.py <YYMMDD>` directly).
6. Compute AAFR: `compute_aafr.py` (see Section D), producing `summary_data_d70_final.csv`.
7. Validate: `aafr_validation_analysis.py`, then `bootstrap_correlation_ci.py`.

---

## Notes

- **Single source of truth.** All reported numbers (ρ, CI, p, n, AAFR) come from the Python code in
  this repository.
- **Landmark.** Tracking uses a single landmark, the **thoracic center**, of each fly; the AAFR uses
  only the inter-fly distance, not full posture.
- **Input data** (per-video brightness and distance CSVs, manual aggression counts) are deposited
  separately; see the paper's Data Availability statement.
