with open('/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/justin_magma_comparison/Main/manuscript.tex', 'r') as f:
    text = f.read()

import re
text = text.replace(
r'and $R^2>0.99$ for volume measures in both cases).',
r'and $R^2>0.99$ for volume measures in both cases\textcolor{blue}{\mycomment{R1.1}, although note that this volume correlation is computed across varying anatomy structure sizes that span orders of magnitude}).'
)

text = text.replace(
r'This suggests that repeatability is worse at 0.55T than it is at 3T, as should be expected.',
r'This suggests that repeatability is worse at 0.55T than it is at 3T, as should be expected. \textcolor{blue}{\mycomment{R1.1} Since the limits of agreement for regional volume vary significantly by structure size, we also evaluated the coefficient of variation (CV) for regional volume repeatability.  The mean volume repeatability CV was 4.29\% at 0.55T versus 3.09\% at 3T for BrainSuite, and 4.40\% at 0.55T versus 2.95\% at 3T for FreeSurfer.}'
)

with open('/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/justin_magma_comparison/Main/manuscript.tex', 'w') as f:
    f.write(text)
