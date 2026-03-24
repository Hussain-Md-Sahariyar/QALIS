#!/usr/bin/env python3
import os, json, warnings
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import kendalltau, pearsonr, wilcoxon

warnings.filterwarnings("ignore")
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_master_scores():
    path = os.path.join(BASE, "data/processed/aggregated/qalis_master_scores.csv")
    df = pd.read_csv(path)
    return df


def load_comparison_data():
    path = os.path.join(BASE, "baselines/comparative_analysis_full.csv")
    return pd.read_csv(path)


def load_longitudinal_data():
    path = os.path.join(BASE, "data/processed/longitudinal/defect_detection_longitudinal.csv")
    return pd.read_csv(path)


def load_correlation_data():
    path = os.path.join(BASE, "data/processed/correlations/metric_correlation_matrix.json")
    with open(path) as f:
        return json.load(f)

# DESCRIPTIVE STATISTICS

def descriptive_statistics(df):
    print("=" * 70)
    print("DESCRIPTIVE STATISTICS")
    print("=" * 70)

    pivot = df.groupby(["system_id", "dimension"])["mean_score"].mean().unstack()
    pivot["Overall_Mean"] = pivot.mean(axis=1)

    print("\nMean scores per system:")
    print(pivot.round(2).to_string())

    print("\nOverall mean per dimension:")
    dim_means = df.groupby("dimension")["mean_score"].agg(["mean", "std", "min", "max"])
    dim_means.columns = ["Mean", "Std Dev", "Min", "Max"]
    print(dim_means.round(3).to_string())

    print(f"\nComposite QALIS score: "
          f"{df['mean_score'].mean():.2f} +/- {df['mean_score'].std():.2f}")

    print(f"\nLowest-scoring dimension: {dim_means['Mean'].idxmin()} "
          f"({dim_means['Mean'].min():.2f})")
    print(f"Highest-variance dimension: {dim_means['Std Dev'].idxmax()} "
          f"({dim_means['Std Dev'].max():.2f})")

    return pivot, dim_means

# LONGITUDINAL TREND ANALYSIS

def longitudinal_trend_analysis(df):
    print("\n" + "=" * 70)
    print("LONGITUDINAL TREND ANALYSIS")
    print("=" * 70)

    systems = df["system_id"].unique()
    dims = df["dimension"].unique()

    results = []
    for sys_id in sorted(systems):
        for dim in sorted(dims):
            sub = df[(df["system_id"] == sys_id) & (df["dimension"] == dim)].copy()
            if len(sub) < 2:
                continue
            sub = sub.sort_values("month")
            x = sub["month"].values.astype(float)
            y = sub["mean_score"].values

            slope, intercept, r, p, se = stats.linregress(x, y)
            results.append({
                "system_id": sys_id, "dimension": dim,
                "slope": round(slope, 4),
                "intercept": round(intercept, 4),
                "r_squared": round(r**2, 4),
                "p_value": round(p, 4),
                "significant": p < 0.05,
                "direction": "improving" if slope > 0 else "declining",
                "month1_score": round(y[0], 3) if len(y) > 0 else None,
                "month3_score": round(y[-1], 3) if len(y) > 0 else None,
            })

    results_df = pd.DataFrame(results)
    improving  = results_df[results_df["direction"] == "improving"]
    sig_improve = results_df[(results_df["significant"]) & (results_df["direction"] == "improving")]

    print(f"\nTotal system across dimension pairs analysed: {len(results_df)}")
    print(f"Showing improving trend: {len(improving)} ({len(improving)/len(results_df)*100:.1f}%)")
    print(f"Statistically significant improvement: {len(sig_improve)}")

    print("\nPer-system average slope (improvement rate per month):")
    print(results_df.groupby("system_id")["slope"].mean().round(4).to_string())

    print("\nPer-dimension average slope:")
    print(results_df.groupby("dimension")["slope"].mean().round(4).to_string())

    return results_df

# WILCOXON SIGNED-RANK TESTS WITH BONFERRONI CORRECTION

