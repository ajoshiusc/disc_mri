import os
import glob
import pydicom
import pandas as pd

data_dir = "/home/ajoshi/project2_ajoshi_27/data/clinical_svr_chla_data/clinical_svr_dicom/"

subject_dirs = [os.path.join(data_dir, d) for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d)) and d.lower().startswith("svr")]

demographics = []
protocols = []

for subj_dir in subject_dirs:
    found_demo = False
    
    # In each SVR dir, there is usually an exam dir (like Mri_Fetal__Pelvic), and then series dirs.
    # We will just traverse 3 levels down and pick 1 dicom per series dir.
    # Level 1: SVR001
    for exam_name in os.listdir(subj_dir):
        exam_path = os.path.join(subj_dir, exam_name)
        if not os.path.isdir(exam_path): continue
        
        # Level 2: Series Dirs (e.g. AXIAL_BRAIN_...)
        for series_name in os.listdir(exam_path):
            series_path = os.path.join(exam_path, series_name)
            if not os.path.isdir(series_path): continue
            
            # Level 3: Files inside Series Dir
            files = os.listdir(series_path)
            dicom_file = None
            for f in files:
                if not f.startswith('.') and not f.endswith('.zip') and not os.path.isdir(os.path.join(series_path, f)):
                    dicom_file = os.path.join(series_path, f)
                    break
            
            if dicom_file:
                try:
                    dcm = pydicom.dcmread(dicom_file, stop_before_pixels=True)
                    
                    if not found_demo:
                        age = getattr(dcm, 'PatientAge', 'N/A')
                        sex = getattr(dcm, 'PatientSex', 'N/A')
                        weight = getattr(dcm, 'PatientWeight', 'N/A')
                        demographics.append({
                            'Subject': os.path.basename(subj_dir),
                            'Age': age,
                            'Sex': sex,
                            'Weight': weight
                        })
                        found_demo = True
                        
                    desc = getattr(dcm, 'SeriesDescription', series_name)
                    tr = getattr(dcm, 'RepetitionTime', 'N/A')
                    te = getattr(dcm, 'EchoTime', 'N/A')
                    thick = getattr(dcm, 'SliceThickness', 'N/A')
                    mag = getattr(dcm, 'MagneticFieldStrength', 'N/A')
                    mfg = getattr(dcm, 'Manufacturer', 'N/A')
                    model = getattr(dcm, 'ManufacturerModelName', 'N/A')
                    
                    protocols.append({
                        'Subject': os.path.basename(subj_dir),
                        'SeriesDescription': desc,
                        'TR': tr,
                        'TE': te,
                        'Thickness': thick,
                        'FieldStrength': mag,
                        'Manufacturer': mfg,
                        'Model': model
                    })
                except Exception as e:
                    pass

demo_df = pd.DataFrame(demographics)
proto_df = pd.DataFrame(protocols)

print("=== Demographics ===")
print(demo_df.head())
print("\nDescriptive stats:")
print(demo_df.describe(include='all'))
print("\nUnique Ages:", demo_df['Age'].value_counts())
print("\nUnique Sex:", demo_df['Sex'].value_counts())

print("\n=== Protocols ===")
print("Field Strengths:\n", proto_df['FieldStrength'].value_counts())
print("Manufacturers:\n", proto_df['Manufacturer'].value_counts())
print("Models:\n", proto_df['Model'].value_counts())

print("\nTop 15 Scans:")
print(proto_df['SeriesDescription'].value_counts().head(15))

print("\nScan details for top 5 scans:")
for desc in proto_df['SeriesDescription'].value_counts().head(5).index:
    subset = proto_df[proto_df['SeriesDescription'] == desc]
    print(f"\n{desc}:")
    try:
        print(f"  Field: {subset['FieldStrength'].mode().iloc[0] if len(subset['FieldStrength'].mode())>0 else 'N/A'}T")
        print(f"  TR mode: {subset['TR'].mode().iloc[0] if len(subset['TR'].mode())>0 else 'N/A'} ms")
        print(f"  TE mode: {subset['TE'].mode().iloc[0] if len(subset['TE'].mode())>0 else 'N/A'} ms")
        print(f"  Thickness mode: {subset['Thickness'].mode().iloc[0] if len(subset['Thickness'].mode())>0 else 'N/A'} mm")
    except: pass

