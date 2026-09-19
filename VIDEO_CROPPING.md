# Video Cropping Guide for the AAFR Workflow

This document provides practical guidance for converting raw behavioral videos containing multiple assay regions into individual videos suitable for the AAFR analysis workflow.

The cropping step is intentionally described as a **general procedure rather than a fixed software implementation**. Camera placement, image resolution, arena shape, arena number, magnification, illumination, and physical layout differ substantially among laboratories. A cropping script that works well for one imaging system may therefore be inappropriate for another.

The goal is not to reproduce one specific cropping script. The goal is to produce well-defined, visually verified videos in which each output file corresponds to one assay region and can be passed reliably to both the motion-analysis and tracking branches of the AAFR pipeline.

For software installation, see [`SETUP.md`](SETUP.md).

For the AAFR calculation, analysis parameters, and recalibration guidance, see [`README.md`](README.md).

---

## Using an AI assistant to develop a cropping workflow

Video cropping is a task for which an AI assistant can be particularly useful because the basic logic is simple but the details are strongly dependent on the imaging system.

A practical approach is to provide the AI assistant with:

- this entire `VIDEO_CROPPING.md`;
- one or more representative video frames;
- the image resolution;
- the number and arrangement of assay regions;
- the approximate shape and size of each arena or well;
- the desired output naming convention; and
- the operating environment in which the script will run.

You can then ask the AI to help write or adapt a small cropping program for your own setup.

For example:

> I want to crop this multi-arena behavioral video for the AAFR pipeline. I have attached a representative frame and this VIDEO_CROPPING.md. The video resolution is 1920 × 1080 pixels and there are eight circular assay regions. Please help me determine a robust way to define the crop coordinates, preview them visually, and export one video per assay region. Do not batch-process the complete dataset until I have checked the output from a small test.

It is usually better to proceed interactively:

1. inspect one frame;
2. define or detect candidate regions;
3. preview the regions;
4. correct mistakes;
5. crop one test video;
6. inspect the cropped output;
7. only then automate the full dataset.

When asking an AI assistant for help, provide the complete error message and the relevant script section if something fails.

AI-generated code should be inspected before execution, particularly when it contains commands that delete, overwrite, rename, or move large numbers of files.

---

# 1. Purpose of the cropping step

A raw recording may contain several assay regions in the same camera image.

For AAFR analysis, it is convenient to convert this into separate videos:

```text
Raw multi-arena video
        |
        +--> assay region 1 --> cropped video 1
        |
        +--> assay region 2 --> cropped video 2
        |
        +--> assay region 3 --> cropped video 3
        |
        ...
```

Each cropped video should correspond to one experimental unit, such as one pair of flies in one arena.

The same cropped recording should then be used as the basis for:

```text
cropped video
     |
     +--> motion branch --> ΔI
     |
     +--> tracking branch --> inter-fly distance
```

This keeps the motion and distance measurements associated with the same assay region and recording.

---

# 2. Cropping is not part of the mathematical definition of AAFR

AAFR itself is calculated from two per-frame measurements:

- frame-to-frame image change, ΔI; and
- inter-fly distance, D_t.

Cropping is an upstream preprocessing step used to isolate the relevant assay region.

Accordingly, the exact way in which crop coordinates are obtained is not intrinsic to AAFR.

Coordinates may be determined:

- manually;
- with the aid of a grid;
- by circle detection;
- by edge or contour detection;
- from known fixed arena positions;
- from fiducial markers;
- by another computer-vision method; or
- by a combination of automatic detection and manual confirmation.

What matters is that the final regions are correct, reproducible, and verified.

---

# 3. Why a universal cropping script is not provided

Cropping geometry depends strongly on the recording system.

Variables that may differ among laboratories include:

- image resolution;
- camera position;
- lens and magnification;
- arena diameter or shape;
- number of arenas per image;
- distance between arenas;
- rotation or translation of the assay plate;
- whether the plate position changes between recordings;
- whether arenas approach the edge of the image;
- illumination and contrast.

