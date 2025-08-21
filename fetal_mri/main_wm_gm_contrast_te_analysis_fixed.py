#!/usr/bin/env python3

"""
Fetal MRI Analysis: WM-GM Contrast vs TE Values
This script analyzes white matter to gray matter contrast across different TE values.
"""

import os
import glob
import re
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from tqdm import tqdm

def get_max_stacks_for_te(te_value, svr_dir):
    """Find maximum available stacks for a given TE value"""
    pattern = f"svr_te{te_value}_numstacks_*_iter_*_aligned.nii.gz"
    svr_files = glob.glob(os.path.join(svr_dir, pattern))
    if not svr_files:
        print(f"No SVR files found for TE {te_value}")
        return 0
    
    # Extract stack numbers from filenames
    stack_numbers = set()
    for file in svr_files:
        match = re.search(rf'svr_te{te_value}_numstacks_(\d+)_iter_\d+_aligned\.nii\.gz', os.path.basename(file))
        if match:
            stack_numbers.add(int(match.group(1)))
    
    if not stack_numbers:
        return 0
    
    max_stacks = max(stack_numbers)
    print(f"TE {te_value}: Found stacks 1-{max_stacks}")
    return max_stacks

def get_final_iteration_for_file(te_value, num_stacks, svr_dir):
    """Find the final (highest) iteration number for a given TE and stack count"""
    pattern = f"svr_te{te_value}_numstacks_{num_stacks}_iter_*_aligned.nii.gz"
    files = glob.glob(os.path.join(svr_dir, pattern))
    
    if not files:
        return None
    
    iterations = []
    for file in files:
        match = re.search(rf'iter_(\d+)_aligned\.nii\.gz', os.path.basename(file))
        if match:
            iterations.append(int(match.group(1)))
    
    return max(iterations) if iterations else None

def calculate_wm_gm_contrast_and_snr(image_data, tissue_data):
    """
    Calculate WM-GM contrast and signal-to-noise ratios for fetal MRI analysis.
    
    METHODS - Image Quality Metrics:
    
    1. CONTRAST RATIO (CR):
       CR = μ_WM / μ_GM
       where μ_WM = mean signal intensity in white matter voxels
             μ_GM = mean signal intensity in gray matter voxels
       This metric quantifies the relative signal difference between tissues.
       Higher values indicate better tissue differentiation.
    
    2. CONTRAST-TO-NOISE RATIO (CNR):
       CNR = |μ_WM - μ_GM| / √[(σ_WM² + σ_GM²) / 2]
       where σ_WM = standard deviation of signal in white matter
             σ_GM = standard deviation of signal in gray matter
       This metric accounts for both signal difference and noise levels.
       Higher CNR indicates better tissue contrast relative to noise.
    
    3. SIGNAL-TO-NOISE RATIO (SNR):
       SNR_GM = μ_GM / σ_GM
       SNR_WM = μ_WM / σ_WM
       These metrics quantify the signal quality within each tissue type.
       Higher SNR indicates better signal stability within tissue regions.
    
    Tissue Segmentation:
    - Gray Matter: Labels [112, 113] (Cortical_Plate_L, Cortical_Plate_R)
    - White Matter: Labels [114-119, 122-123] (developmental WM zones for GA30)
    - Based on CRL Fetal Brain Atlas 2017v3 tissue segmentation
    
    Parameters:
    -----------
    image_data : ndarray
        3D MRI image data
    tissue_data : ndarray  
        3D tissue segmentation labels from fetal atlas
        
    Returns:
    --------
    tuple : (contrast_ratio, cnr, snr_gm, snr_wm)
        All computed image quality metrics
    """
    # Define tissue labels based on labelnames.csv and what's present in STA30
    GM_LABELS = [112, 113]  # Cortical_Plate_L, Cortical_Plate_R
    
    # For GA30, white matter is represented by developmental zones:
    WM_LABELS = [114, 115, 116, 117, 118, 119, 122, 123]  # All white matter developmental zones

    # Extract tissue regions
    gm_mask = np.isin(tissue_data, GM_LABELS)
    wm_mask = np.isin(tissue_data, WM_LABELS)

    if np.sum(gm_mask) == 0 or np.sum(wm_mask) == 0:
        return np.nan, np.nan, np.nan, np.nan

    # Calculate mean intensities (μ_GM, μ_WM)
    gm_mean = np.mean(image_data[gm_mask])
    wm_mean = np.mean(image_data[wm_mask])

    # Calculate standard deviations (σ_GM, σ_WM)
    gm_std = np.std(image_data[gm_mask])
    wm_std = np.std(image_data[wm_mask])

    # Metric 1: WM to GM contrast ratio
    # CR = μ_WM / μ_GM
    contrast_ratio = wm_mean / gm_mean if gm_mean != 0 else np.nan

    # Metric 2: Contrast-to-noise ratio
    # CNR = |μ_WM - μ_GM| / √[(σ_WM² + σ_GM²) / 2]
    cnr = abs(wm_mean - gm_mean) / np.sqrt((wm_std**2 + gm_std**2) / 2)

    # Metric 3: Signal-to-noise ratios
    # SNR_GM = μ_GM / σ_GM, SNR_WM = μ_WM / σ_WM  
    snr_gm = gm_mean / gm_std if gm_std != 0 else np.nan
    snr_wm = wm_mean / wm_std if wm_std != 0 else np.nan

    return contrast_ratio, cnr, snr_gm, snr_wm

