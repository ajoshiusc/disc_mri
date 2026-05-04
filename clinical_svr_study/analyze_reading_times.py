import pandas as pd
from scipy import stats

df = pd.read_csv('outputs/paired_case_table.csv')

def analyze_times(df_subset, label):
    raw = df_subset['raw_time'].dropna()
    svr = df_subset['svr_time'].dropna()
    
    # Ensure they are paired by dropping rows with NaN in either
    valid_idx = df_subset[['raw_time', 'svr_time']].dropna().index
    raw = df_subset.loc[valid_idx, 'raw_time']
    svr = df_subset.loc[valid_idx, 'svr_time']
    
    print(f"--- {label} (n={len(raw)}) ---")
    print(f"Raw Time - Mean: {raw.mean():.2f}, Std: {raw.std():.2f}, Median: {raw.median():.2f}")
    print(f"SVR Time - Mean: {svr.mean():.2f}, Std: {svr.std():.2f}, Median: {svr.median():.2f}")
    
    # Paired t-test
    t_stat, p_val_t = stats.ttest_rel(raw, svr)
    print(f"Paired t-test    : t = {t_stat:.3f}, p = {p_val_t:.4f}")
    
    # Wilcoxon signed-rank test
    w_stat, p_val_w = stats.wilcoxon(raw, svr)
    print(f"Wilcoxon test    : w = {w_stat:.3f}, p = {p_val_w:.4f}")
    print("")

analyze_times(df, "All Cases")

# Let's see what the nondiagnostic columns are or which are the 4 cases.
nondx_mask = (df['svr_nondiagnostic'] == True) | (df['raw_dx'].str.lower().str.contains('limit') | df['raw_dx'].str.lower().str.contains('nondiagnostic') | df['svr_dx'].str.lower().str.contains('limit') | df['svr_dx'].str.lower().str.contains('nondiagnostic'))
# Actually the prompt says "excluding the four limited/nondiagnostic cases".
# Let's count how many are svr_nondiagnostic == True
print(f"Count of svr_nondiagnostic == True: {(df['svr_nondiagnostic'] == True).sum()}")


analyze_times(df[df['svr_nondiagnostic'] == False], "Excluding 4 Nondiagnostic Cases")