For this reason, users should adapt the cropping procedure to their own imaging system rather than assuming that coordinates or automatic-detection parameters obtained under another setup will transfer directly.

---

# 4. Recommended overall workflow

A robust cropping workflow is:

```text
1. Inspect representative frames
2. Identify the physical assay regions
3. Define or automatically detect candidate regions
4. Assign stable physical region identifiers
5. Record occupancy
6. Preview the proposed crop rectangles
7. Check coordinate validity
8. Save the accepted coordinates
9. Crop one or a few test videos
10. Inspect the cropped videos
11. Confirm compatibility with tracking and motion analysis
12. Only then batch-process the full dataset
```

The most important principle is:

> **Automatic detection may propose regions, but the regions should be visually verified before they are accepted for quantitative analysis.**

---

# 5. Inspect the raw videos first

Before writing or running a cropping script, inspect several raw recordings.

Record at least:

- frame width and height;
- frame rate;
- approximate recording duration;
- number of physical assay regions;
- layout of those regions;
- whether their positions are fixed between recordings;
- whether some regions are empty;
- whether arenas approach or cross the image boundary;
- whether illumination or image scale changes among recordings.

Do not assume that all videos have identical geometry merely because they were recorded in the same experiment.

If several resolutions or layouts occur, treat them explicitly rather than forcing all recordings into one coordinate scheme.

---

# 6. Choose a stable physical region numbering system

Each physical assay position should have a stable identifier.

For example:

```text
w01
w02
w03
w04
...
```

The identifier should refer to the **physical assay position**, not to the order in which an automatic detector happened to find it.

This distinction is important because detection order may change when:

- the plate moves;
- one region is empty;
- one arena is missed;
- an extra object is falsely detected;
- the video resolution changes.

A good naming convention is:

```text
<recording_id>_w01
<recording_id>_w02
<recording_id>_w03
...
```

For example:

```text
experiment01_w01.avi
experiment01_w02.avi
```

The same identifier should be retained throughout downstream analysis whenever possible.

---

# 7. Record all physical positions, including empty regions

When practical, maintain a table containing **all physical assay positions**, not only the occupied ones.

A useful coordinate table might contain:

```text
recording
region_id
x1
y1
x2
y2
occupied
notes
```

For example:

```text
recording01   w01   ...   yes
recording01   w02   ...   no
recording01   w03   ...   yes
```

This makes it possible to distinguish later between:

- an intentionally excluded empty arena;
- a missed detection;
- a failed crop;
- a missing file.

If empty regions are simply omitted at the beginning, it can become difficult later to determine whether a missing identifier represents an experimental exclusion or a preprocessing error.

---

# 8. Manual coordinate definition

For a stable and simple recording geometry, manual coordinate definition may be entirely adequate.

A practical method is to:

1. display a representative frame;
2. overlay a pixel-coordinate grid;
3. estimate the upper-left and lower-right corners of each assay region;
4. draw the proposed rectangles over the original frame;
5. adjust the coordinates until each region is correctly enclosed.

A rectangular crop can be represented as:

```text
(x1, y1, x2, y2)
```

where:

```text
x1 = left boundary
y1 = top boundary
x2 = right boundary
y2 = bottom boundary
```

The exact coordinate convention used by your software should be checked before implementation.

---

# 9. Automatic arena detection is optional

For regular arena geometries, automatic detection can save substantial time.

For example, circular wells can often be located using circle-detection methods such as the Hough transform.

Other geometries may be more suitable for:

- contour detection;
- template matching;
- edge detection;
- fiducial-marker detection;
- fixed-coordinate templates.

Automatic detection should normally be treated as a way to generate **candidate regions**, not as an unquestioned final decision.

Detection parameters are imaging-system specific.

A threshold or radius range that works for one camera, magnification, or arena may fail after even a moderate change in geometry.

---

# 10. Separate detection from acceptance

A useful design is to separate two operations:

```text
automatic or manual candidate generation
                |
                v
          human review
                |
                v
       accepted coordinates
```

This is particularly important for:

- empty arenas;
- false-positive arena detections;
- partially visible arenas;
- unusual layouts;
- duplicate detections;
- missing detections.

