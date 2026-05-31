import re

with open('supplementary_material.tex', 'r') as f:
    text = f.read()

new_block = r"""
\vspace{1cm}

\begin{figure}[h!]
\centering
\includegraphics[width=\textwidth]{supplementary_wcv_volume_slices.pdf}
\caption{Supplemental volumetric cross-sections of the BrainSuite atlas, color-coded by the regional within-subject coefficient of variation (wCV) for test-retest measurements acquired at 0.55T and 3T. The colorization visually highlights how measurement precision varies spatially and by geometric structural dimensions across the brain.}
\end{figure}

\end{document}
"""

text = text.replace(r'\end{document}', new_block)

with open('supplementary_material.tex', 'w') as f:
    f.write(text)

