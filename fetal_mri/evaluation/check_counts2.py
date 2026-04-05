import os, glob, re
SUBJECTS = {
    "subj_8_11_2023": ("/deneb_disk/disc_mri/scan_8_11_2023/outsvr", "svr_te{te}*numstacks_*"),                                                                     
    "subj_9_12_2023": ("/deneb_disk/disc_mri/scan_9_12_2023/outsvr", "svr_te{te}*numstacks_*"),                                                                     
    "subj_11_3_2023_babya": ("/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr", "svr_te{te}_babya*numstacks_*"),                                           
    "subj_11_3_2023_babyb": ("/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr", "svr_te{te}_babyb*numstacks_*"),                                           
}
TE_VALUES = [98]
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

print("fpath per stack per subject:")
for subj_name, (d, pat) in SUBJECTS.items():
    res = get_subject_files(d, pat, 98)
    for stack in [3,6,9,12]:
        if stack in res:
            print(f"{subj_name}, Stack {stack}: count = {len(res[stack])}")

