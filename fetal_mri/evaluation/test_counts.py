import json

with open("/home/ajoshi/Projects/disc_mri/fetal_mri/real_error_bar_data.json") as f:
    data = json.load(f)
    print(data["98"]["12"])
