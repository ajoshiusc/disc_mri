# Image Quality Assessment of Fetal Brain MRI Reconstruction across Echo Times

## Methods

### Study Design
We performed a comprehensive quantitative analysis of Super-Resolution Volume (SVR) reconstruction quality across four echo times (TE = 98, 140, 181, 272 ms) using 1-12 input motion-corrupted stacks. Image quality was assessed using six complementary metrics encompassing tissue contrast, signal quality, and structural fidelity (Figure 1). The CRL Fetal Brain Atlas provided tissue segmentation with labels for gray matter (GM = 1) and white matter (WM = 2).

### Image Quality Metrics
**Notation:** Let μ_tissue and σ_tissue denote the mean intensity and standard deviation within tissue region, where tissue ∈ {GM, WM} for gray matter and white matter, respectively. Let I_recon and I_ref represent the reconstructed and reference images.

**Tissue Contrast Metrics:** (1) Contrast Ratio (CR = μ_WM/μ_GM) quantifies the relative intensity difference between tissue types, (2) Contrast-to-Noise Ratio (CNR = |μ_WM - μ_GM|/√[(σ_WM² + σ_GM²)/2]) measures contrast relative to noise levels, (3) Signal-to-Noise Ratio for gray matter (SNR_GM = μ_GM/σ_GM), and (4) Signal-to-Noise Ratio for white matter (SNR_WM = μ_WM/σ_WM) assess tissue-specific signal quality using the CRL Fetal Brain Atlas [1] for gray matter (GM) and white matter (WM) segmentation. **Structural Fidelity Metrics:** (5) 3D Structural Similarity Index (SSIM(I_recon, I_ref) ∈ [0,1]) evaluates perceptual similarity, and (6) Mean Squared Error (MSE = ||I_recon - I_ref||²/N, where N is the total number of voxels) measures pixel-wise reconstruction accuracy relative to the highest-quality reference reconstruction (12 stacks) using MONAI framework [2] implementations. All six metrics are visualized in Figure 1.

### Statistical Analysis
Error bars represent inter-reconstruction variability computed from different combinations of stacks for each stack count (n=50 combinations), simulating clinical acquisition scenarios where different subsets of motion-corrupted volumes might be selected. This methodology accounts for realistic clinical variation in acquisition circumstances, different stack combinations of the same count, and practical factors including patient motion, acquisition timing, and scanner variation. Analysis included 96 total reconstructions across all TE values and stack counts.

## Results

### Tissue Contrast Performance
Contrast ratio demonstrated TE-dependent ordering (TE98 > TE140 > TE181 > TE272), with values ranging from 0.729±0.073 (TE272) to 0.854±0.085 (TE98). All TE values stabilized after 6-8 input stacks. Conversely, CNR showed inverse TE dependence (TE272 > TE181 > TE140 > TE98), ranging from 0.454±0.068 (TE98) to 0.594±0.089 (TE272), with progressive improvement up to 10-12 stacks. While tissue contrast metrics are recognized as important for fetal brain MRI reconstruction quality assessment, no standardized numerical thresholds exist in the literature for these specific metrics in fetal imaging applications.

### Signal Quality Analysis
Both gray matter and white matter SNR followed the pattern TE272 > TE181 > TE140 > TE98. Gray matter SNR ranged from 5.05±0.76 (TE98) to 5.95±0.89 (TE272), while white matter SNR ranged from 6.75±1.01 (TE98) to 7.65±1.15 (TE272). White matter demonstrated more stable signal characteristics across different stack counts compared to gray matter. All observed SNR values exceeded general guidance from quantitative MRI literature, where Tofts [5] suggests minimum SNR of 3-5 for adequate diagnostic imaging, though fetal brain MRI-specific thresholds remain unstandardized. While Dietrich et al. [4] provide comprehensive SNR measurement methodology, they focus on technical measurement aspects rather than establishing diagnostic thresholds.

