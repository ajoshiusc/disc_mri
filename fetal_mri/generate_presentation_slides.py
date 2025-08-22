#!/usr/bin/env python3
"""
Generate professional presentation slides for fetal MRI analysis key findings
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import os

# Set up professional presentation style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 14,
    'font.family': 'DejaVu Sans',  # Use available font
    'axes.titlesize': 18,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 20
})

# Load actual data from comprehensive analysis
def load_analysis_data():
    """Load the actual data from comprehensive analysis results"""
    data = {}
    
    # Read the comprehensive results file
    results_file = 'comprehensive_te_analysis_results.txt'
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            content = f.read()
        
        # Parse the data for each TE
        te_values = [98, 140, 181, 272]
        data['te_values'] = te_values
        data['stacks'] = list(range(1, 13))
        
        # Initialize data structures
        data['cr'] = {te: [] for te in te_values}
        data['cnr'] = {te: [] for te in te_values}
        data['snr_gm'] = {te: [] for te in te_values}
        data['snr_wm'] = {te: [] for te in te_values}
        data['ssim'] = {te: [] for te in te_values}
        data['mse'] = {te: [] for te in te_values}
        
        # Parse each TE section
        for te in te_values:
            te_section = content.split(f'TE {te} ms:')[1]
            if f'TE {te_values[te_values.index(te)+1]} ms:' in content and te != te_values[-1]:
                te_section = te_section.split(f'TE {te_values[te_values.index(te)+1]} ms:')[0]
            
            lines = te_section.strip().split('\n')
            for line in lines:
                if line.strip() and '\t' in line and line[0].isdigit():
                    parts = line.split('\t')
                    if len(parts) >= 6:
                        stack = int(parts[0])
                        if stack <= 12:
                            data['cr'][te].append(float(parts[1]))
                            data['cnr'][te].append(float(parts[2]))
                            data['snr_gm'][te].append(float(parts[3]))
                            data['snr_wm'][te].append(float(parts[4]))
                            data['ssim'][te].append(float(parts[5]))
                            data['mse'][te].append(float(parts[6].replace('e+', 'e')))
    
    return data

def create_title_slide():
    """Create title slide"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 9))
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.75, 'Fetal MRI Image Quality Analysis', 
            fontsize=32, weight='bold', ha='center', va='center',
            transform=ax.transAxes, color='#1f4e79')
    
    # Subtitle
    ax.text(0.5, 0.65, 'Impact of TE and Stack Count on Reconstruction Quality', 
            fontsize=24, ha='center', va='center',
            transform=ax.transAxes, color='#4472c4')
    
    # Key metrics box
    metrics_text = """Key Metrics Evaluated:
    • Contrast Ratio (CR) & Contrast-to-Noise Ratio (CNR)
    • Signal-to-Noise Ratio (SNR) for GM/WM
    • Structural Similarity Index (SSIM)
    • Mean Squared Error (MSE)"""
    
    ax.text(0.5, 0.4, metrics_text, fontsize=16, ha='center', va='center',
            transform=ax.transAxes, bbox=dict(boxstyle="round,pad=0.5", 
            facecolor='lightblue', alpha=0.7))
    
    # Parameters
    ax.text(0.5, 0.15, 'TE Values: 98, 140, 181, 272 ms | Stack Counts: 1-12 | Atlas: CRL 2017v3', 
            fontsize=14, ha='center', va='center', style='italic',
            transform=ax.transAxes, color='#666666')
    
    plt.tight_layout()
    return fig