In our development workflow, automatic detection was useful for locating arena boundaries, whereas occupancy and problematic detections were more reliably resolved by visual review.

Users should therefore retain an explicit review step.

---

# 11. Do not infer occupancy only from apparent motion

An animal may remain nearly stationary for substantial periods.

Consequently, little apparent motion does not necessarily mean that an arena is empty.

If occupancy matters, inspect the image or several frames directly.

For difficult cases, reviewing multiple time points or a short video segment is preferable to deciding from a single frame.

---

# 12. Preview crop rectangles before saving them

Before committing crop coordinates, generate a preview image showing:

- the original frame;
- every proposed crop rectangle;
- the corresponding stable region identifier.

Inspect the preview for each recording.

Check that:

- each identifier refers to the intended physical region;
- the complete relevant arena is included;
- neighboring arenas are not accidentally included;
- no crop is shifted;
- no crop is duplicated;
- empty regions are correctly recorded;
- partially visible arenas are recognized;
- crop boundaries do not silently extend outside the image.

A contact sheet containing previews from many recordings can be useful for batch review, but individual images should still be inspected when the overview is ambiguous.

---

# 13. Validate coordinate bounds explicitly

For an image with width `W` and height `H`, a valid rectangular crop should satisfy:

```text
0 <= x1 < x2 <= W
0 <= y1 < y2 <= H
```

Do not rely on the image-processing library to correct invalid coordinates automatically.

This is particularly important in Python/NumPy because negative array indices have valid meanings and may refer to positions counted from the opposite end of an array.

As a result, an unintended negative coordinate may not produce an error. It may instead produce an incorrect crop.

Coordinate validation should therefore occur **before** large-scale video processing.

---

# 14. Arenas at the image boundary

Sometimes an arena lies close to the edge of the camera image.

A nominal crop centered on that arena may then extend beyond the available image.

In that situation, explicitly clip the crop rectangle to the image boundary.

For example:

```text
x1 >= 0
y1 >= 0
x2 <= image width
y2 <= image height
```

Do not allow an array operation to resolve the out-of-range coordinates implicitly.

If clipping removes a substantial part of the assay region, reconsider whether that recording is suitable for analysis.

Minor clipping should still be documented and inspected during downstream tracking quality control.

---

# 15. Crop rectangles do not have to be square

A cropped region does not have to be square unless a particular downstream tool requires square images.

Rectangular regions are acceptable in principle.

Likewise, different recordings can technically have different crop dimensions.

However, consistency is preferable whenever possible.

Changes in:

- magnification;
- image resizing;
- spatial scale;
- arena coverage;
- background area;
- resolution

may affect motion measurements, spatial calibration, or tracking performance.

If crop geometry or image scale changes substantially, consult the recalibration guidance in [`README.md`](README.md).

---

# 16. Avoid resizing unless there is a clear reason

Cropping and resizing are different operations.

Cropping selects a region from the original image.

Resizing changes the pixel representation of that region.

Whenever possible, retain the original pixel scale and avoid resizing cropped videos before AAFR analysis.

Resizing may alter:

- pixel-to-millimeter calibration;
- the numerical scale of image-change measurements;
- object appearance for tracking;
- effective spatial thresholds.

If resizing is unavoidable, relevant parameters should be re-established or verified.

---

# 17. Preserve the original frame rate

The cropped output should ordinarily preserve the frame rate of the input video.

Do not change the frame rate merely as part of cropping.

AAFR uses frame-to-frame image change, so the time interval between consecutive frames affects the motion signal.

A frame-rate change should therefore be treated as a change in imaging conditions and may require reassessment of the motion threshold.

---

# 18. Preserve frame order and duration

Cropping should preserve the temporal sequence of the original recording.

Unless the experimental design specifically requires trimming, a cropped video should contain the corresponding frames from the original recording in the same order.

Check:

- total frame count;
- start and end of recording;
- frame rate;
- playback speed.

If a separate temporal trimming step is required, document it explicitly.

