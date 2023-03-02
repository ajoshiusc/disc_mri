"""
nii2dcm runner
"""
import nibabel as nib

import nii2dcm.dcm_writer
import nii2dcm.nii
import nii2dcm.svr
import os
import glob

def run_nii2dcm(input_nii_path, output_dcm_path, dicom_type=None,patient_name=''):
    """
    Execute NIfTI to DICOM conversion

    :param input_nii_path: input .nii/.nii.gz file
    :param output_dcm_path: output DICOM directory
    :param dicom_type: specified by user on command-line
    """

    # load NIfTI
    nii = nib.load(input_nii_path)

    # get pixel data from NIfTI
    # TODO: create method in nii class
    nii_img = nii.get_fdata()
    nii_img = nii_img.astype("uint16")  # match DICOM datatype

    # get NIfTI parameters
    nii2dcm_parameters = nii2dcm.nii.Nifti.get_nii2dcm_parameters(nii)

    # initialise nii2dcm.dcm object
    # --dicom_type specified on command line
    if dicom_type is None:
        dicom = nii2dcm.dcm.Dicom('nii2dcm_dicom.dcm')
    if dicom_type is not None and dicom_type.upper() in ['MR', 'MRI']:
        dicom = nii2dcm.dcm.DicomMRI('nii2dcm_dicom_mri.dcm')
    if dicom_type is not None and dicom_type.upper() in ['SVR']:

        example_dicom = '/deneb_disk/chla_data_2_21_2023/unzipped_dicomms/SVR010/Mri_Fetal__Pelvic - MRIFETAL/BRAIN_SAG_SSh_TSE_esp56_1701/IM-0274-0044.dcm'
        dicom = nii2dcm.svr.DicomMRISVR(example_dicom,patient_name=patient_name) #('nii2dcm_dicom_mri_svr.dcm')
        nii_img = nii.get_fdata()
        #nii_img *= 65534.0/nii_img.max()
        nii_img *= 32000.0/nii_img.max()

        nii_img[nii_img < 0] = 0  # set background pixels = 0 (negative in SVRTK)
        nii_img = nii_img.astype("int16")

    # transfer Series tags
    nii2dcm.dcm_writer.transfer_nii_hdr_series_tags(dicom, nii2dcm_parameters)

    # write DICOM files, instance-by-instance

    print('nii2dcm: writing DICOM files ...')

    for instance_index in range(0, nii2dcm_parameters['NumberOfInstances']):

        # Transfer Instance tags
        nii2dcm.dcm_writer.transfer_nii_hdr_instance_tags(dicom, nii2dcm_parameters, instance_index)

        # Write slice
        nii2dcm.dcm_writer.write_slice(dicom, nii_img, instance_index, output_dcm_path)



def main():

    list_svr_files = glob.glob('/home/ajoshi/projects/disc_mri/clinical_svr_study/SVR_3D_NIFTI/SVR*SVR.nii.gz')
    out_dicomms = '/home/ajoshi/projects/disc_mri/clinical_svr_study/SVR_3D_DICOM_test4'

    for nii_file in list_svr_files:
    
        sub = os.path.basename(nii_file)[:-7]

        output_dcm_path = out_dicomms + '/' + sub + '_3D'
        os.makedirs(output_dcm_path)
        
        run_nii2dcm(nii_file, output_dcm_path, dicom_type='SVR', patient_name=sub[:-4])


if __name__ == "__main__":
    main()