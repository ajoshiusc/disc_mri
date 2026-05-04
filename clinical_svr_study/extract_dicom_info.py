import os
import pydicom
import glob
import pandas as pd
from collections import defaultdict

data_dir = "/home/ajoshi/project2_ajoshi_27/data/clinical_svr_chla_data/clinical_svr_dicom/"

demographics = []
protocols = []

# Find all SVR directories
try:
    subject_dirs = [os.path.join(data_dir, d) for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d)) and d.startswith("SVR")]
except Exception as e:
    print("Error reading directories:", e)
    import sys; sys.exit(1)

for subj_dir in subject_dirs:
    found_demographics = False
    processed_series = set()
    files_checked = 0
    
    # Just look for dicoms in some subdirectories
    for root, _, files in os.walk(subj_dir):
        if files_checked > 100: # limit to avoid hanging
            break
            
        for file in files:
            if file.startswith('.') or file.endswith('.zip') or file.endswith('.py') or file.endswith('.txt'):
                continue
                
            filepath = os.path.join(root, file)
            files_checked += 1
            try:
                # Read only header to be fast
                dcm = pydicom.dcmread(filepath, stop_before_pixels=True, force=True)
                
                # Extract demographics once per subject
                if not found_demographics:
                    age = getattr(dcm, 'PatientAge', 'N/A')
                    sex = getattr(dcm, 'PatientSex', 'N/A')
                    weight = getattr(dcm, 'PatientWeight', 'N/A')
                    if age != 'N/A' or sex != 'N/A':
                        demographics.append({
                            'Subject': os.path.basename(subj_dir),
                            'Age': age,
                            'Sex': sex,
                            'Weight': weight
                        })
                        found_demographics = True
                
                # Extract protocol details for each series
                series_uid = getattr(dcm, 'SeriesInstanceUID', None)
                if series_uid and series_uid not in processed_series:
                    processed_series.add(series_uid)
                    desc = getattr(dcm, 'SeriesDescription', 'Unknown')
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
                pass # not a valid dicom

demo_df = pd.DataFrame(demographics)
proto_df = pd.DataFrame(protocols)

if len(demo_df) > 0:
    print("=== Demographics ===")
    print(f"Total subjects extracted: {len(demo_df)}")
    print("Sex Counts:\n", demo_df['Sex'].value_counts())
    print("\nAge Counts:\n", demo_df['Age'].value_counts())
    
    print("\n=== Scan Protocols ===")
    print("Field Strengths:\n", proto_df['FieldStrength'].value_counts())
    print("Manufacturers:\n", proto_df['Manufacturer'].value_counts())
    print("Models:\n", proto_df['Model'].value_counts())
    print("\nCommon Series:")
    print(proto_df['SeriesDescription'].value_counts().head(15))

    print("\nTypical TR/TE/Thickness for top couple series:")
    for desc in proto_df['SeriesDescription'].value_counts().head(5).index:
        subset = proto_df[proto_df['SeriesDescription'] == desc]
        print(f"\nSeries: {desc}")
        try:
            print(f"  TR mode: {subset['TR'].mode().iloc[0] if len(subset['TR'].mode()) > 0 else 'N/A'}")
            print(f"  TE mode: {subset['TE'].mode().iloc[0] if len(subset['TE'].mode()) > 0 else 'N/A'}")
            print(f"  Thickness mode: {subset['Thickness'].mode().iloc[0] if len(subset['Thickness'].mode()) > 0 else 'N/A'}")
        except:
            print("  Error getting mode")
else:
    print("No demographics found!")
