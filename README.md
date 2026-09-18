# Co-occurrence of rapid motion and close proximity as a proxy for *Drosophila* male aggression — Analysis Code

This repository contains the analysis code for the *Aggression-Associated Frame Ratio* (AAFR), a recording-level quantitative measure developed as a proxy for near-contact male–male aggression in *Drosophila melanogaster*.

AAFR combines two per-frame measurements obtained from top-view video:

- **ΔI** — frame-to-frame image change, used as an image-based measure of motion, and
- **Dₜ** — inter-fly distance, estimated from markerless tracking of the **thoracic center** of each fly with DeepLabCut.

For each valid frame, the two criteria **ΔI ≥ xₜ** and **Dₜ ≤ yₜ** are evaluated simultaneously. The AAFR value for a recording is the percentage of valid frames satisfying both criteria.

AAFR does **not** identify or classify individual behavioral actions. Obtaining the AAFR summary measure therefore does not require constructing an action-specific detector or training an action-specific classifier. DeepLabCut is used here only to obtain the thoracic coordinates required for inter-fly distance measurement; it is not trained to recognize aggression.

In the study accompanying this code, AAFR showed a positive association with the combined manual count of lunges and high-level fencing events.

> **Legacy terminology.** Some code, file names, and CSV column names retain terminology from the original analysis for compatibility. In particular, `brightness` refers to the frame-to-frame image-change measure ΔI, and the CSV column `Boxing` is a legacy column name. The events stored in this column were re-examined during manuscript revision and are described in the revised manuscript as **high-level fencing**, not boxing.

---

## Software environment

**Python analysis (image processing, distance, AAFR, statistics).** A Dockerfile pinning the analysis dependencies is provided (`docker/Dockerfile`).

- Python 3.11.15
- NumPy 1.26.4
- pandas 2.2.2
- SciPy 1.15.3
- matplotlib 3.9.0
- OpenCV 4.8.1

**Markerless tracking (DeepLabCut).** Tracking was performed on a separate GPU workstation.

- DeepLabCut 2.3.7
- TensorFlow 2.10.0, Keras 2.10.0, NumPy 1.26.4
- Ubuntu 22.04
- NVIDIA GeForce RTX 4090
- NVIDIA driver 555, CUDA 11.8, cuDNN 8.6
- Network: DLCRNet_ms5 with a ResNet-101 backbone
- Multi-animal mode with identity tracking
- One landmark (thoracic center) per fly
- 200,000 training iterations
- Train error: 0.95 px
- Test error: 2.26 px

DeepLabCut is used to obtain coordinates for distance measurement rather than to classify behavior. A tracking model does not need to be retrained simply for every new recording or strain. When animals or imaging conditions differ substantially from those represented in the tracking model, tracking performance should first be verified, with additional labeling or retraining performed if necessary.

All Python analysis steps supplied in this repository are run inside the provided container from the repository root.

---

## Repository layout

```text
scripts/
├── pipeline/                        # video → ΔI → distance generation
│   ├── video_processor.py           # split a multi-well recording into 8 single-well videos
│   ├── frame_extractor.py           # extract all frames as PNG
│   ├── 1_RGB_to_B_*.py              # ΔI step 1: extract blue channel
│   ├── 2_subtract_byAveImage_*.py   # ΔI step 2: background subtraction using mean image
│   ├── 3_thresholding_*.py          # ΔI step 3: binarization (threshold = 50)
│   ├── 4_difference_*.py            # ΔI step 4: frame-to-frame image difference
│   ├── process_csv.py               # DLC coordinates → inter-fly Euclidean distance
│   ├── countrow_csv.py              # row-count utility
│   ├── run_video_pipeline.sh        # video_processor → frame_extractor
│   ├── run_koyama_analysis_batch.sh # ΔI steps 1 → 2 → 3 → 4
│   └── process_data.sh              # DLC CSVs → process_csv → countrow
├── compute_aafr.py                  # core: ΔI + distance → AAFR
├── aafr_validation_analysis.py      # AAFR vs manual aggression score
└── bootstrap_correlation_ci.py      # bootstrap 95% CIs

docker/
└── Dockerfile                       # pinned Python environment
```

---

## Attribution

The ΔI image-processing scripts (`pipeline/1_RGB_to_B_*.py` through `pipeline/4_difference_*.py`) are adapted from original code by Hiroshi Koyama (NIBB), a co-author of this study.

---

## Pipeline overview

