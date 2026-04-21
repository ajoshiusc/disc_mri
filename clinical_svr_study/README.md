# Clinical SVR Paper Draft

This folder contains an Overleaf-ready manuscript draft plus the reproducibility code needed to regenerate the manuscript tables and figure source files from `SVR2.xlsx`.

## Files

- `main.tex`: manuscript draft in LaTeX
- `references.bib`: bibliography used by the draft
- `analysis/generate_results.py`: reproduces the workbook-derived results
- `outputs/`: generated CSV, JSON, and LaTeX table snippets consumed by `main.tex`

## Reproduce The Results

Run the analysis script with the bundled Python runtime or any Python 3 environment that has `openpyxl`:

```bash
python3 analysis/generate_results.py --xlsx /absolute/path/to/SVR2.xlsx --outdir outputs
```

For this session, the workbook used was:

```text
/Users/ajoshi/Downloads/SVR2.xlsx
```

## What The Script Reproduces

The script will:

1. Parse the raw-stack reads and SVR reads from the Excel workbook.
2. Recover the blinded SVR-to-original case mapping from the study repository randomization permutation.
3. Generate:
   - paired case tables
   - summary statistics
   - diagnostic concordance summaries
   - figure source CSV files
   - LaTeX table snippets used by the manuscript

## Upstream Reconstruction Pipeline

The workbook-level reproducibility above is fully covered by this folder.

The upstream SVR image-generation workflow came from the study repository:

`https://github.com/ajoshiusc/disc_mri/tree/main/clinical_svr_study`

From the repository inspection, the image pipeline was:

1. Convert zipped DICOM studies to NIfTI with `dcm2niix`.
2. Select fetal brain TSE acquisitions (`*BRAIN*TSE*`).
3. Reorient stacks so the slice axis is consistent.
4. Apply manually curated brain masks.
5. Run MIRTK reconstruction at 1 mm isotropic resolution.
6. Rigidly align the reconstructed volume to the fetal atlas with FSL `flirt`.
7. Convert to canonical orientation.
8. Convert the aligned NIfTI volume back to DICOM with the custom `nii2dcm` code.
9. Randomize the SVR case identifiers for blinded radiologist review.

Re-running that upstream imaging pipeline requires the original DICOM ZIP archives plus MIRTK/FSL and the repository environment, which are not included in this folder.

## Notes To Verify Before Submission

- Verify the spelling, credentials, and affiliation formatting for `Jesus Urib` if needed.
- Insert the exact first-author list, affiliations, IRB language, scanner details, gestational age range, and reading-session logistics.
- The workbook does not provide a ground-truth adjudication standard, so the manuscript frames the diagnosis comparison as agreement rather than diagnostic accuracy.