### Structural Fidelity Assessment
SSIM demonstrated the most dramatic improvement with stack count, increasing from ~0.6-0.8 (1 stack) to >0.95 (8+ stacks) across all TE values. Critical convergence occurred at 6 stacks (SSIM > 0.90), where Wang et al. [3] established that SSIM > 0.9 indicates "excellent" image quality for natural images, though medical image thresholds remain unstandardized. Optimal performance was achieved at 8-10 stacks. MSE showed exponential decay from ~40,000 (1 stack) to <1,000 (8+ stacks), with major quality improvements occurring between 1-6 stacks. All TE values demonstrated convergence to similar endpoint values, indicating robust reconstruction performance. For MSE, no universal thresholds exist in the literature as values are highly dependent on image intensity ranges and specific reconstruction parameters.

### Protocol Optimization
Based on multi-metric analysis, optimal protocols were identified: **Standard Clinical Protocol** (TE 140-181 ms, 6-8 stacks) provides balanced performance across all metrics with substantial scan time reduction (30-40% compared to traditional 10-12 stack protocols). **Research Protocol** (TE 140 ms, 8-10 stacks) maximizes quality for detailed morphometric analysis. **Time-Constrained Protocol** (TE 140 ms, 6 stacks) maintains adequate structural fidelity (SSIM > 0.90) with minimum acquisition time while preserving diagnostic quality.

## Conclusions

This quantitative framework demonstrates that fetal brain MRI reconstruction quality exhibits distinct TE-dependent patterns: shorter TE values optimize tissue contrast while longer TE values enhance signal quality and CNR. The convergence of structural similarity metrics at 6-8 stacks provides evidence-based guidance for clinical protocol optimization, enabling significant scan time reduction while maintaining diagnostic image quality. These findings establish baseline quality metrics for fetal brain MRI reconstruction and provide a foundation for future standardization efforts in the field.

**Methodological Note:** The observed numerical ranges are specific to this dataset and reconstruction methodology. While some metrics have established guidance in the broader imaging literature—such as SSIM > 0.9 for "excellent" quality in natural images [3], and general SNR recommendations of 3-5 for diagnostic MRI [5]—fetal brain MRI-specific quality thresholds remain unstandardized. The metrics and ranges presented provide baseline observational data for future validation studies and standardization efforts in fetal neuroimaging.

## Figure

**Figure 1.** Image quality assessment across different echo times (TE = 98, 140, 181, 272 ms) for fetal brain MRI Super-Resolution Volume reconstruction. Six complementary metrics demonstrate distinct TE-dependent patterns: (A) Contrast Ratio shows decreasing trend with longer TE, (B) Contrast-to-Noise Ratio shows increasing trend with longer TE, (C,D) Signal-to-Noise Ratios for gray and white matter both increase with longer TE, (E) Structural Similarity Index shows convergence across TE values at 6-8 stacks, and (F) Mean Squared Error demonstrates exponential decay with increasing stack count. Error bars represent inter-reconstruction variability across different stack combinations (n=50 combinations per data point). All metrics stabilize at 6-8 input stacks, supporting protocol optimization for clinical efficiency.

*Figure file: figure_quality_assessment.pdf (vector format) or figure_quality_assessment.png (300 DPI)*

## References

[1] Gholipour A, Rollins CK, Velasco-Annis C, et al. A normative spatiotemporal MRI atlas of the fetal brain for automatic segmentation and analysis of early brain growth. Scientific Reports. 2017;7(1):476.

[2] Cardoso MJ, Li W, Brown R, et al. MONAI: An open-source framework for deep learning in healthcare. arXiv preprint arXiv:2211.02701. 2022.

[3] Wang Z, Bovik AC, Sheikh HR, Simoncelli EP. Image quality assessment: from error visibility to structural similarity. IEEE Transactions on Image Processing. 2004;13(4):600-612.

[4] Dietrich O, Raya JG, Reeder SB, et al. Measurement of signal-to-noise ratios in MR images: influence of multichannel coils, parallel imaging, and reconstruction filters. Journal of Magnetic Resonance Imaging. 2007;26(2):375-385.

[5] Tofts PS. Quantitative MRI of the Brain: Measuring Changes Caused by Disease. John Wiley & Sons, 2003.