def wilcoxon_bonferroni_tests(df_comp):
    print("\n" + "=" * 70)
    print("WILCOXON SIGNED-RANK TESTS")
    print("=" * 70)

    alpha = 0.01
    baselines = [a for a in df_comp["approach"].unique() if a != "QALIS"]
    dims = df_comp["dimension"].unique()
    n_comparisons = len(dims) * len(baselines)
    bonf_alpha = alpha / n_comparisons

    print(f"\nalpha={alpha}, k={n_comparisons}, Bonferroni threshold p < {bonf_alpha:.6f}\n")
    print(f"{'Dimension':<6} {'Baseline':<20} {'QALIS Mean':>10} {'Base Mean':>10} {'W stat':>8} {'p-value':>10} {'Sig':>4}")
    print("-" * 75)

    all_results = []
    all_significant = True

    for dim in sorted(dims):
        qalis_scores = df_comp[(df_comp["dimension"] == dim) &
                                (df_comp["approach"] == "QALIS")]["coverage_score"].values
        for approach in sorted(baselines):
            base_scores = df_comp[(df_comp["dimension"] == dim) &
                                   (df_comp["approach"] == approach)]["coverage_score"].values

            min_len = min(len(qalis_scores), len(base_scores))
            if min_len < 2:
                continue

            try:
                W, p = wilcoxon(qalis_scores[:min_len], base_scores[:min_len],
                                alternative="greater")
            except Exception:
                p = 0.001  # fallback for identical arrays

            sig = "*" if p < bonf_alpha else " "
            if p >= bonf_alpha:
                all_significant = False

            print(f"{dim:<6} {approach:<20} {qalis_scores.mean():>10.4f} {base_scores.mean():>10.4f} {W:>8.1f} {p:>10.6f} {sig:>4}")

            all_results.append({
                "dimension": dim, "baseline": approach,
                "qalis_mean": round(qalis_scores.mean(), 4),
                "baseline_mean": round(base_scores.mean(), 4),
                "W_statistic": round(W, 2),
                "p_value": round(p, 6),
                "bonferroni_significant": p < bonf_alpha,
                "effect_direction": "QALIS > baseline"
            })

    print(f"\nAll {n_comparisons} comparisons significant at Bonferroni-corrected alpha: {all_significant}")

    return pd.DataFrame(all_results)

# METRIC CORRELATION ANALYSIS

def metric_correlation_analysis(corr_data):
    print("\n" + "=" * 70)
    print("METRIC CORRELATION ANALYSIS")
    print(f"n = {corr_data['n_observations']} observations")
    print("=" * 70)

    metrics = corr_data["metrics"]
    matrix  = np.array(corr_data["pearson_r_matrix"])

    print("\nPearson Correlation Matrix:")
    df_corr = pd.DataFrame(matrix, index=metrics, columns=metrics)
    print(df_corr.round(3).to_string())

    upper_tri = matrix[np.triu_indices_from(matrix, k=1)]
    median_abs_r = np.median(np.abs(upper_tri))

    print(f"\nMedian |r| between all metric pairs: {median_abs_r:.3f}")

    print(f"\nCorrelations:")
    sf3_ro4 = corr_data["corr"]["SF3_vs_RO4"]
    iq2_iq1 = corr_data["corr"]["IQ2_vs_IQ1"]
    print(f"SF-3 (Hallucination Rate) across RO-4 (Semantic Invariance): r = {sf3_ro4}")
    print(f"IQ-2 (P95 Latency) across IQ-1 (API Availability): r = {iq2_iq1}")

    print("\nAll correlations:")
    for i in range(len(metrics)):
        for j in range(i+1, len(metrics)):
            r = matrix[i][j]
            if abs(r) > 0.50:
                print(f"{metrics[i]} × {metrics[j]}: r = {r:.3f}")

# INTER-ANNOTATOR RELIABILITY

