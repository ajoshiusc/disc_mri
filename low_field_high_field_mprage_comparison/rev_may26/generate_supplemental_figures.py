import numpy as np
import matplotlib.pyplot as plt

def fractional_bland_altman(name1, data_path1, name2, data_path2, out_name):
    # Load BrainSuite and FreeSurfer data
    # We will do test-retest fractional. 
    # But wait, review says "excellent correlation between field strengths...". 
    # Ah! Justin's normalized Bland Altman is for test-retest or 3T vs 0.55T?
    # "how you're planning to calculate or display the coefficient of variation... 
    # what if you created another Bland-Altman style plot... normalized by mean value"
    # Test-retest is easiest for CV, but let's do Test-Retest Normalized BA plots.
    pass
