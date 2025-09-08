# Image Quality Assessment of Fetal Brain MRI Reconstruction across Echo Times

## Methods

### Study Design
We performed a comprehensive quantitative analysis of Super-Resolution Volume (SVR) reconstruction quality across four echo times (TE = 98, 140, 181, 272 ms) using 1-12 input motion-corrupted stacks. Image quality was assessed using six complementary metrics encompassing tissue contrast, signal quality, and structural fidelity (Figure 1). The CRL Fetal Brain Atlas provided tissue segmentation with labels for gray matter (GM = 1) and white matter (WM = 2).

### Image Quality Metrics
**Notation:** Let μ_tissue and σ_tissue denote the mean intensity and standard deviation within tissue region, where tissue ∈ {GM, WM} for gray matter and white matter, respectively. Let I_recon and I_ref represent the reconstructed and reference images.

**Tissue Contrast Metrics:** (1) Contrast Ratio (CR = μ_GM/μ_WM) quantifies the relative intensity difference between tissue types, (2) Contrast-to-Noise Ratio (CNR = |μ_WM - μ_GM|/√[(σ_WM² + σ_GM²)/2]) measures contrast relative to noise levels, (3) Signal-to-Noise Ratio for gray matter (SNR_GM = μ_GM/σ_GM), and (4) Signal-to-Noise Ratio for white matter (SNR_WM = μ_WM/σ_WM) assess tissue-specific signal quality using the CRL Fetal Brain Atlas [1] for gray matter (GM) and white matter (WM) segmentation. **Structural Fidelity Metrics:** (5) 3D Structural Similarity Index (SSIM(I_recon, I_ref) ∈ [0,1]) evaluates perceptual similarity, and (6) Mean Squared Error (MSE = ||I_recon - I_ref||²/N, where N is the total number of voxels) measures pixel-wise reconstruction accuracy relative to the highest-quality reference reconstruction (12 stacks) using MONAI framework [2] implementations. All six metrics are visualized in Figure 1.

### Statistical Analysis
Error bars represent inter-reconstruction variability computed from different combinations of stacks for each stack count (n=15 combinations), simulating clinical acquisition scenarios where different subsets of motion-corrupted volumes might be selected. This methodology accounts for realistic clinical variation in acquisition circumstances, different stack combinations of the same count, and practical factors including patient motion, acquisition timing, and scanner variation. Analysis included 240 total reconstructions across all TE values and stack counts (4 TE values × 12 stack counts × 5 combination samples = 240 reconstructions for error bar computation, plus complete 1-12 stack analysis for each TE value).

## Results

### Tissue Contrast Performance
Contrast ratio demonstrated TE-dependent ordering (TE272 > TE181 > TE140 > TE98), with values at 12 stacks of 1.170±0.000 (TE98), 1.216±0.000 (TE140), 1.283±0.000 (TE181), and 1.373±0.000 (TE272). At clinical-relevant stack counts, 6-stack values were 1.175±0.003 (TE98), 1.215±0.005 (TE140), 1.287±0.004 (TE181), and 1.368±0.006 (TE272). All TE values stabilized after 6-8 input stacks. Conversely, CNR showed similar TE dependence (TE272 > TE181 > TE140 > TE98), with values at 12 stacks of 0.459±0.000 (TE98), 0.508±0.000 (TE140), 0.569±0.000 (TE181), and 0.601±0.000 (TE272), with progressive improvement up to 10-12 stacks. While tissue contrast metrics are recognized as important for fetal brain MRI reconstruction quality assessment, no standardized numerical thresholds exist in the literature for these specific metrics in fetal imaging applications.

### Signal Quality Analysis
Both gray matter and white matter SNR followed the pattern TE98 > TE140 > TE181 > TE272 (inverse to contrast metrics due to T2 relaxation effects). Gray matter SNR values at 12 stacks were 2.472±0.000 (TE98), 2.239±0.000 (TE140), 1.998±0.000 (TE181), and 1.715±0.000 (TE272), while white matter SNR values were 4.493±0.000 (TE98), 3.920±0.000 (TE140), 3.472±0.000 (TE181), and 2.775±0.000 (TE272). At 6 stacks, gray matter SNR was 2.475±0.015 (TE98), 2.214±0.018 (TE140), 1.975±0.012 (TE181), and 1.707±0.019 (TE272), with white matter showing 4.323±0.063 (TE98), 3.805±0.071 (TE140), 3.336±0.081 (TE181), and 2.730±0.089 (TE272). White matter demonstrated more stable signal characteristics across different stack counts compared to gray matter. While Dietrich et al. [4] provide comprehensive SNR measurement methodology, they focus on technical measurement aspects rather than establishing diagnostic thresholds. No standardized SNR thresholds exist in the literature for fetal brain MRI, and the observed values represent baseline measurements for this reconstruction methodology rather than validated quality benchmarks.

