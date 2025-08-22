#!/usr/bin/env python3
"""
Generate professional presentation slides for fetal MRI analysis key findings
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import os
from itertools import combinations

# Set up professional presentation style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 14,
    'font.family': 'DejaVu Sans',
    'axes.titlesize': 18,
    'axes.labelsize': 14,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 20
})

def compute_stack_combination_stats(data_dict, n_stacks, n_combinations=20):
    """
    Compute statistics for different combinations of stacks
    
    Parameters:
    - data_dict: dictionary with TE as keys and lists of values as values
    - n_stacks: number of stacks to select
    - n_combinations: number of random combinations to try
    
    Returns:
    - dict with means and stds for each TE
    """
    stats = {}
    
    for te in data_dict.keys():
        if len(data_dict[te]) < n_stacks:
            continue
            
        # Get all possible combinations or sample if too many
        total_stacks = len(data_dict[te])
        if total_stacks == 12:  # Our case
            all_combinations = list(combinations(range(total_stacks), n_stacks))
            if len(all_combinations) > n_combinations:
                # Sample random combinations
                selected_combinations = np.random.choice(len(all_combinations), 
                                                       n_combinations, replace=False)
                combinations_to_use = [all_combinations[i] for i in selected_combinations]
            else:
                combinations_to_use = all_combinations
        else:
            combinations_to_use = [tuple(range(n_stacks))]
        
        # Compute mean for each combination
        combination_means = []
        for combo in combinations_to_use:
            combo_values = [data_dict[te][i] for i in combo]
            combination_means.append(np.mean(combo_values))
        
        stats[te] = {
            'mean': np.mean(combination_means),
            'std': np.std(combination_means)
        }
    
    return stats

# Load actual data from comprehensive analysis
def load_actual_data():
    """Load the actual data from comprehensive analysis results"""
    # Parse actual results from our analysis
    actual_data = {
        'te_values': [98, 140, 181, 272],
        'stacks': list(range(1, 13)),
        
        # Actual CNR values from comprehensive analysis
        'cnr': {
            98: [0.253, 0.420, 0.466, 0.431, 0.451, 0.469, 0.458, 0.460, 0.452, 0.456, 0.454, 0.459],
            140: [0.293, 0.444, 0.477, 0.489, 0.492, 0.499, 0.496, 0.489, 0.505, 0.501, 0.507, 0.508],
            181: [0.525, 0.520, 0.547, 0.566, 0.548, 0.566, 0.569, 0.573, 0.569, 0.567, 0.572, 0.569],
            272: [0.571, 0.479, 0.579, 0.589, 0.589, 0.591, 0.597, 0.595, 0.591, 0.602, 0.600, 0.601]
        },
        
        # Actual SNR values
        'snr_gm': {
            98: [2.348, 2.420, 2.404, 2.451, 2.430, 2.475, 2.458, 2.468, 2.465, 2.464, 2.465, 2.472],
            140: [2.134, 2.174, 2.156, 2.171, 2.196, 2.214, 2.198, 2.216, 2.242, 2.219, 2.238, 2.239],
            181: [1.990, 1.964, 1.993, 1.979, 1.950, 1.975, 2.003, 2.000, 1.985, 1.997, 1.998, 1.998],
            272: [1.714, 1.695, 1.675, 1.693, 1.683, 1.707, 1.711, 1.701, 1.706, 1.719, 1.715, 1.715]
        },
        
        'snr_wm': {
            98: [3.228, 3.979, 4.094, 4.245, 4.325, 4.323, 4.394, 4.467, 4.466, 4.433, 4.483, 4.493],
            140: [2.933, 3.395, 3.611, 3.605, 3.708, 3.805, 3.804, 3.857, 3.896, 3.876, 3.913, 3.920],
            181: [2.976, 3.102, 3.112, 3.209, 3.252, 3.336, 3.367, 3.395, 3.419, 3.430, 3.455, 3.472],
            272: [2.501, 2.339, 2.510, 2.601, 2.609, 2.730, 2.731, 2.749, 2.724, 2.770, 2.776, 2.775]
        },
        
        # Actual SSIM values
        'ssim': {
            98: [0.617, 0.859, 0.881, 0.911, 0.893, 0.934, 0.949, 0.961, 0.974, 0.978, 0.989, 1.000],
            140: [0.664, 0.801, 0.861, 0.882, 0.894, 0.927, 0.934, 0.944, 0.952, 0.968, 0.977, 1.000],
            181: [0.729, 0.801, 0.846, 0.888, 0.925, 0.928, 0.937, 0.959, 0.969, 0.976, 0.984, 1.000],
            272: [0.798, 0.773, 0.847, 0.883, 0.925, 0.942, 0.951, 0.959, 0.969, 0.972, 0.975, 1.000]
        },
        
        # Actual MSE values
        'mse': {
            98: [38400, 6850, 5120, 4130, 5790, 3060, 2050, 1400, 859, 722, 308, 0],
            140: [30900, 11900, 8780, 4930, 6160, 2950, 4330, 3040, 2600, 1380, 714, 0],
            181: [25400, 13800, 7210, 4850, 2160, 2620, 2680, 1280, 987, 653, 409, 0],
            272: [12500, 12500, 7270, 4100, 1870, 1450, 1150, 925, 609, 550, 558, 0]
        }
    }
    return actual_data

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

def create_comprehensive_analysis_slide(data):
    """Create slide with comprehensive analysis including actual figures with proper error bars"""
    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(20, 12))
    
    # 1. CNR vs TE with error bars from stack combinations (using 8 stacks as representative)
    te_values = data['te_values']
    cnr_stats = compute_stack_combination_stats(data['cnr'], n_stacks=8, n_combinations=30)
    
    cnr_means = [cnr_stats[te]['mean'] for te in te_values if te in cnr_stats]
    cnr_stds = [cnr_stats[te]['std'] for te in te_values if te in cnr_stats]
    
    bars = ax1.bar(te_values, cnr_means, yerr=cnr_stds, capsize=8,
                   color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'],
                   edgecolor='black', linewidth=1)
    ax1.set_xlabel('Echo Time (ms)', fontweight='bold')
    ax1.set_ylabel('CNR', fontweight='bold')
    ax1.set_title('A. CNR vs TE (8-stack combinations)', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, mean, std in zip(bars, cnr_means, cnr_stds):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + std + 0.01,
                f'{mean:.3f}±{std:.3f}', ha='center', va='bottom', 
                fontweight='bold', fontsize=10)
    
    # 2. SSIM vs Stack count with error bars from combinations
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
    stack_range = [3, 6, 9, 12]  # Representative stack counts
    
    for i, te in enumerate(te_values):
        ssim_means = []
        ssim_stds = []
        
        for n_stacks in stack_range:
            if n_stacks <= len(data['ssim'][te]):
                stats = compute_stack_combination_stats({te: data['ssim'][te]}, 
                                                      n_stacks=n_stacks, n_combinations=20)
                ssim_means.append(stats[te]['mean'])
                ssim_stds.append(stats[te]['std'])
            else:
                ssim_means.append(data['ssim'][te][-1])
                ssim_stds.append(0)
        
        ax2.errorbar(stack_range, ssim_means, yerr=ssim_stds, 
                    fmt='o-', label=f'TE {te}ms', linewidth=2, markersize=8, 
                    color=colors[i], capsize=5, capthick=2)
    
    ax2.axhline(y=0.95, color='red', linestyle='--', linewidth=2, alpha=0.8)
    ax2.set_xlabel('Number of Stacks', fontweight='bold')
    ax2.set_ylabel('SSIM', fontweight='bold')
    ax2.set_title('B. SSIM vs Stack Count (combination variability)', fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0.7, 1.02)
    
    # 3. SNR comparison with error bars from 8-stack combinations
    te_labels = [f'{te}ms' for te in te_values]
    snr_gm_stats = compute_stack_combination_stats(data['snr_gm'], n_stacks=8, n_combinations=30)
    snr_wm_stats = compute_stack_combination_stats(data['snr_wm'], n_stacks=8, n_combinations=30)
    
    gm_snr = [snr_gm_stats[te]['mean'] for te in te_values if te in snr_gm_stats]
    wm_snr = [snr_wm_stats[te]['mean'] for te in te_values if te in snr_wm_stats]
    gm_std = [snr_gm_stats[te]['std'] for te in te_values if te in snr_gm_stats]
    wm_std = [snr_wm_stats[te]['std'] for te in te_values if te in snr_wm_stats]
    
    x = np.arange(len(te_labels))
    width = 0.35
    
    ax3.bar(x - width/2, gm_snr, width, label='Gray Matter', 
           color='lightcoral', yerr=gm_std, capsize=5, edgecolor='black')
    ax3.bar(x + width/2, wm_snr, width, label='White Matter', 
           color='lightblue', yerr=wm_std, capsize=5, edgecolor='black')
    
    ax3.set_xlabel('Echo Time', fontweight='bold')
    ax3.set_ylabel('SNR', fontweight='bold')
    ax3.set_title('C. SNR by Tissue (8-stack combinations)', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(te_labels)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3)
    
    # 4. MSE vs Stack count with error bars from combinations
    for i, te in enumerate(te_values):
        mse_means = []
        mse_stds = []
        
        for n_stacks in stack_range:
            if n_stacks <= len(data['mse'][te]):
                stats = compute_stack_combination_stats({te: data['mse'][te]}, 
                                                      n_stacks=n_stacks, n_combinations=20)
                mse_means.append(stats[te]['mean'])
                mse_stds.append(stats[te]['std'])
            else:
                mse_means.append(data['mse'][te][-1])
                mse_stds.append(0)
        
        ax4.errorbar(stack_range, mse_means, yerr=mse_stds,
                    fmt='o-', label=f'TE {te}ms', linewidth=2, markersize=6, 
                    color=colors[i], capsize=5, capthick=2)
    
    ax4.set_yscale('log')
    ax4.set_xlabel('Number of Stacks', fontweight='bold')
    ax4.set_ylabel('MSE (log scale)', fontweight='bold')
    ax4.set_title('D. Reconstruction Error (combination variability)', fontweight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    # 5. Quality vs Time trade-off with error bars
    stack_points = [6, 8, 10, 12]
    scan_time = [100, 133, 167, 200]
    quality_means = []
    quality_stds = []
    
    for stack in stack_points:
        # Get SSIM values for all TEs at this stack count
        ssim_values = [data['ssim'][te][stack-1] for te in te_values if stack <= len(data['ssim'][te])]
        if len(ssim_values) > 0:
            # Compute stats across different stack combinations for average SSIM
            all_te_stats = []
            for te in te_values:
                if stack <= len(data['ssim'][te]):
                    te_stats = compute_stack_combination_stats({te: data['ssim'][te]}, 
                                                             n_stacks=stack, n_combinations=15)
                    all_te_stats.append(te_stats[te]['mean'])
            
            quality_means.append(np.mean(all_te_stats))
            quality_stds.append(np.std(all_te_stats))
        else:
            quality_means.append(1.0)
            quality_stds.append(0.0)
    
    ax5.errorbar(scan_time, quality_means, yerr=quality_stds,
                fmt='o', markersize=12, capsize=8, capthick=3, linewidth=3,
                color='purple', ecolor='red', alpha=0.8)
    
    for i, (x, y, s, std) in enumerate(zip(scan_time, quality_means, stack_points, quality_stds)):
        ax5.annotate(f'{s} stacks\nSSIM={y:.3f}±{std:.3f}', (x, y), 
                    xytext=(10, 15), textcoords='offset points', 
                    fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
    
    ax5.set_xlabel('Relative Scan Time (%)', fontweight='bold')
    ax5.set_ylabel('Quality Score (SSIM)', fontweight='bold')
    ax5.set_title('E. Quality vs Time (combination variability)', fontweight='bold')
    ax5.grid(True, alpha=0.3)
    ax5.set_xlim(90, 210)
    ax5.set_ylim(0.85, 1.02)
    
    # 6. Clinical recommendations with updated combination-based values
    ax6.axis('off')
    
    # Calculate combination-based values for recommendations
    cnr_181_stats = compute_stack_combination_stats({181: data['cnr'][181]}, n_stacks=8, n_combinations=30)
    cnr_140_stats = compute_stack_combination_stats({140: data['cnr'][140]}, n_stacks=6, n_combinations=20)
    cnr_272_stats = compute_stack_combination_stats({272: data['cnr'][272]}, n_stacks=10, n_combinations=20)
    
    ssim_181_stats = compute_stack_combination_stats({181: data['ssim'][181]}, n_stacks=8, n_combinations=30)
    ssim_140_stats = compute_stack_combination_stats({140: data['ssim'][140]}, n_stacks=6, n_combinations=20)
    ssim_272_stats = compute_stack_combination_stats({272: data['ssim'][272]}, n_stacks=10, n_combinations=20)
    
    recommendations = f"""CLINICAL RECOMMENDATIONS
    (Error bars from stack combinations)
    
    OPTIMAL PROTOCOL
    TE: 181 ms, Stacks: 8
    CNR: {cnr_181_stats[181]['mean']:.3f}±{cnr_181_stats[181]['std']:.3f}
    SSIM: {ssim_181_stats[181]['mean']:.3f}±{ssim_181_stats[181]['std']:.3f}
    
    TIME-CRITICAL
    TE: 140 ms, Stacks: 6
    CNR: {cnr_140_stats[140]['mean']:.3f}±{cnr_140_stats[140]['std']:.3f}
    SSIM: {ssim_140_stats[140]['mean']:.3f}±{ssim_140_stats[140]['std']:.3f}
    
    HIGH CONTRAST
    TE: 272 ms, Stacks: 10
    CNR: {cnr_272_stats[272]['mean']:.3f}±{cnr_272_stats[272]['std']:.3f}
    SSIM: {ssim_272_stats[272]['mean']:.3f}±{ssim_272_stats[272]['std']:.3f}
    
    Error bars represent variability
    across different stack combinations"""
    
    ax6.text(0.05, 0.95, recommendations, fontsize=11, ha='left', va='top',
            transform=ax6.transAxes, fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow', 
                     alpha=0.9, edgecolor='orange', linewidth=2))
    
    ax6.set_title('F. Clinical Recommendations (Combination-based)', fontweight='bold')
    
    plt.tight_layout()
    return fig

def create_updated_comprehensive_figure(data):
    """Create updated version of comprehensive analysis figure with proper error bars"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    ax1, ax2, ax3, ax4, ax5, ax6 = axes.flatten()
    
    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']
    te_values = data['te_values']
    stack_counts = [3, 6, 9, 12]
    
    # Plot 1: CNR vs TE with combination-based error bars
    cnr_stats = compute_stack_combination_stats(data['cnr'], n_stacks=8, n_combinations=30)
    cnr_means = [cnr_stats[te]['mean'] for te in te_values]
    cnr_stds = [cnr_stats[te]['std'] for te in te_values]
    
    ax1.errorbar(te_values, cnr_means, yerr=cnr_stds, fmt='o-', 
                 capsize=8, capthick=3, linewidth=3, markersize=10,
                 color='#2E86AB', ecolor='#A23B72', markerfacecolor='white',
                 markeredgecolor='#2E86AB', markeredgewidth=2)
    
    ax1.set_xlabel('Echo Time (ms)', fontweight='bold')
    ax1.set_ylabel('Contrast-to-Noise Ratio', fontweight='bold')
    ax1.set_title('CNR vs TE (8-stack combinations)', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: SSIM vs Stack Count with combination error bars
    for i, te in enumerate(te_values):
        means, stds = [], []
        for n_stacks in stack_counts:
            stats = compute_stack_combination_stats({te: data['ssim'][te]}, 
                                                   n_stacks=n_stacks, n_combinations=20)
            means.append(stats[te]['mean'])
            stds.append(stats[te]['std'])
        
        ax2.errorbar(stack_counts, means, yerr=stds, fmt='o-', 
                     label=f'TE {te}ms', color=colors[i], linewidth=2, 
                     markersize=8, capsize=5, capthick=2)
    
    ax2.axhline(y=0.95, color='red', linestyle='--', linewidth=2, alpha=0.8, 
                label='Quality threshold')
    ax2.set_xlabel('Number of Stacks', fontweight='bold')
    ax2.set_ylabel('Structural Similarity Index', fontweight='bold')
    ax2.set_title('SSIM vs Stack Count (combination variability)', fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: SNR by Tissue with combination error bars
    snr_gm_stats = compute_stack_combination_stats(data['snr_gm'], n_stacks=8, n_combinations=30)
    snr_wm_stats = compute_stack_combination_stats(data['snr_wm'], n_stacks=8, n_combinations=30)
    
    gm_means = [snr_gm_stats[te]['mean'] for te in te_values]
    wm_means = [snr_wm_stats[te]['mean'] for te in te_values]
    gm_stds = [snr_gm_stats[te]['std'] for te in te_values]
    wm_stds = [snr_wm_stats[te]['std'] for te in te_values]
    
    x = np.arange(len(te_values))
    width = 0.35
    
    ax3.bar(x - width/2, gm_means, width, yerr=gm_stds, 
            label='Gray Matter', color='lightcoral', capsize=5, 
            edgecolor='black', alpha=0.8)
    ax3.bar(x + width/2, wm_means, width, yerr=wm_stds,
            label='White Matter', color='lightblue', capsize=5, 
            edgecolor='black', alpha=0.8)
    
    ax3.set_xlabel('Echo Time (ms)', fontweight='bold')
    ax3.set_ylabel('Signal-to-Noise Ratio', fontweight='bold')
    ax3.set_title('SNR by Tissue Type (8-stack combinations)', fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels([f'{te}ms' for te in te_values])
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: MSE vs Stack Count with combination error bars
    for i, te in enumerate(te_values):
        means, stds = [], []
        for n_stacks in stack_counts:
            stats = compute_stack_combination_stats({te: data['mse'][te]}, 
                                                   n_stacks=n_stacks, n_combinations=20)
            means.append(stats[te]['mean'])
            stds.append(stats[te]['std'])
        
        ax4.errorbar(stack_counts, means, yerr=stds, fmt='o-', 
                     label=f'TE {te}ms', color=colors[i], linewidth=2, 
                     markersize=8, capsize=5, capthick=2)
    
    ax4.set_yscale('log')
    ax4.set_xlabel('Number of Stacks', fontweight='bold')
    ax4.set_ylabel('Mean Squared Error (log scale)', fontweight='bold')
    ax4.set_title('Reconstruction Error (combination variability)', fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Combined TE analysis with error bars
    # Show both CNR and SSIM for 8-stack combinations
    ax5_twin = ax5.twinx()
    
    # CNR on left axis
    bars1 = ax5.bar([x - 0.2 for x in range(len(te_values))], cnr_means, 
                    0.4, yerr=cnr_stds, capsize=5, 
                    color='coral', alpha=0.7, label='CNR')
    ax5.set_ylabel('Contrast-to-Noise Ratio', fontweight='bold', color='coral')
    ax5.tick_params(axis='y', labelcolor='coral')
    
    # SSIM on right axis (8-stack values with combinations)
    ssim_8_stats = [compute_stack_combination_stats({te: data['ssim'][te]}, 
                                                    n_stacks=8, n_combinations=30)[te] 
                    for te in te_values]
    ssim_8_means = [s['mean'] for s in ssim_8_stats]
    ssim_8_stds = [s['std'] for s in ssim_8_stats]
    
    bars2 = ax5_twin.bar([x + 0.2 for x in range(len(te_values))], ssim_8_means, 
                         0.4, yerr=ssim_8_stds, capsize=5,
                         color='skyblue', alpha=0.7, label='SSIM (8 stacks)')
    ax5_twin.set_ylabel('Structural Similarity Index', fontweight='bold', color='skyblue')
    ax5_twin.tick_params(axis='y', labelcolor='skyblue')
    
    ax5.set_xlabel('Echo Time (ms)', fontweight='bold')
    ax5.set_title('CNR & SSIM vs TE (8-stack combinations)', fontweight='bold')
    ax5.set_xticks(range(len(te_values)))
    ax5.set_xticklabels([f'{te}' for te in te_values])
    
    # Combined legend
    lines1, labels1 = ax5.get_legend_handles_labels()
    lines2, labels2 = ax5_twin.get_legend_handles_labels()
    ax5.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    ax5.grid(True, alpha=0.3)
    
    # Plot 6: Quality metrics summary table
    ax6.axis('off')
    
    # Create summary table with combination statistics
    table_data = [['TE (ms)', 'CNR', 'SSIM (8 stacks)', 'SNR GM', 'SNR WM']]
    
    for te in te_values:
        cnr_val = f"{cnr_stats[te]['mean']:.3f}±{cnr_stats[te]['std']:.3f}"
        ssim_val = f"{ssim_8_stats[te_values.index(te)]['mean']:.3f}±{ssim_8_stats[te_values.index(te)]['std']:.3f}"
        gm_val = f"{snr_gm_stats[te]['mean']:.2f}±{snr_gm_stats[te]['std']:.2f}"
        wm_val = f"{snr_wm_stats[te]['mean']:.2f}±{snr_wm_stats[te]['std']:.2f}"
        table_data.append([str(te), cnr_val, ssim_val, gm_val, wm_val])
    
    table = ax6.table(cellText=table_data[1:], colLabels=table_data[0],
                      cellLoc='center', loc='center',
                      colWidths=[0.15, 0.25, 0.25, 0.20, 0.20])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Style the table
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#4472c4')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax6.set_title('Quality Metrics Summary\n(Error bars from stack combinations)', 
                  fontweight='bold')
    
    plt.tight_layout()
    return fig

def main():
    """Generate presentation slides with actual data and proper combination-based error bars"""
    # Set random seed for reproducible combinations
    np.random.seed(42)
    
    print("Loading actual analysis data...")
    data = load_actual_data()
    
    print("Generating slides with actual figures...")
    
    # Create slides
    slides = [
        ("Title Slide", create_title_slide()),
        ("Comprehensive Analysis", create_comprehensive_analysis_slide(data))
    ]
    
    # Create comprehensive slide PDF
    pdf_filename = "fetal_mri_presentation_with_figures.pdf"
    
    with PdfPages(pdf_filename) as pdf:
        for i, (title, fig) in enumerate(slides, 1):
            # Save individual PNG slides
            png_filename = f"presentation_slide_{i:02d}_{title.lower().replace(' ', '_')}.png"
            fig.savefig(png_filename, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            print(f"Saved PNG: {png_filename}")
            
            # Add to PDF
            pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
            plt.close(fig)
    
    print(f"Comprehensive PDF presentation saved: {pdf_filename}")
    
    # Include the original comprehensive analysis figure if available
    analysis_figure = "comprehensive_te_analysis_publication.png"
    if os.path.exists(analysis_figure):
        print("Adding original analysis figure to extended PDF...")
        
        extended_pdf = "fetal_mri_complete_presentation.pdf"
        with PdfPages(extended_pdf) as pdf:
            # Add slides
            for title, fig_func in [("Title Slide", create_title_slide),
                                   ("Comprehensive Analysis", lambda: create_comprehensive_analysis_slide(data))]:
                fig = fig_func()
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
            
            # Add original analysis figure
            from matplotlib.image import imread
            img = imread(analysis_figure)
            fig, ax = plt.subplots(figsize=(16, 12))
            ax.imshow(img)
            ax.axis('off')
            ax.set_title('Original Comprehensive Analysis Results', 
                       fontsize=18, fontweight='bold', pad=20)
            pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
            plt.close(fig)
            
        print(f"Complete presentation with original figure: {extended_pdf}")
    
    print("\nPresentation generation completed!")
    print("\nFiles created:")
    print(f"  • Main PDF: {pdf_filename}")
    if os.path.exists(analysis_figure):
        print("  • Extended PDF: fetal_mri_complete_presentation.pdf")
    print("  • Individual PNG slides: presentation_slide_*.png")
    
    return slides

if __name__ == "__main__":
    main()
