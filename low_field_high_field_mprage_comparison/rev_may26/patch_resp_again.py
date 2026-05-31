import re

with open('response_to_reviewers.tex', 'r') as f:
    resp = f.read()

new_bullet = r"""    \item \textcolor{blue}{\textbf{Supplemental Material:} As an additional way to demonstrate how structural standard error compares to geometric sizing, we have provided an explicit Supplementary Fractional Bland-Altman test-retest plot normalized directly by the Mean structure volumes. Furthermore, we calculated volume repeatability wCVs per region and generated supplemental volumetric cross-section maps mapped onto the BrainSuite atlas. These visually present how measurement precision varies spatially, explicitly providing both data and visualization configurations alongside the aggregate numbers as discussed.}
\end{itemize}"""

# A simpler string replace avoiding escaping struggles.
old_bullet_start = r"\item \textcolor{blue}{\textbf{Supplemental Material:}"

idx_start = resp.find(old_bullet_start)
if idx_start != -1:
    resp = resp[:idx_start] + new_bullet + "\n\end{document}"

with open('response_to_reviewers.tex', 'w') as f:
    f.write(resp)
