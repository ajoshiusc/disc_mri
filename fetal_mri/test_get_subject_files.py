import re

files = [
    "svr_te98_numstacks_3_iter_0.nii.gz",
    "svr_te98_numstacks_3_iter_10.nii.gz",
    "svr_te98_numstacks_3_iter_19.nii.gz",
    "svr_te98_numstacks_12_iter_19.nii.gz"
]

stack_files = {}
for f in files:
    m = re.search(r'numstacks_(\d+)_(?:iter_)?(\d+)', f)
    if m:
        stacks, it = int(m.group(1)), int(m.group(2))
        if stacks not in stack_files:
            stack_files[stacks] = []
        stack_files[stacks].append((it, f))

# Only keep the max iteration file
final_dict = {}
for stacks, it_list in stack_files.items():
    best = max(it_list, key=lambda x: x[0])
    final_dict[stacks] = best[1]

print(final_dict)