```text
raw multi-well video (.avi/.mp4)
   │  video_processor.py
   ▼
single-well videos (.avi)
   │  frame_extractor.py
   ▼
per-frame PNGs ───────────────────────────────┐
   │                                           │
   │  ΔI branch                                │  DeepLabCut tracking
   │  1_RGB_to_B                               │  thoracic coordinates
   │    → 2_subtract                           │
   │    → 3_thresholding (=50)                 │  process_csv.py
   │    → 4_difference                         │
   ▼                                           ▼
*_brightness_differences.csv (N-1 rows)    distance_*.csv (N rows)
   └───────────────────┬───────────────────────┘
                       ▼
                  compute_aafr.py
                       │
                       │ align ΔI and distance
                       │ remove frames lacking valid coordinates
                       │
                       │ gate:
                       │ ΔI ≥ xₜ (45000)
                       │ AND
                       │ Dₜ ≤ yₜ (70 px)
                       │
                       │ AAFR (%) =
                       │ gated frames / valid frames × 100
                       ▼
             summary_data_d70_final.csv
             (Identifier, Total Frames, Valid Frames,
              AAFR (%), Lunge, Boxing [legacy column])
                       │
        ┌──────────────┴────────────────────┐
        ▼                                   ▼
aafr_validation_analysis.py       bootstrap_correlation_ci.py
(Spearman ρ, Pearson r)           (bootstrap 95% CIs)
```

---

## Step-by-step

### A. Video preprocessing (`pipeline/`)

- **`video_processor.py <input_dir>`** — splits each raw multi-well recording into 8 single-well videos. Chamber coordinates are defined in the script and depend on the imaging layout.
- **`frame_extractor.py`** — extracts every frame of each single-well video as zero-padded PNGs (`<base>_NNNNNN.png`).

### B. Frame-to-frame image change ΔI (`pipeline/`, four ordered steps)

Original code by Hiroshi Koyama (NIBB), adapted for this study. Each step reads an input folder and writes an output folder; `run_koyama_analysis_batch.sh` substitutes the actual folder name and runs steps 1→2→3→4 in order.

1. **`1_RGB_to_B_*.py`** — extract the blue channel to obtain a single-channel grayscale image.
2. **`2_subtract_byAveImage_*.py`** — compute the stack mean image and calculate the absolute difference between each frame and that static background image. This step emphasizes the flies against the background; it does not itself measure motion.
3. **`3_thresholding_*.py`** — binarize the difference image using a fixed threshold of **50** on the 8-bit intensity scale. Pixels with an absolute difference greater than 50 are assigned 255; the remaining pixels are assigned 0.
4. **`4_difference_*.py`** — calculate frame-to-frame image change between successive binary masks:

   `ΔI = Σ |imgₜ − imgₜ₊₁|`

   Values are written to `*_brightness_differences.csv` (`Image Pair`, `Brightness Difference`).

Because the binary masks contain values of 0 or 255, ΔI is proportional to the number of pixels that changed state between successive frames. For N frames, the ΔI series has **N − 1** rows.

### C. Inter-fly distance Dₜ (`pipeline/`)

DeepLabCut tracks the thoracic center of each fly and produces per-frame coordinate CSVs. The tracking output is then converted to inter-fly distance:

- **`process_csv.py <YYMMDD>`** — reads DLC coordinate CSVs (`skiprows=3`, columns interpreted as `x1, y1, x2, y2`) and calculates

  `Dₜ = √((x2 − x1)² + (y2 − y1)²)`

  Results are written to `distance_*.csv` with one row per frame (**N** rows).

- **`countrow_csv.py <dir>`** — reports CSV row counts as a QC helper.

### D. AAFR computation (`compute_aafr.py`)

```text
python scripts/compute_aafr.py \
    --brightness-dir <dir of *_brightness_differences.csv> \
    --distance-dir <dir of distance_*.csv> \
    --aggression-counts <CSV: Identifier, Lunge, Boxing> \
    --brightness-threshold 45000 \
    --distance-threshold 70 \
    --output data/summary_data_d70_final.csv
```

- The set of `Identifier`s in `--aggression-counts` defines which recordings are processed.
- The manual-count columns are carried into the output for validation but are **not used in the AAFR formula**.
- **Alignment:** the distance series (N rows) is shifted by one row (`iloc[1:]`) to match the ΔI series (N − 1 rows). Both series are truncated to the shorter length.
- Frames lacking valid coordinates are excluded. The remaining frames constitute the **valid frames**.
- **Gate:** a frame contributes to AAFR when `ΔI ≥ 45000` **and** `Dₜ ≤ 70`.
- **Output:** `AAFR (%) = gated frames / valid frames × 100`.

The current script retains the output columns

`Identifier, Total Frames, Valid Frames, AAFR (%), Lunge, Boxing`

for compatibility with the original analysis. As noted above, `Boxing` is a legacy column name for the events described as **high-level fencing** in the revised manuscript.

AAFR is calculated separately for each recording, yielding **one AAFR value per recording**.

The **10-min analysis interval** used in the accompanying study was a study-specific choice and is not an intrinsic requirement of the AAFR calculation.

### E. Validation and statistics (`scripts/`)

- **`aafr_validation_analysis.py`** — applies the study QC criterion and calculates Spearman ρ and Pearson r between AAFR and the manual aggression score.
- **`bootstrap_correlation_ci.py`** — calculates bootstrap 95% confidence intervals (10,000 resamples, random seed = 42, percentile method) for Spearman ρ and Pearson r for the primary and sensitivity analyses.