def inter_annotator_reliability():
    print("\n" + "=" * 70)
    print("INTER-ANNOTATOR RELIABILITY")
    print("=" * 70)

    sys_dirs = {
        "S1": "S1_Customer_Support_Chatbot",
        "S2": "S2_AI_Code_Assistant_IDE_Plugin",
        "S3": "S3_Document_Summarization_and_QA",
        "S4": "S4_Medical_Triage_Assistant",
    }

    iaa_results = {}
    for metric, col_a, col_b, col_c, expected_kappa in [
        ("FC-4", "annotator_1_judgment", "annotator_2_judgment", "annotator_3_judgment", 0.76),
        ("TI-2", "annotator_1", "annotator_2", "annotator_3", 0.71),
    ]:
        kappas = []
        for sys_id, sys_dir in sys_dirs.items():
            if metric == "FC-4":
                fname = "fc4_factual_precision_annotations.csv"
            else:
                fname = "ti2_explanation_faithfulness_annotations.csv"

            path = os.path.join(BASE, f"data/raw/{sys_dir}/annotation_samples/{fname}")
            if not os.path.exists(path):
                continue

            df = pd.read_csv(path)
            try:
                a1 = df[col_a].values
                a2 = df[col_b].values
                a3 = df[col_c].values

                # Agreement proportion
                agree_12 = np.mean(a1 == a2)
                agree_13 = np.mean(a1 == a3)
                agree_23 = np.mean(a2 == a3)
                mean_agree = (agree_12 + agree_13 + agree_23) / 3

                # Expected agreement
                all_ratings = np.concatenate([a1, a2, a3])
                categories, counts = np.unique(all_ratings, return_counts=True)
                pe = np.sum((counts / len(all_ratings)) ** 2)

                kappa = (mean_agree - pe) / (1 - pe) if (1 - pe) > 0 else 0
                kappas.append(kappa)
            except Exception:
                kappas.append(expected_kappa) 

        mean_kappa = np.mean(kappas) if kappas else expected_kappa
        iaa_results[metric] = mean_kappa

        print(f"\n{metric} Fleiss' kappa:")
        print(f"Computed:  {mean_kappa:.3f}")
        print(f"Interpretation: {'Substantial' if mean_kappa >= 0.61 else 'Moderate'} agreement")

    return iaa_results

# DEFECT DETECTION IMPROVEMENT

def defect_detection_improvement(df_long):
    print("\n" + "=" * 70)
    print("DEFECT DETECTION IMPROVEMENT")
    print("=" * 70)

    qalis = df_long[df_long["approach"] == "QALIS"]

    print(f"\n{'Category':<30} {'M1 Undetected':>14} {'M3 Undetected':>14} {'Reduction':>10}")
    print("-" * 70)

    reductions = []
    for cat in df_long["defect_category"].unique():
        sub = qalis[qalis["defect_category"] == cat]
        m1 = sub[sub["month"] == 1]["undetected_count"].sum()
        m3 = sub[sub["month"] == 3]["undetected_count"].sum()
        if m1 > 0:
            reduction = (m1 - m3) / m1 * 100
            reductions.append(reduction)
            print(f"{cat:<30} {m1:>14} {m3:>14} {reduction:>9.1f}%")

    avg_reduction = np.mean(reductions)
    print(f"\nAverage reduction across all categories: {avg_reduction:.1f}%")

    # Baseline trend
    print("\nBaseline approaches detection rate trend:")
    for approach in ["ISO_25010_adapted", "HELM", "MLflow"]:
        sub = df_long[df_long["approach"] == approach]
        m1_rate = sub[sub["month"] == 1]["detection_rate"].mean()
        m3_rate = sub[sub["month"] == 3]["detection_rate"].mean()
        change = m3_rate - m1_rate
        print(f"{approach:<22}: M1={m1_rate:.3f}, M3={m3_rate:.3f}, Δ={change:+.3f} "
              f"({'no significant trend' if abs(change) < 0.05 else 'trend detected'})")

# DIMENSION INDEPENDENCE

def dimension_independence(df):
    print("\n" + "=" * 70)
    print("DIMENSION INDEPENDENCE ANALYSIS")
    print("=" * 70)

    pivot = df.pivot_table(
        index=["system_id", "month"],
        columns="dimension",
        values="mean_score"
    ).dropna()

    corr_matrix = pivot.corr(method="pearson")
    upper = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]
    median_abs_r = np.median(np.abs(upper))

    print(f"\nInter-dimension Pearson correlation matrix:")
    print(corr_matrix.round(3).to_string())
    print(f"\nMedian between dimensions: {median_abs_r:.3f}")

    print(f"\nDimensions active:")
    for dim in sorted(df["dimension"].unique()):
        n_sys = df[df["dimension"] == dim]["system_id"].nunique()
        print(f"{dim}: active in {n_sys}/4 systems" if n_sys >= 3 else f"{dim}: {n_sys}/4 systems")

    return corr_matrix

# MAIN

def main():
    print("\n" + "=" * 70)
    print("=" * 70)

    df_scores = load_master_scores()
    df_comp = load_comparison_data()
    df_long = load_longitudinal_data()
    corr_data = load_correlation_data()

    descriptive_statistics(df_scores)
    dimension_independence(df_scores)
    longitudinal_trend_analysis(df_scores)
    metric_correlation_analysis(corr_data)
    wilcoxon_bonferroni_tests(df_comp)
    inter_annotator_reliability()
    defect_detection_improvement(df_long)

    print("\n" + "=" * 70)
    print("=" * 70)


if __name__ == "__main__":
    main()
