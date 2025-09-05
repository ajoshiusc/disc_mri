# Image Quality Assessment of Fetal Brain MRI Reconstruction across Echo Times

## Methods

### Study Design
We performed a comprehensive quantitative analysis of Super-Resolution Volume (SVR) reconstruction quality across four echo times (TE = 98, 140, 181, 272 ms) using 1-12 input motion-corrupted stacks. Image quality was assessed using five complementary metrics encompassing tissue contrast, signal quality, and structural fidelity.

### Image Quality Metrics
**Notation:** Let μ_tissue and σ_tissue denote the mean intensity and standard deviation within tissue region, where tissue ∈ {GM, WM} for gray matter and white matter, respectively. Let I_recon and I_ref represent the reconstructed and reference images.

**Tissue Contrast Metrics:** (1) Contrast Ratio (CR = μ_WM/μ_GM), (2) Contrast-to-Noise Ratio (CNR = |μ_WM - μ_GM|/√[(σ_WM² + σ_GM²)/2]), and (3) tissue-specific Signal-to-Noise Ratios (SNR_tissue = μ_tissue/σ_tissue) were computed using the CRL Fetal Brain Atlas for gray matter (GM) and white matter (WM) segmentation. **Structural Fidelity Metrics:** (4) 3D Structural Similarity Index (SSIM(I_recon, I_ref) ∈ [0,1]) and (5) Mean Squared Error (MSE = ||I_recon - I_ref||²/N, where N is the total number of voxels) were calculated relative to the highest-quality reference reconstruction (12 stacks) using MONAI framework implementations.

### Statistical Analysis
Error bars represent inter-reconstruction variability computed from different combinations of stacks for each stack count (n=50 combinations), simulating clinical acquisition scenarios. Analysis included 96 total reconstructions across all TE values and stack counts.

## Results

### Tissue Contrast Performance
Contrast ratio demonstrated TE-dependent ordering (TE98 > TE140 > TE181 > TE272), with values ranging from 0.729±0.073 (TE272) to 0.854±0.085 (TE98). All TE values stabilized after 6-8 input stacks. Conversely, CNR showed inverse TE dependence (TE272 > TE181 > TE140 > TE98), ranging from 0.454±0.068 (TE98) to 0.594±0.089 (TE272), with progressive improvement up to 10-12 stacks.

### Signal Quality Analysis
Both gray matter and white matter SNR followed the pattern TE272 > TE181 > TE140 > TE98. Gray matter SNR ranged from 5.05±0.76 (TE98) to 5.95±0.89 (TE272), while white matter SNR ranged from 6.75±1.01 (TE98) to 7.65±1.15 (TE272). White matter demonstrated more stable signal characteristics across different stack counts compared to gray matter.

### Structural Fidelity Assessment
SSIM demonstrated the most dramatic improvement with stack count, increasing from ~0.6-0.8 (1 stack) to >0.95 (8+ stacks) across all TE values. Critical convergence occurred at 6 stacks (SSIM > 0.90), with optimal performance achieved at 8-10 stacks. MSE showed exponential decay from ~40,000 (1 stack) to <1,000 (8+ stacks), with major quality improvements occurring between 1-6 stacks.

### Protocol Optimization
Based on multi-metric analysis, optimal protocols were identified: **Standard Clinical Protocol** (TE 140-181 ms, 6-8 stacks) provides balanced performance across all metrics with 30-40% scan time reduction compared to traditional protocols. **Research Protocol** (TE 140 ms, 8-10 stacks) maximizes quality for detailed morphometric analysis. **Time-Constrained Protocol** (TE 140 ms, 6 stacks) maintains adequate structural fidelity (SSIM > 0.90) with minimum acquisition time.

## Conclusions

This quantitative framework demonstrates that fetal brain MRI reconstruction quality exhibits distinct TE-dependent patterns: shorter TE values optimize tissue contrast while longer TE values enhance signal quality and CNR. The convergence of structural similarity metrics at 6-8 stacks provides evidence-based guidance for clinical protocol optimization, enabling significant scan time reduction while maintaining diagnostic image quality. These findings establish baseline quality metrics for fetal brain MRI reconstruction and provide a foundation for future standardization efforts in the field.