The 10-min interval used in the accompanying AAFR study was a study-specific analysis choice rather than an intrinsic requirement of the AAFR calculation.

---

# 19. Output format

Use a video format that:

- preserves the required image information;
- can be read reliably by the downstream software;
- does not introduce unnecessary compression artifacts;
- preserves frame rate and frame order.

The original workflow used lossless FFV1-encoded AVI files for cropped videos.

This specific codec is not part of the definition of AAFR. Other suitable formats may be used if they are compatible with the subsequent analysis tools and do not materially alter the images.

---

# 20. Keep a machine-readable coordinate record

Do not rely only on screenshots or handwritten notes.

Store the accepted coordinates in a machine-readable format such as CSV or TSV.

A useful structure is:

```text
recording,region_id,x1,y1,x2,y2,occupied
```

Additional useful fields may include:

```text
image_width
image_height
arena_type
plate_id
notes
manual_review_status
```

This coordinate file becomes an important provenance record.

It should be possible to determine later exactly which portion of each raw recording produced each cropped output video.

---

# 21. Keep the coordinate record separate from detection order

If automatic detection is used, distinguish between:

```text
detected object number
```

and:

```text
physical region identifier
```

For example, a detector may report objects:

```text
0, 1, 2, 3, 4, 5
```

but these numbers should not automatically become:

```text
w01, w02, w03, ...
```

Assign physical identifiers according to the actual arena layout.

This prevents region identity from changing when detection order changes between recordings.

---

# 22. Check occupancy independently of geometry

Arena detection and animal occupancy are separate questions.

A circular arena may be detected perfectly even when it contains no animal.

Conversely, an occupied arena may be missed by an imperfect detector.

The workflow should therefore treat:

```text
Where is the arena?
```

and:

```text
Does the arena contain the intended animals?
```

as separate decisions.

---

# 23. Crop a small test set first

Before processing an entire experiment, crop one or a few representative recordings.

Include difficult examples if possible, such as:

- a slightly shifted plate;
- a darker recording;
- an arena close to the image boundary;
- a recording containing an empty region;
- a recording with a different layout.

Inspect these outputs before batch processing.

---

# 24. Inspect the cropped videos directly

Do not assume that correct-looking coordinates guarantee correct video output.

Play several cropped videos.

Confirm that:

- the expected arena is present;
- the stable region identifier is correct;
- both animals are visible when expected;
- the crop does not jump or shift;
- playback speed is normal;
- the full intended recording interval is present;
- no neighboring arena has entered the crop.

A preprocessing script can complete successfully while still producing scientifically incorrect output.

---

# 25. Check basic video metadata after cropping

For representative cropped files, check:

- image width;
- image height;
- frame rate;
- total number of frames;
- duration.

Unexpected differences can reveal:

- incomplete output;
- wrong crop coordinates;
- codec problems;
- frame loss;
- accidental resizing;
- incorrect source-video selection.

---

# 26. Test DeepLabCut before processing the full dataset

Cropping changes the visual input presented to the tracker.

Before tracking all cropped videos, test the DeepLabCut model on a small representative subset.

Inspect:

- coordinate completeness;
- labeled videos;
- placement of the thoracic landmarks;
- identity behavior;
- difficult or overlapping frames.

A model trained on one imaging geometry may require additional labeling or retraining if the new cropped images differ substantially.

See [`SETUP.md`](SETUP.md) for DeepLabCut setup and tracking guidance.

---

# 27. Test the complete AAFR pipeline before batch processing

A successful cropping test is not the end of validation.

Ideally, run at least one recording through the complete workflow:

```text
raw video
    |
    v
cropped video
    |
    +--> ΔI
    |
    +--> tracking --> distance
                    |
                    v
                   AAFR
```

Check that the identifiers used by the two branches match correctly.

Only after this end-to-end test succeeds should the complete dataset be processed.

---

# 28. Keep identifiers consistent across all downstream files

The cropped-video identifier should remain recognizable in later files.

For example:

```text
experiment01_w03.avi
```

might lead to:

```text
experiment01_w03 tracking output
experiment01_w03 distance output
experiment01_w03 ΔI output
experiment01_w03 AAFR result
```

