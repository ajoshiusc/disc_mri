import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

# Define the path to the BrainSuite Atlas
atlas = "/home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.label.nii.gz"

# Load the NIfTI label file
nifti_file_path = atlas
label_img = nib.load(nifti_file_path)
label_data = label_img.get_fdata()

# Load input data
roi_vols_3t = np.load("brainSuite_3T.npz")["roi_vols"]
roi_vols_lf = np.load("brainSuite_low_field.npz")["roi_vols"]
label_ids = np.load("brainSuite_3T.npz")["label_ids"]

# Remove unnecessary dimensions from roi_vols_lf, and remove 0 and 2000 
roi_vols_lf = roi_vols_lf[:, :, 0, 1:-1]

# remove 0 and 2000 rois from 3t data
roi_vols_3t = roi_vols_3t[:, :, 1:-1]

# Initialize an array for 3T intra-session statistics
stat_3t_intra = np.zeros(label_data.shape)

# Reshape roi_vols arrays
roi_vols_3t = roi_vols_3t.reshape(2, -1)
roi_vols_lf = roi_vols_lf.reshape(2, -1)

# Sample data for the 1st and 2nd repetitions at 0.55T and 3T
data_0_55T = {
    "First Repetition": roi_vols_lf[0],
    "Second Repetition": roi_vols_lf[1],
}

data_3T = {
    "First Repetition": roi_vols_3t[0],
    "Second Repetition": roi_vols_3t[1],
}

# Calculate the differences and means for both datasets
diff_0_55T = np.array(data_0_55T['First Repetition']) - np.array(data_0_55T['Second Repetition'])
mean_0_55T = (np.array(data_0_55T['First Repetition']) + np.array(data_0_55T['Second Repetition'])) / 2

# divide the measures by 1000 to get the volumes in cm^3
mean_0_55T = mean_0_55T / 1000
diff_0_55T = diff_0_55T / 1000


diff_3T = np.array(data_3T['First Repetition']) - np.array(data_3T['Second Repetition'])
mean_3T = (np.array(data_3T['First Repetition']) + np.array(data_3T['Second Repetition'])) / 2

# divide the measures by 1000 to get the volumes in cm^3
mean_3T = mean_3T / 1000
diff_3T = diff_3T / 1000

# Bland-Altman Plot for 0.55T with increased font size
plt.rcParams.update({'font.size': 16})
plt.figure(figsize=(8, 6))
plt.scatter(mean_0_55T, diff_0_55T, c='blue', marker='.')#, label='0.55T')
plt.axhline(np.mean(diff_0_55T), color='red', linestyle='--')#, label='Bias')
plt.axhline(np.mean(diff_0_55T) + 1.96 * np.std(diff_0_55T), color='gray', linestyle='--')#, label='Upper LoA')
plt.axhline(np.mean(diff_0_55T) - 1.96 * np.std(diff_0_55T), color='gray', linestyle='--')#, label='Lower LoA')
plt.xlabel('Mean of 1st and 2nd Repetitions (0.55T) in cm$^3$')
plt.ylabel('Difference (1st - 2nd Repetition) in cm$^3$')

# Add coefficients of variation in a box at the top right corner for 0.55T
#plt.text(0.95, 0.95, f'CV 0.55T: {np.mean(np.abs(diff_0_55T) / mean_0_55T) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)


#plt.text(0.95, 0.95, f'CV 0.55T: {np.std(mean_0_55T) / np.mean(mean_0_55T) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)
#plt.text(0.95, 0.90, f'CV Diff: {np.std(diff_0_55T) / np.mean(diff_0_55T) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)

plt.ylim(-6, 6)
plt.legend()
#plt.title('Bland-Altman Plot for 0.55T')

print("mean",np.mean(diff_0_55T), "1.96 * std dev", 1.96 * np.std(diff_0_55T))
# add mean and std dev to the plot in a box at the top center
#plt.text(0.5, 0.95, f'Mean: {np.mean(diff_0_55T):.2f}, 1.96 * Std Dev: {1.96 * np.std(diff_0_55T):.2f}', horizontalalignment='center', verticalalignment='top', transform=plt.gca().transAxes)




plt.grid(True)
plt.savefig('Bland-Altman_Plot_for_0.55T_vol_BrainSuite.png')