For compatibility with the original data files, the scripts calculate the manual reference as `Lunge + Boxing`; in the revised manuscript this corresponds to the combined count of **lunges + high-level fencing**.

---

## Parameters and recalibration

The values below are those used in the accompanying study. They should not be assumed to be universal defaults when the imaging setup changes.

| Parameter / component | Value used in this study | Same imaging setup, new recordings | New strain or condition, same imaging setup | New imaging setup |
|---|---|---|---|---|
| Foreground binarization threshold | 50 | No routine change | No routine change | Verify; adjust if background or image contrast changes substantially |
| ΔI threshold `xₜ` | 45000 a.u. | Use the same threshold | Use the same threshold | Re-establish or verify using appropriate non-aggressive control recordings |
| Spatial calibration | 0.0552 mm/px | No routine change | No routine change | Recalculate if camera position, magnification, resolution, or arena geometry changes |
| Distance threshold `yₜ` | 70 px = 3.86 mm ≈ 1.5 adult male body lengths | Use the same threshold | Use the same threshold | Convert the intended physical distance using the new spatial calibration |
| DeepLabCut tracking model | DLC 2.3.7 model described above | Verify tracking quality | Verify tracking quality, particularly if morphology or behavior changes substantially | Verify; add labeled frames or retrain if tracking performance is inadequate |
| Valid-frame QC cutoff | ≥ 0.90 in this study | Apply the predefined study QC criterion | Apply the predefined study QC criterion | Define and justify an appropriate QC criterion |
| Analysis interval | 10 min in this study | Keep consistent within the experiment | Keep consistent within the experiment | Choose an interval appropriate to the experiment |

### ΔI threshold calibration

The value `xₜ = 45000` was established under the imaging conditions used in this study from three non-aggressive control recordings. For each control recording, a candidate threshold was calculated as `Q3 + 3 × IQR`; the resulting values were 44,625, 45,135, and 45,390, leading to the rounded common threshold of 45,000.

The number of calibration recordings is **not intrinsically fixed at three**. When implementing the method under a substantially different imaging setup, enough non-aggressive control recordings should be used to establish or verify a stable threshold.

Under unchanged imaging conditions, the same ΔI threshold should be applied across recordings and experimental conditions rather than recalibrated separately for each condition. Condition-specific normalization could obscure genuine differences in locomotor activity.

### Distance threshold and spatial calibration

In this study, 70 pixels corresponded to approximately 3.86 mm, or about 1.5 adult male body lengths.

If the spatial scale changes, the pixel value corresponding to the desired physical distance should be recalculated. The biological distance criterion and the pixel threshold should therefore be distinguished: the former describes the intended proximity, whereas the latter depends on the imaging geometry.

### Tracking quality control

The primary analysis in the accompanying study used a valid-frame ratio cutoff of **90%**. This was a conservative, study-specific QC criterion and is **not an intrinsic requirement of AAFR**.

Tracking performance should be assessed for the particular dataset and tracking model being used.

---

## Minimal reproduction

1. Build the provided Docker image and run the Python analysis from the repository root.
2. Preprocess videos with `run_video_pipeline.sh <input_dir>`.
3. Generate ΔI with `run_koyama_analysis_batch.sh <frame_folders>`.
4. Track the thoracic center of each fly using DeepLabCut and export coordinate CSVs.
5. Generate inter-fly distances with `process_data.sh <YYMMDD>` or `process_csv.py <YYMMDD>`.
6. Calculate AAFR with `compute_aafr.py`.
7. Calculate the association with the manual behavioral reference using `aafr_validation_analysis.py`.
8. Calculate bootstrap confidence intervals using `bootstrap_correlation_ci.py`.

---

## Interpretation and limitations

AAFR is a **recording-level frame proportion**, not an event count. It does not determine whether an individual contributing frame represents a lunge, high-level fencing, courtship, grooming, or another behavioral action.

Any movement can contribute to AAFR when both the motion and proximity criteria are satisfied. Accordingly, conditions associated with pronounced changes in locomotor activity or male–male courtship should be interpreted with appropriate caution.

AAFR is therefore intended as a quantitative summary of the co-occurrence of motion and proximity that may complement, rather than replace, action-specific behavioral analysis.

---

## Notes

- **Landmark.** Tracking uses one landmark, the **thoracic center**, for each fly. AAFR uses inter-fly distance rather than full-body posture.
- **DeepLabCut.** DeepLabCut is used for coordinate estimation, not for aggression classification.
- **Manual behavioral data.** Manual aggression counts are used to evaluate the association between AAFR and observed behavior; they are not used to calculate the AAFR value itself.
- **Input data.** Per-video ΔI series, distance series, manual aggression counts, and AAFR summaries are deposited separately; see the paper's Data Availability statement.
