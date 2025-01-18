import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt


# Load data
roi_surf_3t = np.load("brainSuite_3T.npz")["roi_thickness_3t"]
roi_surf_lf = np.load("brainSuite_low_field.npz")["roi_thickness_lf"]
label_ids = np.load("brainSuite_3T.npz")["cortical_label_ids"]


roi_surf_lf = roi_surf_lf[:, :, 0, :]

#roi_surf_3t = roi_surf_3t[:,(3)]
#roi_surf_lf = roi_surf_lf[:,(3)]

# Reshape roi_vols arrays
roi_surf_3t = roi_surf_3t.reshape(2, -1)
roi_surf_lf = roi_surf_lf.reshape(2, -1)

# Sample data for the 1st and 2nd repetitions at 0.55T and 3T
data_0_55T = {
    "First Repetition": roi_surf_lf[0],
    "Second Repetition": roi_surf_lf[1],
}

data_3T = {
    "First Repetition": roi_surf_3t[0],
    "Second Repetition": roi_surf_3t[1],
}

# Calculate the differences and means for both datasets
diff_0_55T = np.array(data_0_55T['First Repetition']) - np.array(data_0_55T['Second Repetition'])
mean_0_55T = (np.array(data_0_55T['First Repetition']) + np.array(data_0_55T['Second Repetition'])) / 2

diff_3T = np.array(data_3T['First Repetition']) - np.array(data_3T['Second Repetition'])
mean_3T = (np.array(data_3T['First Repetition']) + np.array(data_3T['Second Repetition'])) / 2

# Bland-Altman Plot (thickness) for 0.55T with increased font size
plt.rcParams.update({'font.size': 16})
plt.figure(figsize=(9, 6))
plt.scatter(mean_0_55T, diff_0_55T, c='blue', marker='.')#, label='0.55T')
plt.axhline(np.mean(diff_0_55T), color='red', linestyle='--')#, label='Bias')
plt.axhline(np.mean(diff_0_55T) + 1.96 * np.std(diff_0_55T), color='gray', linestyle='--')#, label='Upper LoA')
plt.axhline(np.mean(diff_0_55T) - 1.96 * np.std(diff_0_55T), color='gray', linestyle='--')#, label='Lower LoA')
plt.xlabel('Mean of 1st and 2nd Repetitions (0.55T) in mm')
plt.ylabel('Difference (1st - 2nd Repetition) in mm')
plt.ylim(-1, 1)
plt.legend()
#plt.title('Bland-Altman Plot (thickness) for 0.55T')
print("mean",np.mean(diff_0_55T), "1.96 * std dev", 1.96 * np.std(diff_0_55T))
# add mean and std dev to the plot in a box at the top center
#plt.text(0.5, 0.95, f'Mean: {np.mean(diff_0_55T):.2f}, 1.96 * Std Dev: {1.96 * np.std(diff_0_55T):.2f}', horizontalalignment='center', verticalalignment='top', transform=plt.gca().transAxes)

# Add coefficients of variation in a box at the top right corner for 0.55T
#plt.text(0.95, 0.95, f'CV 0.55T: {np.mean(np.abs(diff_0_55T) / (mean_0_55T+1e-6)) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)

plt.grid(True)
plt.savefig('Bland-Altman_Plot_thickness_for_0.55T_BrainSuite.png')

# Bland-Altman Plot (thickness) for 3T
plt.figure(figsize=(9, 6))
plt.scatter(mean_3T, diff_3T, c='green', marker='.')#, label='3T')
plt.axhline(np.mean(diff_3T), color='red', linestyle='--')#, label='Bias')
plt.axhline(np.mean(diff_3T) + 1.96 * np.std(diff_3T), color='gray', linestyle='--')#, label='Upper LoA')
plt.axhline(np.mean(diff_3T) - 1.96 * np.std(diff_3T), color='gray', linestyle='--')#, label='Lower LoA')
plt.xlabel('Mean of 1st and 2nd Repetitions (3T) in mm')
plt.ylabel('Difference (1st - 2nd Repetition) in mm')
plt.ylim(-1, 1)
plt.legend()
#plt.title('Bland-Altman Plot (thickness) for 3T')
print("mean",np.mean(diff_3T), "1.96 * std dev", 1.96 * np.std(diff_3T))
# add mean and std dev to the plot in a box at the top center
#plt.text(0.5, 0.95, f'Mean: {np.mean(diff_3T):.2f}, 1.96 * Std Dev: {1.96 * np.std(diff_3T):.2f}', horizontalalignment='center', verticalalignment='top', transform=plt.gca().transAxes)

# Add coefficients of variation in a box at the top right corner for 3T
#plt.text(0.95, 0.95, f'CV 3T: {np.mean(np.abs(diff_3T) / (mean_3T+1e-6)) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)

plt.grid(True)
plt.savefig('Bland-Altman_Plot_thickness_for_3T_BrainSuite.png')

# Calculate the means for both datasets
mean_0_55T = (np.array(data_0_55T['First Repetition']) + np.array(data_0_55T['Second Repetition'])) / 2
mean_3T = (np.array(data_3T['First Repetition']) + np.array(data_3T['Second Repetition'])) / 2

# Calculate the differences between means
diff_means = mean_0_55T - mean_3T

# Bland-Altman Plot (thickness) comparing averages of repetitions for 0.55T and 3T
plt.figure(figsize=(9, 6))
plt.scatter(mean_0_55T, diff_means, c='purple', marker='.')#, label='0.55T vs. 3T')
plt.axhline(np.mean(diff_means), color='red', linestyle='--')#, label='Bias')
plt.axhline(np.mean(diff_means) + 1.96 * np.std(diff_means), color='gray', linestyle='--')#, label='Upper LoA')
plt.axhline(np.mean(diff_means) - 1.96 * np.std(diff_means), color='gray', linestyle='--')#, label='Lower LoA')
plt.xlabel('Mean of Means of 0.55T and 3T in mm')
plt.ylabel('Difference in Means (0.55T - 3T) in mm')
plt.ylim(-1, 1)
plt.legend()

print("mean",np.mean(diff_means), "1.96 * std dev", 1.96 * np.std(diff_means))
# Add mean and std dev to the plot in a box at the top center
#plt.text(0.5, 0.95, f'Mean: {np.mean(diff_means):.2f}, Std Dev: {np.std(diff_means):.2f}', horizontalalignment='center', verticalalignment='top', transform=plt.gca().transAxes)

# Add coefficients of variation in a box at the top right corner for 0.55T vs 3T
#plt.text(0.95, 0.95, f'CV 0.55T vs 3T: {np.mean(np.abs(diff_means) / ((mean_0_55T + mean_3T+1e-6)/2.0)) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)

#plt.title('Bland-Altman Plot (thickness): 0.55T vs. 3T')
plt.grid(True)
plt.savefig('Bland-Altman_Plot_thickness_0.55T_vs_3T_BrainSuite.png')

# Show the plots
#plt.show()