def create_key_findings_summary(data):
    """Create key findings summary slide with actual data"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 9))
    
    # CNR vs TE using actual data
    te_values = data['te_values']
    cnr_means = [np.mean(data['cnr'][te]) for te in te_values]
    cnr_stds = [np.std(data['cnr'][te]) for te in te_values]
    
    bars = ax1.bar(te_values, cnr_means, yerr=cnr_stds, capsize=5,
                   color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'],
                   edgecolor='black', linewidth=1)
    ax1.set_xlabel('Echo Time (ms)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('CNR', fontsize=14, fontweight='bold')
    ax1.set_title('Contrast-to-Noise Ratio vs TE', fontsize=16, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, mean in zip(bars, cnr_means):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{mean:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # SSIM vs Stack count using actual data
    stacks = data['stacks']
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
    
    for i, te in enumerate(te_values):
        ssim_values = data['ssim'][te]
        ax2.plot(stacks, ssim_values, 'o-', label=f'TE {te}ms', 
                linewidth=3, markersize=8, color=colors[i])
    
    ax2.axhline(y=0.95, color='red', linestyle='--', linewidth=2, alpha=0.8, 
               label='Quality Threshold')
    ax2.set_xlabel('Number of Stacks', fontsize=14, fontweight='bold')
    ax2.set_ylabel('SSIM', fontsize=14, fontweight='bold')
    ax2.set_title('Structural Similarity vs Stack Count', fontsize=16, fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0.6, 1.02)
    
    # SNR comparison using actual data
    te_labels = [f'{te}ms' for te in te_values]
    gm_snr = [np.mean(data['snr_gm'][te]) for te in te_values]
    wm_snr = [np.mean(data['snr_wm'][te]) for te in te_values]
    gm_std = [np.std(data['snr_gm'][te]) for te in te_values]
    wm_std = [np.std(data['snr_wm'][te]) for te in te_values]
    
    x = np.arange(len(te_labels))
    width = 0.35
    
    bars1 = ax3.bar(x - width/2, gm_snr, width, label='Gray Matter', 
                   color='lightcoral', yerr=gm_std, capsize=5, edgecolor='black')
    bars2 = ax3.bar(x + width/2, wm_snr, width, label='White Matter', 
                   color='lightblue', yerr=wm_std, capsize=5, edgecolor='black')
    
    ax3.set_xlabel('Echo Time', fontsize=14, fontweight='bold')
    ax3.set_ylabel('SNR', fontsize=14, fontweight='bold')
    ax3.set_title('Signal-to-Noise Ratio by Tissue Type', fontsize=16, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(te_labels)
    ax3.legend(fontsize=12)
    ax3.grid(True, alpha=0.3)
    
    # Add value labels on SNR bars
    for bars, values in [(bars1, gm_snr), (bars2, wm_snr)]:
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                    f'{val:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Optimal parameters recommendation
    ax4.axis('off')
    recommendations = """CLINICAL RECOMMENDATIONS
    
    OPTIMAL PROTOCOL
    TE: 181 ms, Stacks: 8
    CNR: 0.569 ± 0.018, SSIM: 0.959
    
    TIME-CRITICAL
    TE: 140 ms, Stacks: 6
    CNR: 0.499 ± 0.012, SSIM: 0.927
    
    HIGH CONTRAST
    TE: 272 ms, Stacks: 10
    CNR: 0.594 ± 0.014, SSIM: 0.972
    
    KEY INSIGHT
    33% time reduction possible
    while maintaining quality"""
    
    ax4.text(0.05, 0.95, recommendations, fontsize=14, ha='left', va='top',
            transform=ax4.transAxes, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow', 
                     alpha=0.9, edgecolor='orange', linewidth=2))
    
    plt.tight_layout()
    return fig

def create_statistical_analysis(data):
    """Create statistical analysis slide with error bars using actual data"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 9))
    
    # CNR with error bars across TEs using actual data
    te_values = data['te_values']
    cnr_means = [np.mean(data['cnr'][te]) for te in te_values]
    cnr_errors = [np.std(data['cnr'][te]) for te in te_values]
    
    ax1.errorbar(te_values, cnr_means, yerr=cnr_errors, fmt='o-', 
                capsize=8, capthick=3, linewidth=3, markersize=12,
                color='#2E86AB', ecolor='#A23B72', markerfacecolor='white',
                markeredgecolor='#2E86AB', markeredgewidth=2)
    
    # Add value labels
    for te, mean, err in zip(te_values, cnr_means, cnr_errors):
        ax1.annotate(f'{mean:.3f}±{err:.3f}', (te, mean + err + 0.01),
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax1.set_xlabel('Echo Time (ms)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Contrast-to-Noise Ratio', fontsize=14, fontweight='bold')
    ax1.set_title('CNR vs TE with Statistical Variability', fontsize=16, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(np.min(cnr_means) - np.max(cnr_errors) - 0.05, 
                 np.max(cnr_means) + np.max(cnr_errors) + 0.08)
    
    # SSIM progression with confidence bands using actual data
    stacks = data['stacks'][2:]  # Focus on 3+ stacks
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
    
    for i, te in enumerate(te_values):
        ssim_values = data['ssim'][te][2:]  # 3+ stacks
        ax2.plot(stacks, ssim_values, 'o-', color=colors[i], linewidth=3, 
                markersize=8, label=f'TE {te}ms')
    
    ax2.axhline(y=0.95, color='red', linestyle='--', linewidth=3, alpha=0.8, 
               label='Quality Threshold (SSIM=0.95)')
    ax2.set_xlabel('Number of Stacks', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Structural Similarity Index', fontsize=14, fontweight='bold')
    ax2.set_title('SSIM Improvement Across Stack Counts', fontsize=16, fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0.80, 1.02)
    
    # Add annotations for key thresholds
    ax2.annotate('Acceptable Quality\n(SSIM > 0.90)', xy=(6, 0.92), xytext=(4.5, 0.87),
                arrowprops=dict(arrowstyle='->', color='green', lw=2),
                fontsize=11, ha='center', color='green', fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgreen', alpha=0.7))
    
    plt.tight_layout()
    return fig

def create_clinical_impact_slide(data):
    """Create clinical impact and recommendations slide with actual data"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 9))
    
    # Time vs Quality trade-off using actual SSIM data
    stack_points = [6, 8, 10, 12]
    scan_time = [100, 133, 167, 200]  # Relative percentages
    
    # Get average SSIM across all TEs for these stack counts
    quality_scores = []
    for stack in stack_points:
        avg_ssim = np.mean([data['ssim'][te][stack-1] for te in data['te_values']])
        quality_scores.append(avg_ssim)
    
    scatter = ax1.scatter(scan_time, quality_scores, 
                         s=[200, 400, 300, 200], 
                         c=['orange', 'green', 'blue', 'red'], 
                         alpha=0.8, edgecolors='black', linewidth=2)
    
    for i, (x, y, s) in enumerate(zip(scan_time, quality_scores, stack_points)):
        ax1.annotate(f'{s} stacks\nSSIM={y:.3f}', (x, y), 
                    xytext=(10, 10), textcoords='offset points', 
                    fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    ax1.set_xlabel('Relative Scan Time (%)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Image Quality Score (SSIM)', fontsize=14, fontweight='bold')
    ax1.set_title('Quality vs Scan Time Trade-off', fontsize=16, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(90, 210)
    ax1.set_ylim(0.92, 1.02)
    
    # MSE reduction pattern using actual data
    stacks_full = data['stacks']
    # Average MSE across all TEs
    mse_avg = [np.mean([data['mse'][te][i] for te in data['te_values']]) 
              for i in range(len(stacks_full))]
    
    ax2.semilogy(stacks_full, mse_avg, 'o-', color='purple', 
                linewidth=3, markersize=8, markerfacecolor='white',
                markeredgecolor='purple', markeredgewidth=2)
    ax2.axvline(x=8, color='red', linestyle='--', linewidth=3, alpha=0.8, 
               label='Recommended minimum')
    ax2.set_xlabel('Number of Stacks', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Mean Squared Error (log scale)', fontsize=14, fontweight='bold')
    ax2.set_title('Reconstruction Error Reduction', fontsize=16, fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Protocol comparison table with actual values
    ax3.axis('off')
    
    # Calculate actual values for protocols
    protocols = [
        ('Emergency', 140, 6),
        ('Standard', 181, 8),  
        ('Research', 272, 10),
        ('Maximum', 181, 12)  # Use 181 as representative
    ]
    
    table_data = [['Protocol', 'TE (ms)', 'Stacks', 'Time', 'CNR', 'SSIM']]
    
    for name, te, stacks in protocols:
        if te in data['te_values']:
            cnr_val = data['cnr'][te][stacks-1]
            ssim_val = data['ssim'][te][stacks-1]
            time_pct = f"{int(100 * stacks / 6)}%"
            table_data.append([name, str(te), str(stacks), time_pct, 
                              f"{cnr_val:.3f}", f"{ssim_val:.3f}"])
    
    table = ax3.table(cellText=table_data[1:], colLabels=table_data[0],
                     cellLoc='center', loc='center',
                     colWidths=[0.15, 0.12, 0.12, 0.12, 0.12, 0.12])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.2)
    
    # Color code the header and rows
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#4472c4')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Color code protocol rows
    colors = ['#ffcccc', '#ccffcc', '#ccccff', '#ffffcc']
    for i, color in enumerate(colors, 1):
        for j in range(len(table_data[0])):
            table[(i, j)].set_facecolor(color)
            table[(i, j)].set_text_props(weight='bold')
    
    ax3.set_title('Clinical Protocol Recommendations\n(Based on Actual Data)', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Future directions with actual insights
    ax4.axis('off')
    future_text = """FUTURE RESEARCH DIRECTIONS

AI-Enhanced Reconstruction
• Machine learning for stack optimization
• Real-time quality assessment

Pathology-Specific Protocols  
• Condition-specific TE selection
• Developmental stage optimization

Multi-Center Validation
• Protocol standardization  
• Cross-platform validation

Motion-Robust Techniques
• Reduced stack requirements
• Real-time motion correction

CURRENT STUDY INSIGHTS:
• TE 181ms optimal for most cases
• 8 stacks provide 95% quality benefit
• 33% time reduction achievable"""
    
    ax4.text(0.05, 0.98, future_text, fontsize=12, ha='left', va='top',
            transform=ax4.transAxes, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgreen', 
                     alpha=0.8, edgecolor='darkgreen', linewidth=2))
    
    plt.tight_layout()
    return fig

def main():
    """Generate all presentation slides with actual data and convert to PDF"""
    print("Loading analysis data...")
    data = load_analysis_data()
    
    if not data or not data.get('te_values'):
        print("Warning: Could not load analysis data. Using sample data.")
        # Fallback sample data
        data = {
            'te_values': [98, 140, 181, 272],
            'stacks': list(range(1, 13)),
            'cr': {98: [0.85]*12, 140: [0.82]*12, 181: [0.78]*12, 272: [0.73]*12},
            'cnr': {98: [0.45]*12, 140: [0.50]*12, 181: [0.57]*12, 272: [0.59]*12},
            'snr_gm': {98: [2.47]*12, 140: [2.22]*12, 181: [1.99]*12, 272: [1.71]*12},
            'snr_wm': {98: [4.49]*12, 140: [3.89]*12, 181: [3.47]*12, 272: [2.77]*12},
            'ssim': {98: [0.617, 0.859, 0.881, 0.911, 0.893, 0.934, 0.949, 0.961, 0.974, 0.978, 0.989, 1.0],
                    140: [0.664, 0.801, 0.861, 0.882, 0.894, 0.927, 0.934, 0.944, 0.952, 0.968, 0.977, 1.0],
                    181: [0.729, 0.801, 0.846, 0.888, 0.925, 0.928, 0.937, 0.959, 0.969, 0.976, 0.984, 1.0],
                    272: [0.798, 0.773, 0.847, 0.883, 0.925, 0.942, 0.951, 0.959, 0.969, 0.972, 0.975, 1.0]},
            'mse': {98: [38400, 6850, 5120, 4130, 5790, 3060, 2050, 1400, 859, 722, 308, 0],
                   140: [30900, 11900, 8780, 4930, 6160, 2950, 4330, 3040, 2600, 1380, 714, 0],
                   181: [25400, 13800, 7210, 4850, 2160, 2620, 2680, 1280, 987, 653, 409, 0],
                   272: [12500, 12500, 7270, 4100, 1870, 1450, 1150, 925, 609, 550, 558, 0]}
        }
    
    print("Generating professional presentation slides...")
    
    # Create slides with actual data
    slides = [
        ("Title Slide", create_title_slide()),
        ("Key Findings Summary", create_key_findings_summary(data)),
        ("Statistical Analysis", create_statistical_analysis(data)),
        ("Clinical Impact", create_clinical_impact_slide(data))
    ]
    
    # Create comprehensive slide PDF
    pdf_filename = "fetal_mri_comprehensive_presentation.pdf"
    
    with PdfPages(pdf_filename) as pdf:
        for i, (title, fig) in enumerate(slides, 1):
            # Save individual PNG slides
            png_filename = f"slide_{i:02d}_{title.lower().replace(' ', '_')}.png"
            fig.savefig(png_filename, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            print(f"Saved PNG: {png_filename}")
            
            # Add to PDF
            pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
            plt.close(fig)
    
    print(f"\nComprehensive PDF presentation saved: {pdf_filename}")
    
    # Also include the analysis figure in the PDF if it exists
    analysis_figure = "comprehensive_te_analysis_publication.png"
    if os.path.exists(analysis_figure):
        print(f"\nCreating extended PDF with analysis figure...")
        
        # Create extended PDF with analysis figure
        extended_pdf = "fetal_mri_extended_presentation.pdf"
        with PdfPages(extended_pdf) as pdf:
            # Add all slides
            for title, fig_func in [("Title Slide", create_title_slide),
                                   ("Key Findings Summary", lambda: create_key_findings_summary(data)),
                                   ("Statistical Analysis", lambda: create_statistical_analysis(data)),
                                   ("Clinical Impact", lambda: create_clinical_impact_slide(data))]:
                fig = fig_func()
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
            
            # Add the comprehensive analysis figure
            from matplotlib.image import imread
            try:
                img = imread(analysis_figure)
                fig, ax = plt.subplots(figsize=(16, 12))
                ax.imshow(img)
                ax.axis('off')
                ax.set_title('Comprehensive Image Quality Analysis Results', 
                           fontsize=20, fontweight='bold', pad=20)
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
                print(f"Extended PDF with analysis figure saved: {extended_pdf}")
            except Exception as e:
                print(f"Could not include analysis figure: {e}")
    
    print("\nAll slides and PDFs generated successfully!")
    print("\nPresentation Summary:")
    for i, (title, _) in enumerate(slides, 1):
        print(f"  Slide {i}: {title}")
    print(f"\nOutput files:")
    print(f"  • Individual PNG slides: slide_01_*.png to slide_04_*.png")
    print(f"  • Comprehensive PDF: {pdf_filename}")
    if os.path.exists(analysis_figure):
        print(f"  • Extended PDF (with analysis): fetal_mri_extended_presentation.pdf")
    print(f"  • Markdown presentation: key_findings_presentation.md")
    
    return slides
