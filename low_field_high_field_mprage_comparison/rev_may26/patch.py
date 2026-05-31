with open('/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/justin_magma_comparison/Main/manuscript.tex', 'r') as f:
    text = f.read()

import re
text = re.sub(r'\\noindent \\textbf\{Results:\}.+?and the software tool that was used\.',
r'\\noindent \\textbf{Results:} For both image analysis software tools, we found relatively good agreement between field strengths for regional morphological measures, although test-retest repeatability analysis suggests that experimental variability was generally higher at 0.55T than at 3T (e.g., volume repeatability coefficient of variation was roughly 4.3--4.4\\% at 0.55T compared to 2.9--3.1\\% at 3T). The amount of difference was dependent on the specific measure being considered and the software tool that was used.', text, flags=re.DOTALL)

with open('/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/justin_magma_comparison/Main/manuscript.tex', 'w') as f:
    f.write(text)
