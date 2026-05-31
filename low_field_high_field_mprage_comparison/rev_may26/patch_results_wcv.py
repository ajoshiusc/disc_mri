import re

with open('/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/justin_magma_comparison/Main/manuscript.tex', 'r') as f:
    text = f.read()

text = text.replace(
r'volume repeatability coefficient of variation was roughly 4.3--4.4\% at 0.55T compared to 2.9--3.1\% at 3T).',
r'volume within-subject coefficient of variation (wCV) was roughly 5.3--5.6\% at 0.55T compared to 3.3--3.8\% at 3T).'
)

text = text.replace(
r'the coefficient of variation (CV) for regional volume repeatability.  The mean volume repeatability CV was 4.29\% at 0.55T versus 3.09\% at 3T for BrainSuite, and 4.40\% at 0.55T versus 2.95\% at 3T for FreeSurfer.',
r'the within-subject coefficient of variation (wCV) for regional volume repeatability.  The mean volume repeatability wCV was 5.26\% at 0.55T versus 3.76\% at 3T for BrainSuite, and 5.63\% at 0.55T versus 3.26\% at 3T for FreeSurfer.'
)

with open('/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/justin_magma_comparison/Main/manuscript.tex', 'w') as f:
    f.write(text)

with open('/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/rev_may26/Draft_Response.txt', 'r') as f:
    resp = f.read()

resp = resp.replace(
r'coefficient of variation (CV) metrics to quantify volume test-retest repeatability.',
r'within-subject coefficient of variation (wCV) metrics to quantify volume test-retest repeatability.'
)

resp = resp.replace(
r'repeatability coefficient of variation (CV) for the volume measures and added these metrics to the text covering the volume Bland-Altman test-retest results. Specifically, we added a note that the mean volume repeatability CV was 4.29% at 0.55T versus 3.09% at 3T for BrainSuite processing, and 4.40% at 0.55T versus 2.95% at 3T for FreeSurfer processing.',
r'within-subject repeatability coefficient of variation (wCV) for the volume measures and added these metrics to the text covering the volume Bland-Altman test-retest results. Specifically, we added a note that the mean volume repeatability wCV was 5.26% at 0.55T versus 3.76% at 3T for BrainSuite processing, and 5.63% at 0.55T versus 3.26% at 3T for FreeSurfer processing.'
)

resp = resp.replace(
r'coefficient of variation (CV) for the regional volume repeatability',
r'within-subject coefficient of variation (wCV) for the regional volume repeatability'
)

resp = resp.replace(
r'coefficient of variation (CV) metrics to quantify',
r'within-subject coefficient of variation (wCV) metrics to quantify'
)


with open('/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/rev_may26/Draft_Response.txt', 'w') as f:
    f.write(resp)
