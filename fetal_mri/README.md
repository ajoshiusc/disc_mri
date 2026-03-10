# Fetal MRI Publication Figure Generation Pipeline

This document outlines the sequence of Python scripts executed to generate the final publication-quality figure (`publication_figure_x_preserved.pdf`) from raw DICOM images.

## 1. Data Conversion (DICOM to NIfTI)
First, raw DICOMs are converted to NIFTI format for processing. This is done within each scan's specific directory (e.g., `scan_10_23_2025/`).
*   **Script:** `[scan_directory]/main_convert_dicomms_to_nifti.py`

## 2. Stack Orientation / Pre-processing
Once you have the NIfTI stacks, they need to be oriented properly so that the slice direction aligns with the main axes (Z, Y, or X) prior to reconstruction.
*   **Script:** `[scan_directory]/main_rotate2makeslice_z.py` (and/or x/y equivalents if needed)

## 3. Slice-Volume Reconstruction (SVR)
The aligned NIfTI stacks are fed into the Apptainer-based Slice-To-Volume Reconstruction pipeline to generate high-resolution volumes at different Echo Times (TE) and stack counts.
*   **Scripts:** `[scan_directory]/main_svr_process_te98_apptainer.py`, `...te140_apptainer.py`, `...te181_apptainer.py`, `...te272_apptainer.py` 

## 4. Image Quality Analysis
Once reconstructions exist for all combinations of TE and stack numbers (1 to 12), the comprehensive analysis script evaluates the metrics (Contrast Ratio, CNR, SSIM, MSE, SNR).
*   **Script:** `comprehensive_te_analysis.py` 
*   **Output:** Generates `comprehensive_te_analysis_results.txt` containing the raw metric measurements.

## 5. Statistical Variance Calculation
This script takes the measured metrics and performs legitimate statistical measurements (using multiple reconstruction combinations) to create accurate error bars, rather than using estimated variants.
*   **Script:** `generate_real_error_bars.py`
*   **Output:** Generates `real_error_bar_data.json`

## 6. Publication Figure Generation
Finally, the plotting script reads the calculated statistics from the json file to produce the publication-quality visualization with the updated, highly-accurate error margins.
*   **Script:** `generate_publication_figure_preserved.py`
*   **Output:** Generates the final `publication_figure_x_preserved.pdf` (and the corresponding `.png`).