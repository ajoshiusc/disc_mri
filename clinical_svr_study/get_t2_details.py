import os
import pydicom
import glob
import pandas as pd

data_dir = "/home/ajoshi/project2_ajoshi_27/data/clinical_svr_chla_data/clinical_svr_dicom/"
subject_dirs = [os.path.join(data_dir, d) for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d)) and d.lower().startswith("svr")]

t2_data = []

for subj_dir in subject_dirs:
    for exam_name in os.listdir(subj_dir):
        exam_path = os.path.join(subj_dir, exam_name)
        if not os.path.isdir(exam_path): continue
        
        for series_name in os.listdir(exam_path):
            if "SSh_TSE" not in series_name: continue
            
            series_path = os.path.join(exam_path, series_name)
            if not os.path.isdir(series_path): continue
            
            dicom_file = None
            for f in os.listdir(series_path):
                if not f.startswith('.') and not f.endswith('.zip') and not os.path.isdir(os.path.join(series_path, f)):
                    dicom_file = os.path.join(series_path, f)
                    break
            
            if dicom_file:
                try:
                    dcm = pydicom.dcmread(dicom_file, stop_before_pixels=True)
                    t2_data.append({
                        'Series': series_name,
                        'TR': getattr(dcm, 'RepetitionTime', None),
                        'TE': getattr(dcm, 'EchoTime', None),
                        'Thickness': getattr(dcm, 'SliceThickness', None),
                        'SpacingBetweenSlices': getattr(dcm, 'SpacingBetweenSlices', None),
                        'PixelSpacing': str(getattr(dcm, 'PixelSpacing', None)),
                        'Rows': getattr(dcm, 'Rows', None),
                        'Columns': getattr(dcm, 'Columns', None),
                        'FlipAngle': getattr(dcm, 'FlipAngle', None),
                        'EchoTrainLength': getattr(dcm, 'EchoTrainLength', None),
                    })
                except Exception:
                    pass

df = pd.DataFrame(t2_data)
print("Total T2 scans analyzed:", len(df))
print("\nStats:")
for col in ['TR', 'TE', 'Thickness', 'SpacingBetweenSlices', 'PixelSpacing', 'Rows', 'Columns', 'FlipAngle', 'EchoTrainLength']:
    print(f"--- {col} ---")
    print(df[col].value_counts())
