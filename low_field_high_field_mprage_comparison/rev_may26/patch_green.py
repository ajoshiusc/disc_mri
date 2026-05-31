import re

with open('/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/justin_magma_comparison/Main/manuscript.tex', 'r') as f:
    text = f.read()

# 1. Abstract change
text = re.sub(r'\\noindent \\textbf\{Results:\}.+?and the software tool that was used\.',
r'\\noindent \\textbf{Results:} For both image analysis software tools, we \textcolor{green}{found relatively good agreement between field strengths for regional morphological measures, although test-retest repeatability analysis suggests that experimental variability was generally higher at 0.55T than at 3T (e.g., volume within-subject coefficient of variation (wCV) was roughly 5.3--5.6\\% at 0.55T compared to 3.3--3.8\\% at 3T). The amount of difference was dependent on the specific measure being considered and the software tool that was used.}', text, flags=re.DOTALL)

# 2. Results change R^2
text = text.replace(
r'and $R^2>0.99$ for volume measures in both cases).',
r'and $R^2>0.99$ for volume measures in both cases\textcolor{green}{\mycomment{R1.1}, although note that this volume correlation is computed across varying anatomy structure sizes that span orders of magnitude}).'
)

# 3. Test-retest change
text = text.replace(
r'This suggests that repeatability is worse at 0.55T than it is at 3T, as should be expected.',
r'This suggests that repeatability is worse at 0.55T than it is at 3T, as should be expected. \textcolor{green}{\mycomment{R1.1} Since the limits of agreement for regional volume vary significantly by structure size, we also evaluated the within-subject coefficient of variation (wCV) for regional volume repeatability. The mean volume repeatability wCV was 5.26\% at 0.55T versus 3.76\% at 3T for BrainSuite, and 5.63\% at 0.55T versus 3.26\% at 3T for FreeSurfer.}'
)

with open('/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/justin_magma_comparison/Main/manuscript.tex', 'w') as f:
    f.write(text)