# Bland-Altman Plot for 3T
plt.figure(figsize=(8, 6))
plt.scatter(mean_3T, diff_3T, c='green', marker='.')#, label='3T')
plt.axhline(np.mean(diff_3T), color='red', linestyle='--')#, label='Bias')
plt.axhline(np.mean(diff_3T) + 1.96 * np.std(diff_3T), color='gray', linestyle='--')#, label='Upper LoA')
plt.axhline(np.mean(diff_3T) - 1.96 * np.std(diff_3T), color='gray', linestyle='--')#, label='Lower LoA')
plt.xlabel('Mean of 1st and 2nd Repetitions (3T) in cm$^3$')
plt.ylabel('Difference (1st - 2nd Repetition) in cm$^3$')

# Add coefficients of variation in a box at the top right corner for 3T
#plt.text(0.95, 0.95, f'CV 3T: {np.mean(np.abs(diff_3T) / mean_3T) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)

#plt.text(0.95, 0.95, f'CV 3T: {np.std(mean_3T) / np.mean(mean_3T) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)
#plt.text(0.95, 0.90, f'CV Diff: {np.std(diff_3T) / np.mean(diff_3T) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)

# Add legend
plt.ylim(-6, 6)
plt.legend()
#plt.title('Bland-Altman Plot for 3T')

print("mean",np.mean(diff_3T), "1.96 * std dev", 1.96 * np.std(diff_3T))
# add mean and std dev to the plot in a box at the top center
#plt.text(0.5, 0.95, f'Mean: {np.mean(diff_3T):.2f}, 1.96 * Std Dev: {1.96 * np.std(diff_3T):.2f}', horizontalalignment='center', verticalalignment='top', transform=plt.gca().transAxes)


plt.grid(True)
plt.savefig('Bland-Altman_Plot_for_3T_vol_BrainSuite.png')

# Calculate the means for both datasets
mean_0_55T = (np.array(data_0_55T['First Repetition']) + np.array(data_0_55T['Second Repetition'])) / 2
mean_3T = (np.array(data_3T['First Repetition']) + np.array(data_3T['Second Repetition'])) / 2

# Divide the measures by 1000 to get the volumes in cm^3
mean_0_55T = mean_0_55T / 1000 # convert to cm^3
mean_3T = mean_3T / 1000 # convert to cm^3

# Calculate the differences between means
diff_means = mean_0_55T - mean_3T

# Bland-Altman Plot comparing averages of repetitions for 0.55T and 3T, show coefficients of variation

plt.figure(figsize=(8, 6))
plt.scatter(mean_0_55T, diff_means, c='purple', marker='.')#, label='0.55T vs. 3T')
plt.axhline(np.mean(diff_means), color='red', linestyle='--')#, label='Bias')
plt.axhline(np.mean(diff_means) + 1.96 * np.std(diff_means), color='gray', linestyle='--')#, label='Upper LoA')
plt.axhline(np.mean(diff_means) - 1.96 * np.std(diff_means), color='gray', linestyle='--')#, label='Lower LoA')
plt.xlabel('Mean of Means of 0.55T and 3T in cm$^3$')
plt.ylabel('Difference in Means (0.55T - 3T) in cm$^3$')



# Add coefficients of variation in a box at the top right corner
#plt.text(0.95, 0.95, f'CV 3T vs 0.55T: {np.mean(np.abs(diff_means) / (mean_0_55T + mean_3T)/2) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)


#plt.text(0.95, 0.95, f'CV 0.55T: {np.std(mean_0_55T) / np.mean(mean_0_55T) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)
#plt.text(0.95, 0.90, f'CV 3T: {np.std(mean_3T) / np.mean(mean_3T) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)
#plt.text(0.95, 0.85, f'CV Diff: {np.std(diff_means) / np.mean(diff_means) * 100:.2f}%', horizontalalignment='right', verticalalignment='top', transform=plt.gca().transAxes)

# Add legend
plt.ylim(-6, 6)
plt.legend()

print("mean",np.mean(diff_means), "1.96 * std dev", 1.96 * np.std(diff_means))
# add mean and std dev to the plot in a box at the top center
#plt.text(0.5, 0.95, f'Mean: {np.mean(diff_means):.2f}, 1.96 * Std Dev: {1.96 * np.std(diff_means):.2f}', horizontalalignment='center', verticalalignment='top', transform=plt.gca().transAxes)




#plt.title('Bland-Altman Plot: 0.55T vs. 3T')
plt.grid(True)
plt.savefig('Bland-Altman_Plot_0.55T_vs_3T_vol_BrainSuite.png')

# Show the plots
plt.show()
