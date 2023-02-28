"""
Classes for creating 3D MRI SVR DICOMs

Tom Roberts
"""

from nii2dcm.dcm import DicomMRI, nii2dcm_temp_filename


class DicomMRISVR(DicomMRI):
    """
    Creates 3D Slice-to-Volume Registration reconstruction DICOM
    """

    def __init__(self, filename=nii2dcm_temp_filename, patient_name=''):
        super().__init__(filename)

        self.ds.MRAcquisitionType = '3D'
        self.ds.NumberOfPhaseEncodingSteps = ''
        self.ds.PercentPhaseFieldOfView = ''
        self.ds.BitsAllocated = 16
        self.ds.Manufacturer = "Philips Medical Systems"
        self.ds.SamplesPerPixel = 1
        self.ds.PatientName = patient_name
        self.ds.PatientID=''

        self.ds.BitsStored = 16
        self.ds.HighBit = 15
        self.ds.PixelRepresentation = 1


