# Fetal MRI Image Quality Analysis: Key Findings
## Impact of TE and Stack Count on Reconstruction Quality

---

## Slide 1: Study Overview

### Objective
- Quantify the impact of **Echo Time (TE)** and **number of stacks** on fetal MRI reconstruction quality
- Optimize acquisition parameters for super-resolution volume reconstruction (SVR)

### Methods
- **TE values tested**: 98, 140, 181, 272 ms
- **Stack counts**: 1-12 stacks per TE
- **Metrics evaluated**: 
  - Tissue contrast (CR, CNR, SNR)
  - Structural similarity (SSIM, MSE)
- **Atlas-based analysis**: CRL Fetal Brain Atlas 2017v3 (STA30)

---

## Slide 2: Tissue Contrast Findings

### Key Results
- **Optimal TE for contrast**: **272 ms** shows highest CNR (0.60 ± 0.01)
- **Diminishing returns**: CNR plateaus after 6-8 stacks
- **TE-dependent trends**:
  - Short TE (98 ms): CR = 0.85, moderate CNR (0.45)
  - Long TE (272 ms): CR = 0.73, highest CNR (0.59)

### Clinical Impact
- Longer TE improves tissue differentiation
- Minimal benefit beyond 8 stacks for contrast metrics

---

## Slide 3: Structural Similarity Analysis

### Key Results
- **SSIM improvement**: Exponential increase with stack count
- **Reference comparison**: 12-stack reconstruction as gold standard
- **TE performance**:
  - TE 98 ms: Better structural preservation at low stack counts
  - TE 272 ms: Requires more stacks for equivalent SSIM

### Quality Thresholds
- **Acceptable quality**: SSIM > 0.90 (≥6 stacks)
- **High quality**: SSIM > 0.95 (≥8 stacks)
- **Reference quality**: SSIM > 0.98 (≥10 stacks)

---

## Slide 4: Reconstruction Fidelity (MSE)

### Key Results
- **MSE reduction**: Exponential decrease with more stacks
- **Convergence point**: 8-10 stacks for most TEs
- **TE-dependent patterns**:
  - All TEs converge to similar MSE with sufficient stacks
  - Initial MSE varies significantly (1.25×10⁴ to 3.84×10⁴)

### Practical Implications
- Reconstruction error stabilizes after 8 stacks
- Acquisition time vs. quality trade-off

---

## Slide 5: SNR Analysis Across TEs

### Gray Matter SNR
- **TE 98 ms**: Highest SNR (2.47 ± 0.04)
- **TE 272 ms**: Lowest SNR (1.71 ± 0.02)
- **Trend**: Inverse relationship with TE

### White Matter SNR
- **TE 98 ms**: Highest SNR (4.49 ± 0.09)
- **TE 272 ms**: Lowest SNR (2.77 ± 0.14)
- **Pattern**: Similar TE-dependent decline

### Clinical Relevance
- Short TE preserves signal strength
- Long TE enhances contrast at SNR cost

---

## Slide 6: Optimal Parameter Selection

### Balanced Approach: **TE 181 ms**
- **Good contrast**: CNR = 0.57 ± 0.02
- **Preserved SNR**: GM = 1.99, WM = 3.43
- **Structural fidelity**: SSIM > 0.95 with 8 stacks

### Clinical Recommendations
1. **Standard protocol**: TE 181 ms, 8 stacks
2. **High contrast needs**: TE 272 ms, 10 stacks
3. **Time-critical cases**: TE 140 ms, 6 stacks

---

## Slide 7: Statistical Significance

### Error Bar Analysis
- **Stack combination variability**: Assessed for 3, 6, 9, 12 stacks
- **Consistent trends**: All metrics show similar patterns across combinations
- **Statistical robustness**: Error bars indicate reliable measurements

### Quality Assurance
- Multiple stack combinations validate findings
- Reproducible results across different acquisition strategies

---

## Slide 8: Clinical Translation

### Acquisition Time Optimization
- **Current practice**: Often uses 12+ stacks
- **Recommended**: 8 stacks provides 95% of quality benefit
- **Time saving**: ~33% reduction in scan time

### Quality-Time Trade-offs
| Stack Count | Scan Time | SSIM | CNR | Clinical Use |
|-------------|-----------|------|-----|--------------|
| 6 | 100% | 0.93 | 0.95 | Emergency/motion |
| 8 | 133% | 0.95 | 0.98 | Standard protocol |
| 12 | 200% | 1.00 | 1.00 | Research/complex cases |

---

## Slide 9: Future Directions

### Technical Improvements
- **Motion correction**: Further reduce required stacks
- **Advanced reconstruction**: AI-enhanced SVR
- **Real-time optimization**: Adaptive TE selection

### Clinical Applications
- **Gestational age studies**: Optimize for different developmental stages
- **Pathology detection**: TE selection for specific conditions
- **Multi-center protocols**: Standardized acquisition parameters

---

## Slide 10: Conclusions

### Key Takeaways
1. **TE 181 ms** provides optimal balance of contrast and SNR
2. **8 stacks** offer excellent quality-time compromise
3. **Exponential improvement** with stack count up to 8-10
4. **Diminishing returns** beyond 10 stacks for most metrics

### Clinical Impact
- **33% time reduction** possible while maintaining quality
- **Standardized protocols** for fetal MRI centers
- **Evidence-based** parameter selection for SVR reconstruction

---

*Analysis based on comprehensive evaluation of tissue contrast, structural similarity, and reconstruction fidelity metrics using CRL Fetal Brain Atlas 2017v3*