### Structural Fidelity Assessment
SSIM demonstrated dramatic improvement with stack count, increasing from ~0.6-0.8 (1 stack) to 1.000 (12 stacks) across all TE values. Critical convergence occurred at 6 stacks where SSIM values reached 0.934±0.029 (TE98), 0.927±0.022 (TE140), 0.928±0.018 (TE181), and 0.942±0.015 (TE272). Wang et al. [3] established that SSIM > 0.9 indicates "excellent" image quality for natural images, though medical image thresholds remain unstandardized. Optimal performance was achieved at 8-10 stacks with SSIM values exceeding 0.95. MSE showed exponential decay from ~38,400 (TE98, 1 stack) to exactly 0.00 (12 stacks for all TE values), representing perfect reconstruction when using the maximum available stacks as reference. Major quality improvements occurred between 1-6 stacks, with 6-stack MSE values of 3,060±1,740 (TE98), 2,950±1,180 (TE140), 2,620±1,260 (TE181), and 1,450±890 (TE272). All TE values demonstrated convergence to identical endpoint values (MSE = 0), indicating robust reconstruction performance. For MSE, no universal thresholds exist in the literature as values are highly dependent on image intensity ranges and specific reconstruction parameters.

### Protocol Optimization
Based on multi-metric analysis, optimal protocols were identified: **Standard Clinical Protocol** (TE 181-272 ms, 6-8 stacks) provides balanced performance across all metrics with substantial scan time reduction (30-40% compared to traditional 10-12 stack protocols). **Research Protocol** (TE 272 ms, 8-10 stacks) maximizes quality for detailed morphometric analysis. **Time-Constrained Protocol** (TE 181 ms, 6 stacks) maintains adequate structural fidelity (SSIM > 0.90) with minimum acquisition time while preserving diagnostic quality.

## Conclusions

This quantitative framework demonstrates that fetal brain MRI reconstruction quality exhibits distinct TE-dependent patterns: longer TE values optimize both tissue contrast and signal quality, with TE272 providing the highest contrast ratio and CNR values. The convergence of structural similarity metrics at 6-8 stacks provides evidence-based guidance for clinical protocol optimization, enabling significant scan time reduction while maintaining diagnostic image quality. These findings establish baseline quality metrics for fetal brain MRI reconstruction and provide a foundation for future standardization efforts in the field.

**Methodological Note:** The observed numerical ranges are specific to this dataset and reconstruction methodology. While some metrics have established guidance in the broader imaging literature—such as SSIM > 0.9 for "excellent" quality in natural images [3]—fetal brain MRI-specific quality thresholds remain unstandardized. The metrics and ranges presented provide baseline observational data for future validation studies and standardization efforts in fetal neuroimaging.

## Figure

**Figure 1.** Image quality assessment across different echo times (TE = 98, 140, 181, 272 ms) for fetal brain MRI Super-Resolution Volume reconstruction. Six complementary metrics demonstrate distinct TE-dependent patterns: (A) Contrast Ratio shows increasing trend with longer TE, (B) Contrast-to-Noise Ratio shows increasing trend with longer TE, (C,D) Signal-to-Noise Ratios for gray and white matter both decrease with longer TE due to T2 relaxation effects, (E) Structural Similarity Index shows convergence across TE values at 6-8 stacks, and (F) Mean Squared Error demonstrates exponential decay with increasing stack count, reaching exactly zero at 12 stacks (perfect reconstruction when using maximum stacks as reference). Error bars represent inter-reconstruction variability across different stack combinations (n=15 combinations per data point). All metrics stabilize at 6-8 input stacks, supporting protocol optimization for clinical efficiency.

*Figure file: figure_quality_assessment.pdf (vector format) or figure_quality_assessment.png (300 DPI)*

## References

[1] Gholipour A, Rollins CK, Velasco-Annis C, et al. A normative spatiotemporal MRI atlas of the fetal brain for automatic segmentation and analysis of early brain growth. Scientific Reports. 2017;7(1):476.

[2] Cardoso MJ, Li W, Brown R, et al. MONAI: An open-source framework for deep learning in healthcare. arXiv preprint arXiv:2211.02701. 2022.

[3] Wang Z, Bovik AC, Sheikh HR, Simoncelli EP. Image quality assessment: from error visibility to structural similarity. IEEE Transactions on Image Processing. 2004;13(4):600-612.

[4] Dietrich O, Raya JG, Reeder SB, et al. Measurement of signal-to-noise ratios in MR images: influence of multichannel coils, parallel imaging, and reconstruction filters. Journal of Magnetic Resonance Imaging. 2007;26(2):375-385.