Consistent identifiers greatly reduce the risk of pairing motion data from one arena with tracking data from another.

Avoid unnecessary renaming after cropping.

If renaming is necessary, retain a mapping table.

---

# 29. Relationship between cropping and AAFR calibration

Cropping is not merely a cosmetic operation.

Changes in video geometry can affect downstream quantities.

Relevant examples include:

### Spatial scale

If the image has been resized or camera magnification has changed, the number of pixels corresponding to a given physical distance changes.

The pixel distance threshold should therefore be recalculated from the spatial calibration.

### Image-change measurement

Changes in:

- resolution;
- frame rate;
- illumination;
- segmentation behavior;
- crop geometry;
- background area

may alter the numerical behavior of ΔI.

The motion threshold should therefore be verified or re-established when the imaging configuration changes substantially.

### Tracking

A different crop may alter apparent animal size, contrast, and surrounding visual features.

Tracking performance should be verified before an existing model is reused.

For detailed guidance, see the **Parameters and recalibration** section of [`README.md`](README.md).

---

# 30. Do not normalize away biological differences automatically

Cropping and calibration should correct technical differences in image acquisition, not remove genuine behavioral differences among experimental groups.

For recordings obtained under the same imaging conditions, it is generally preferable to use a common preprocessing and thresholding procedure across experimental groups.

Do not choose separate crop-related normalization rules for each condition merely because their locomotor behavior differs.

---

# 31. Human review is part of the workflow

Automation can reduce repetitive work, but it should not eliminate critical validation steps.

A practical division of labor is:

```text
Computer:
    detect candidate arenas
    draw boundaries
    generate previews
    flag obvious inconsistencies
    crop accepted regions

Human:
    verify physical identity
    identify empty regions
    recognize false detections
    inspect edge cases
    approve coordinates
    inspect representative outputs
```

This hybrid workflow is often more reliable than attempting full automation of every preprocessing decision.

---

# 32. Suggested quality-control checkpoints

A useful cropping pipeline has several explicit checkpoints.

## Checkpoint A — raw video

Confirm:

- expected resolution;
- expected frame rate;
- expected number of assay regions;
- correct experimental recording.

## Checkpoint B — proposed regions

Confirm:

- correct boundaries;
- correct region identifiers;
- correct occupancy;
- no invalid coordinates.

## Checkpoint C — cropped video

Confirm:

- correct arena;
- expected dimensions;
- expected frame rate;
- expected duration;
- no obvious cropping artifact.

## Checkpoint D — tracking

Confirm:

- both animals tracked adequately;
- landmarks placed correctly;
- no major systematic failure.

## Checkpoint E — AAFR input matching

Confirm:

- ΔI and distance files correspond to the same cropped recording;
- identifiers match;
- frame alignment is valid.

---

# 33. Recommended record keeping

For reproducibility, retain:

- the raw video filename;
- the crop coordinate table;
- the physical region identifier;
- occupancy information;
- preview images showing crop boundaries;
- the cropped video filename;
- any exclusions and their reasons.

A simple record of these decisions can save substantial time when data are revisited months later.

---

# 34. Common failure modes

## Wrong physical identifier

**Problem:** Detection order was treated as physical position.

**Prevention:** Assign stable physical region IDs independently of detector order.

---

## Empty arena treated as valid

**Problem:** Arena geometry was detected correctly, but no animals were present.

**Prevention:** Record occupancy separately and inspect questionable regions visually.

---

## Crop extends outside the image

**Problem:** A region lies near the image boundary.

**Prevention:** Validate all coordinates and clip explicitly when appropriate.

---

## Negative coordinates silently generate the wrong crop

**Problem:** Python/NumPy negative indices may be interpreted as positions relative to the end of the image.

**Prevention:** Require all crop coordinates to satisfy explicit image-bound checks before processing.

---

## Cropped video has the wrong region

**Problem:** Coordinates or region IDs were swapped.

**Prevention:** Produce labeled preview images and inspect them before processing.

---

## Tracking quality deteriorates after cropping

