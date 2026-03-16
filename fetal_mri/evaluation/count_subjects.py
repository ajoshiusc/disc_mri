import json

with open("/home/ajoshi/Projects/disc_mri/fetal_mri/real_error_bar_data.json") as f:
    data = json.load(f)
    print("98 TE:")
    for stack in ["3", "6", "9", "12"]:
        if stack in data["98"]:
            print(f"Stack {stack}: NMSE mean: {data['98'][stack]['nmse_mean']}, std: {data['98'][stack]['nmse_std']}")

