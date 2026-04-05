import json

# Just a script that re-runs the data collection part to see how many subjects we actually have per stack
import os, glob, re
SUBJECTS = {
    "subj_8_11_2023": ("/deneb_disk/disc_mri/scan_8_11_2023/outsvr", "svr_te{te}*numstacks_*"),                                                                     
    "subj_9_12_2023": ("/deneb_disk/disc_mri/scan_9_12_2023/outsvr", "svr_te{te}*numstacks_*"),                                                                     
    "subj_11_3_2023_babya": ("/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr", "svr_te{te}_babya*numstacks_*"),                                           
    "subj_11_3_2023_babyb": ("/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr", "svr_te{te}_babyb*numstacks_*"),                                           
    "subj_3_20_2024": ("/deneb_disk/disc_mri/scan_3_20_2024/outsvr", "svr_te{te}*numstacks_*"),                                                                     
    "subj_10_23_2025": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_10_23_2025/outsvr", "svr_te{te}*numstacks_*"),                                          
    "subj_12_03_2025": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_12_03_2025/outsvr", "svr_te{te}*numstacks_*"),                                          
    "subj_1_8_2026": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_1_8_2026/outsvr", "svr_te{te}*numstacks_*"),                                              
    "subj_2_6_2026": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_2_6_2026/outsvr", "svr_te{te}*numstacks_*"),                                              
    "subj_2_9_2026": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_2_9_2026/outsvr", "svr_te{te}*numstacks_*"),                                          
}

TE_VALUES = [98, 140, 181, 272]
data_counts = {te: {} for te in TE_VALUES}

def get_subject_files(d, pat_template, te):
    pat = pat_template.format(te=te)
    search_path = os.path.join(d, pat)
    files = glob.glob(search_path)
    stack_files = {}
    for f in files:
        if "aligned" in f or "mask" in f: continue
        m = re.search(r'numstacks_(\d+)', f)
        if m:
            s_num = int(m.group(1))
            if s_num not in stack_files: stack_files[s_num] = []
            stack_files[s_num].append(f)
    return stack_files

for subj_name, (d, pat) in SUBJECTS.items():
    for te in TE_VALUES:
        stack_files = get_subject_files(d, pat, te)
        if stack_files:
            max_stacks = max(stack_files.keys())
            for stacks in stack_files:
                if stacks not in data_counts[te]: data_counts[te][stacks] = 0
                data_counts[te][stacks] += 1

print("Available subject count points per TE/Stack tuple:")
for te in TE_VALUES:
    for stack in sorted(data_counts[te].keys()):
        if stack in [3,6,9,12]:
            print(f"TE {te}, Stack {stack}: {data_counts[te][stack]} subjects")