**Problem:** The animals appear at a different scale or with different visual context from the tracking-model training data.

**Prevention:** Test representative cropped videos before large-scale tracking.

---

## Motion values change after a new cropping setup

**Problem:** The new recording or crop geometry changes image characteristics.

**Prevention:** Check the recalibration guidance in `README.md` and verify the motion threshold under the new imaging conditions.

---

## Output files cannot be matched downstream

**Problem:** Naming conventions changed between preprocessing stages.

**Prevention:** Use stable identifiers from the moment the assay regions are defined.

---

# 35. What should remain fixed within an experiment when possible

For a given experimental dataset, consistency is desirable in:

- frame rate;
- camera position;
- magnification;
- resolution;
- illumination;
- crop-definition logic;
- spatial calibration;
- naming convention.

Perfect geometric identity among every recording is not always possible, but uncontrolled variation increases both technical noise and the amount of validation required.

---

# 36. When a new cropping procedure should be reconsidered

Revisit the cropping workflow when:

- a new camera is introduced;
- resolution changes;
- magnification changes;
- the assay plate changes;
- arena size changes;
- arena number or layout changes;
- the plate position becomes variable;
- automatic detection begins to fail frequently;
- tracking performance deteriorates;
- image borders cut through assay regions;
- downstream files no longer align correctly.

A new biological strain alone does not normally require a new cropping method if the imaging geometry remains unchanged.

---

# 37. A practical first-time workflow

For a new laboratory or a new imaging system, the following sequence is recommended:

```text
1. Record a few test videos
2. Inspect representative frames
3. Decide on stable physical region identifiers
4. Define or detect candidate crop regions
5. Preview all proposed regions
6. Record occupancy
7. Validate coordinate bounds
8. Crop one test recording
9. Play the cropped videos
10. Check metadata
11. Run DeepLabCut on a small subset
12. Inspect labeled tracking videos
13. Run one recording through ΔI + distance + AAFR
14. Verify identifiers and frame alignment
15. Only then process the complete dataset
```

This sequence generally makes failures easier to diagnose than attempting to automate the entire dataset from the beginning.

---

# 38. Suggested information to provide when asking for help

When asking another researcher, system administrator, or AI assistant to help develop or debug a cropping workflow, provide:

- a representative frame;
- image width and height;
- frame rate;
- arena shape;
- arena count;
- approximate arena arrangement;
- whether positions vary between videos;
- desired physical numbering;
- desired output naming convention;
- the existing coordinate table, if any;
- the complete error message;
- a small example rather than the entire dataset.

For visual problems, an annotated frame is often more informative than a long written explanation.

---

# 39. Minimal checklist before batch cropping

Before starting a large batch, confirm:

- [ ] I know the image resolution.
- [ ] I know the physical arena layout.
- [ ] Each physical region has a stable identifier.
- [ ] Empty regions are recorded explicitly.
- [ ] Candidate crop rectangles have been previewed.
- [ ] All coordinates are within image bounds.
- [ ] No negative coordinates are being used implicitly.
- [ ] Edge clipping has been reviewed.
- [ ] The output frame rate matches the input.
- [ ] A test cropped video has been played manually.
- [ ] DeepLabCut has been tested on representative cropped videos.
- [ ] One recording has successfully passed through the complete AAFR pipeline.
- [ ] I have considered whether the imaging changes require parameter recalibration.

If all of these points are satisfied, batch cropping can proceed with substantially lower risk of silent preprocessing errors.

---

# 40. Scope of this guide

This guide intentionally does not prescribe one universal cropping script.

Video cropping is strongly dependent on the physical assay and imaging configuration, whereas AAFR itself requires only that valid motion and inter-fly distance measurements can be obtained from the same recording.

Users are therefore encouraged to implement the simplest cropping workflow that is appropriate for their system, document the accepted coordinates, verify the output visually, and test the complete downstream pipeline before large-scale analysis.

For installation and software environments, see [`SETUP.md`](SETUP.md).

For AAFR parameters, analysis commands, and recalibration guidance, see [`README.md`](README.md).