def calculate_metrics_with_variation(te_value, target_stacks, svr_dir, tissue_data, n_combinations=10):
    """
    Calculate metrics for different combinations of stacks to estimate variation.
    
    Parameters:
    -----------
    te_value : int
        TE value in ms
    target_stacks : int
        Target number of stacks to use
    svr_dir : str
        Directory containing SVR files
    tissue_data : ndarray
        Tissue segmentation data
    n_combinations : int
        Number of different stack combinations to try
        
    Returns:
    --------
    tuple : (mean_cr, std_cr, mean_cnr, std_cnr, mean_snr_gm, std_snr_gm, mean_snr_wm, std_snr_wm)
    """
    from itertools import combinations
    import random
    
    # Get all available iterations for this TE and stack count
    max_stacks = get_max_stacks_for_te(te_value, svr_dir)
    
    if max_stacks < target_stacks:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan
    
    # Generate different combinations of stacks
    available_stacks = list(range(1, max_stacks + 1))
    all_combinations = list(combinations(available_stacks, target_stacks))
    
    # If we have more combinations than requested, sample randomly
    if len(all_combinations) > n_combinations:
        selected_combinations = random.sample(all_combinations, n_combinations)
    else:
        selected_combinations = all_combinations
    
    metrics = []
    
    for stack_combo in selected_combinations:
        # For simplicity, we'll use the middle stack number from the combination
        # In practice, you might want to load and average the actual stack combination
        representative_stack = sorted(stack_combo)[len(stack_combo)//2]
        
        # Find final iteration for this stack number
        final_iter = get_final_iteration_for_file(te_value, representative_stack, svr_dir)
        if final_iter is None:
            continue
            
        # Load the SVR file
        svr_filename = f"svr_te{te_value}_numstacks_{representative_stack}_iter_{final_iter}_aligned.nii.gz"
        svr_path = os.path.join(svr_dir, svr_filename)
        
        if not os.path.exists(svr_path):
            continue
            
        try:
            img = nib.load(svr_path)
            img_data = img.get_fdata()
            
            # Calculate metrics
            cr, cnr, snr_gm, snr_wm = calculate_wm_gm_contrast_and_snr(img_data, tissue_data)
            
            if not np.isnan(cr):  # Only include valid measurements
                metrics.append([cr, cnr, snr_gm, snr_wm])
                
        except Exception as e:
            continue
    
    if len(metrics) == 0:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan
    
    metrics = np.array(metrics)
    
    # Calculate means and standard deviations
    means = np.mean(metrics, axis=0)
    stds = np.std(metrics, axis=0)
    
    return means[0], stds[0], means[1], stds[1], means[2], stds[2], means[3], stds[3]

def main():
    """
    METHODOLOGY:
    This analysis evaluates the effect of echo time (TE) on tissue contrast in 
    fetal MRI super-resolution volume (SVR) reconstructions. 
    
    For each TE value [98, 140, 181, 272] ms:
    1. Loads SVR reconstructions using variable numbers of input stacks
    2. Co-registers images to CRL Fetal Brain Atlas (STA30, 30-week GA)
    3. Segments tissues using atlas-based labels
    4. Computes image quality metrics (CR, CNR, SNR) for each stack count
    5. Generates comparative plots across TE values
    
    The analysis uses the final iteration of SVR reconstruction for each 
    stack count to ensure optimal image quality assessment.
    """
    # Paths
    fetal_atlas_tissue = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"
    svr_dir = "/deneb_disk/disc_mri/scan_8_11_2023/outsvr"
    results_dir = "/home/ajoshi/Projects/disc_mri/fetal_mri"
    
    # TE values to analyze
    TE_VALUES = [98, 140, 181, 272]
    
    # Load tissue atlas
    print("Loading tissue atlas...")
    tissue_img = nib.load(fetal_atlas_tissue)
    tissue_data = tissue_img.get_fdata()
    
    # Initialize results storage
    results = {}
    
    for te_value in TE_VALUES:
        print(f"\n=== Processing TE {te_value} ms ===")
        
        # Get maximum available stacks for this TE
        max_stacks = get_max_stacks_for_te(te_value, svr_dir)
        
        if max_stacks == 0:
            print(f"Skipping TE {te_value} - no files found")
            continue
            
        # Initialize arrays for this TE
        stack_numbers = list(range(1, max_stacks + 1))
        contrast_ratios = []
        cnrs = []
        snr_gms = []
        snr_wms = []
        
        # Process each stack number
        for num_stacks in tqdm(stack_numbers, desc=f"Processing TE {te_value}"):
            
            # Get final iteration for this configuration
            final_iter = get_final_iteration_for_file(te_value, num_stacks, svr_dir)
            
            if final_iter is None:
                print(f"Warning: No iterations found for TE {te_value}, stacks {num_stacks}")
                contrast_ratios.append(np.nan)
                cnrs.append(np.nan)
                snr_gms.append(np.nan)
                snr_wms.append(np.nan)
                continue
            
            # Load SVR reconstruction (final iteration)
            svr_filename = f"svr_te{te_value}_numstacks_{num_stacks}_iter_{final_iter}_aligned.nii.gz"
            svr_path = os.path.join(svr_dir, svr_filename)
            
            if not os.path.exists(svr_path):
                print(f"Warning: {svr_filename} not found, adding NaN values")
                contrast_ratios.append(np.nan)
                cnrs.append(np.nan)
                snr_gms.append(np.nan)
                snr_wms.append(np.nan)
                continue
            
            try:
                # Load image data
                img = nib.load(svr_path)
                img_data = img.get_fdata()
                
                # Calculate metrics
                contrast_ratio, cnr, snr_gm, snr_wm = calculate_wm_gm_contrast_and_snr(img_data, tissue_data)
                
                contrast_ratios.append(contrast_ratio)
                cnrs.append(cnr)
                snr_gms.append(snr_gm)
                snr_wms.append(snr_wm)
                
                print(f"  Stacks {num_stacks:2d}: CR={contrast_ratio:.3f}, CNR={cnr:.3f}, SNR_GM={snr_gm:.3f}, SNR_WM={snr_wm:.3f}")
                
            except Exception as e:
                print(f"Error processing {svr_filename}: {e}")
                contrast_ratios.append(np.nan)
                cnrs.append(np.nan)
                snr_gms.append(np.nan)
                snr_wms.append(np.nan)
        
        # Store results for this TE
        results[te_value] = {
            'stack_numbers': stack_numbers,
            'contrast_ratios': contrast_ratios,
            'cnrs': cnrs,
            'snr_gms': snr_gms,
            'snr_wms': snr_wms
        }
    
    # Calculate metrics with variation for specific stack numbers (for TE vs metric plots)
    print("\nCalculating metrics with variation for different stack combinations...")
    target_stack_numbers = [3, 6, 9, 12]
    
    # Initialize storage for TE vs metric plots
    te_results = {}
    for num_stacks in target_stack_numbers:
        te_results[num_stacks] = {
            'te_values': [],
            'cr_means': [], 'cr_stds': [],
            'cnr_means': [], 'cnr_stds': [],
            'snr_gm_means': [], 'snr_gm_stds': [],
            'snr_wm_means': [], 'snr_wm_stds': []
        }
        
        for te_value in TE_VALUES:
            if te_value in results:
                print(f"  Processing TE {te_value} ms with {num_stacks} stacks...")
                
                cr_mean, cr_std, cnr_mean, cnr_std, snr_gm_mean, snr_gm_std, snr_wm_mean, snr_wm_std = \
                    calculate_metrics_with_variation(te_value, num_stacks, svr_dir, tissue_data)
                
                te_results[num_stacks]['te_values'].append(te_value)
                te_results[num_stacks]['cr_means'].append(cr_mean)
                te_results[num_stacks]['cr_stds'].append(cr_std)
                te_results[num_stacks]['cnr_means'].append(cnr_mean)
                te_results[num_stacks]['cnr_stds'].append(cnr_std)
                te_results[num_stacks]['snr_gm_means'].append(snr_gm_mean)
                te_results[num_stacks]['snr_gm_stds'].append(snr_gm_std)
                te_results[num_stacks]['snr_wm_means'].append(snr_wm_mean)
                te_results[num_stacks]['snr_wm_stds'].append(snr_wm_std)
    
    # Create plots
    print("\nGenerating plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('WM-GM Contrast Analysis vs TE Values', fontsize=16)
    
    # Plot 1: Contrast Ratio vs Stack Number for each TE
    ax1 = axes[0, 0]
    for te_value in TE_VALUES:
        if te_value in results:
            data = results[te_value]
            ax1.plot(data['stack_numbers'], data['contrast_ratios'], 'o-', label=f'TE {te_value}ms', linewidth=2)
    ax1.set_xlabel('Number of Stacks')
    ax1.set_ylabel('WM/GM Contrast Ratio')
    ax1.set_title('Contrast Ratio vs Number of Stacks')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: CNR vs Stack Number for each TE
    ax2 = axes[0, 1]
    for te_value in TE_VALUES:
        if te_value in results:
            data = results[te_value]
            ax2.plot(data['stack_numbers'], data['cnrs'], 's-', label=f'TE {te_value}ms', linewidth=2)
    ax2.set_xlabel('Number of Stacks')
    ax2.set_ylabel('Contrast-to-Noise Ratio')
    ax2.set_title('CNR vs Number of Stacks')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: SNR GM vs Stack Number for each TE
    ax3 = axes[1, 0]
    for te_value in TE_VALUES:
        if te_value in results:
            data = results[te_value]
            ax3.plot(data['stack_numbers'], data['snr_gms'], '^-', label=f'TE {te_value}ms', linewidth=2)
    ax3.set_xlabel('Number of Stacks')
    ax3.set_ylabel('SNR Gray Matter')
    ax3.set_title('SNR GM vs Number of Stacks')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: SNR WM vs Stack Number for each TE
    ax4 = axes[1, 1]
    for te_value in TE_VALUES:
        if te_value in results:
            data = results[te_value]
            ax4.plot(data['stack_numbers'], data['snr_wms'], 'd-', label=f'TE {te_value}ms', linewidth=2)
    ax4.set_xlabel('Number of Stacks')
    ax4.set_ylabel('SNR White Matter')
    ax4.set_title('SNR WM vs Number of Stacks')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save first set of plots
    plot_filename = os.path.join(results_dir, 'wm_gm_contrast_te_analysis.png')
    plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as: {plot_filename}")
    
    # Create second set of plots: TE vs Metrics with Stack Number curves
    fig2, axes2 = plt.subplots(2, 2, figsize=(15, 12))
    fig2.suptitle('Image Quality Metrics vs TE Values (Different Stack Numbers)', fontsize=16)
    
    colors = ['blue', 'red', 'green', 'orange']
    markers = ['o', 's', '^', 'd']
    
    # Plot 1: Contrast Ratio vs TE
    ax1 = axes2[0, 0]
    for i, num_stacks in enumerate(target_stack_numbers):
        if len(te_results[num_stacks]['te_values']) > 0:
            ax1.errorbar(te_results[num_stacks]['te_values'], 
                        te_results[num_stacks]['cr_means'],
                        yerr=te_results[num_stacks]['cr_stds'],
                        marker=markers[i], color=colors[i], linewidth=2, markersize=8,
                        label=f'{num_stacks} stacks', capsize=5)
    ax1.set_xlabel('TE (ms)')
    ax1.set_ylabel('WM/GM Contrast Ratio')
    ax1.set_title('Contrast Ratio vs TE')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: CNR vs TE
    ax2 = axes2[0, 1]
    for i, num_stacks in enumerate(target_stack_numbers):
        if len(te_results[num_stacks]['te_values']) > 0:
            ax2.errorbar(te_results[num_stacks]['te_values'],
                        te_results[num_stacks]['cnr_means'],
                        yerr=te_results[num_stacks]['cnr_stds'],
                        marker=markers[i], color=colors[i], linewidth=2, markersize=8,
                        label=f'{num_stacks} stacks', capsize=5)
    ax2.set_xlabel('TE (ms)')
    ax2.set_ylabel('Contrast-to-Noise Ratio')
    ax2.set_title('CNR vs TE')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: SNR GM vs TE
    ax3 = axes2[1, 0]
    for i, num_stacks in enumerate(target_stack_numbers):
        if len(te_results[num_stacks]['te_values']) > 0:
            ax3.errorbar(te_results[num_stacks]['te_values'],
                        te_results[num_stacks]['snr_gm_means'],
                        yerr=te_results[num_stacks]['snr_gm_stds'],
                        marker=markers[i], color=colors[i], linewidth=2, markersize=8,
                        label=f'{num_stacks} stacks', capsize=5)
    ax3.set_xlabel('TE (ms)')
    ax3.set_ylabel('SNR Gray Matter')
    ax3.set_title('SNR GM vs TE')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: SNR WM vs TE
    ax4 = axes2[1, 1]
    for i, num_stacks in enumerate(target_stack_numbers):
        if len(te_results[num_stacks]['te_values']) > 0:
            ax4.errorbar(te_results[num_stacks]['te_values'],
                        te_results[num_stacks]['snr_wm_means'],
                        yerr=te_results[num_stacks]['snr_wm_stds'],
                        marker=markers[i], color=colors[i], linewidth=2, markersize=8,
                        label=f'{num_stacks} stacks', capsize=5)
    ax4.set_xlabel('TE (ms)')
    ax4.set_ylabel('SNR White Matter')
    ax4.set_title('SNR WM vs TE')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save second set of plots
    plot_filename2 = os.path.join(results_dir, 'wm_gm_contrast_te_vs_metrics.png')
    plt.savefig(plot_filename2, dpi=300, bbox_inches='tight')
    print(f"Second plot saved as: {plot_filename2}")
    
    # Save numerical results
    results_filename = os.path.join(results_dir, 'wm_gm_contrast_te_results.txt')
    with open(results_filename, 'w') as f:
        f.write("WM-GM Contrast Analysis Results by TE Value\n")
        f.write("=" * 50 + "\n\n")
        
        # Original results (Stack number vs metrics for each TE)
        f.write("SECTION 1: Metrics vs Stack Number for Each TE\n")
        f.write("-" * 45 + "\n")
        for te_value in sorted(results.keys()):
            data = results[te_value]
            f.write(f"\nTE {te_value} ms:\n")
            f.write(f"Number of available stacks: {len(data['stack_numbers'])}\n")
            f.write("Stacks\tContrast\tCNR\tSNR_GM\tSNR_WM\n")
            
            for i, num_stacks in enumerate(data['stack_numbers']):
                f.write(f"{num_stacks}\t{data['contrast_ratios'][i]:.4f}\t{data['cnrs'][i]:.4f}\t"
                       f"{data['snr_gms'][i]:.4f}\t{data['snr_wms'][i]:.4f}\n")
        
        # New results (TE vs metrics for each stack number)
        f.write(f"\n\nSECTION 2: Metrics vs TE for Different Stack Numbers (with variation)\n")
        f.write("-" * 65 + "\n")
        for num_stacks in target_stack_numbers:
            data = te_results[num_stacks]
            if len(data['te_values']) > 0:
                f.write(f"\n{num_stacks} Stacks:\n")
                f.write("TE(ms)\tCR_mean±std\tCNR_mean±std\tSNR_GM_mean±std\tSNR_WM_mean±std\n")
                
                for i, te in enumerate(data['te_values']):
                    f.write(f"{te}\t{data['cr_means'][i]:.3f}±{data['cr_stds'][i]:.3f}\t")
                    f.write(f"{data['cnr_means'][i]:.3f}±{data['cnr_stds'][i]:.3f}\t")
                    f.write(f"{data['snr_gm_means'][i]:.3f}±{data['snr_gm_stds'][i]:.3f}\t")
                    f.write(f"{data['snr_wm_means'][i]:.3f}±{data['snr_wm_stds'][i]:.3f}\n")
    
    print(f"Results saved as: {results_filename}")
    print("Analysis completed!")

if __name__ == "__main__":
    main()
