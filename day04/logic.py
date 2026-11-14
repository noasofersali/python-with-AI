import re
from difflib import SequenceMatcher

import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

ALPHA = 0.05
COLORS = ["#2166ac", "#d6604d", "#1b9e77", "#7570b3"]
KEYS = {
    "value": ["hemolysis", "haemolysis", "hemolisis", "hemo", "המוליזה"],
    "id": ["id", "subject", "sample", "patient", "bag", "donor", "unit", "נבדק"],
    "group": ["group", "grp", "treatment", "arm", "condition", "קבוצה"],
    "time": ["time", "day", "days", "hour", "hrs", "week", "visit", "זמן", "יום"],
}


def analyze_csv(path, alpha=ALPHA):
    """Analyze a hemolysis CSV and return its tables and Matplotlib figure."""
    if not 0 < alpha < 1:
        raise ValueError("Alpha must be greater than 0 and less than 1.")

    df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
    df = df.dropna(how="all", axis=1)
    df.columns = df.columns.astype(str).str.strip()
    if df.empty or len(df.columns) < 3:
        raise ValueError("The CSV must contain data and columns for ID, group, time, and hemolysis.")

    def score(column, role):
        return max(
            1.0 if key in column.lower() else
            SequenceMatcher(None, column.lower(), key).ratio()
            for key in KEYS[role]
        )

    numeric = df.apply(
        lambda series: pd.to_numeric(
            series.astype(str).str.strip("% ").str.replace(",", "."), errors="coerce"
        )
    )
    numeric_columns = [column for column in df if numeric[column].notna().mean() > 0.8]
    hemolysis_columns = [column for column in numeric_columns if score(column, "value") > 0.75]

    try:
        if len(hemolysis_columns) > 1:
            remaining = [column for column in df if column not in hemolysis_columns]
            subject_id = max(remaining, key=lambda column: score(column, "id") + df[column].nunique() / len(df))
            group_candidates = [column for column in remaining if column != subject_id]
            group = max(group_candidates, key=lambda column: score(column, "group"))
            df = df.melt([subject_id, group], hemolysis_columns, "Time", "Hemolysis %")
            time, value = "Time", "Hemolysis %"
        else:
            value = max(numeric_columns, key=lambda column: 3 * score(column, "value") + df[column].nunique() / len(df))
            remaining = [column for column in df if column != value]
            subject_id = max(
                remaining,
                key=lambda column: 2 * score(column, "id") + df[column].nunique() / len(df)
                - (df[column].nunique() == len(df)),
            )
            remaining = [
                column for column in remaining
                if column != subject_id and 2 <= df[column].nunique() <= 12
            ]
            fixed = {
                column: (df.groupby(subject_id)[column].nunique() == 1).mean()
                for column in remaining
            }
            group = max(remaining, key=lambda column: score(column, "group") + 2 * fixed[column])
            time = max(
                [column for column in remaining if column != group],
                key=lambda column: score(column, "time") + 2 * (1 - fixed[column]),
            )
    except ValueError as exc:
        raise ValueError(
            "Could not identify ID, group, time, and hemolysis columns. "
            "Check that the CSV contains the expected data."
        ) from exc

    df[value] = pd.to_numeric(df[value].astype(str).str.strip("% ").str.replace(",", "."), errors="coerce")
    df[group] = df[group].astype(str)
    df = df.dropna(subset=[value])
    df["Day"] = df[time].astype(str).str.extract(r"(\d+\.?\d*)")[0].astype(float)
    df = df.dropna(subset=["Day"])
    groups = sorted(df[group].unique())
    days = sorted(df["Day"].unique())
    if len(groups) < 2 or not days:
        raise ValueError("The CSV must contain at least two groups and valid time/day values.")

    group_rows = []
    anova_rows = []
    decisions = []
    for day in days:
        samples = [df[(df["Day"] == day) & (df[group] == group_name)][value] for group_name in groups]
        f_statistic, p_value = stats.f_oneway(*samples)
        df_between = len(groups) - 1
        df_within = sum(map(len, samples)) - len(groups)
        for group_name, sample in zip(groups, samples):
            group_rows.append({
                "Day": day,
                "Group": group_name,
                "N": len(sample),
                "Mean": sample.mean(),
                "SD": sample.std(),
                "Shapiro p": stats.shapiro(sample).pvalue,
            })
        levene_p = stats.levene(*samples).pvalue
        verdict = "NOT significant - no difference between groups"
        if p_value < alpha:
            tukey_p = stats.tukey_hsd(*samples).pvalue
            pairs = [
                f"{groups[i]} vs {groups[j]}"
                for i in range(len(groups))
                for j in range(i + 1, len(groups))
                if tukey_p[i, j] < alpha
            ]
            verdict = "SIGNIFICANT difference between groups"
            if pairs:
                verdict += f" (Tukey: {', '.join(pairs)})"
        anova_rows.append({
            "Day": day,
            "F": f_statistic,
            "df between": df_between,
            "df within": df_within,
            "p": p_value,
            "Levene p": levene_p,
            "Decision": verdict,
        })
        p_text = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"
        decisions.append(
            (f"Day {day:g}:  F({df_between}, {df_within}) = {f_statistic:.2f}, "
             f"{p_text}  ->  {verdict}", p_value < alpha)
        )

    figure, axes = plt.subplots(1, len(groups), figsize=(5 * len(groups), 5.2), sharey=True, squeeze=False)
    axes = axes[0]
    for index, (axis, group_name) in enumerate(zip(axes, groups)):
        color = COLORS[index % len(COLORS)]
        subset = df[df[group] == group_name]
        for _, individual in subset.groupby(subject_id):
            individual = individual.sort_values("Day")
            axis.plot(individual["Day"], individual[value], color=color, lw=1, alpha=0.35, marker="o", ms=4)
        means = subset.groupby("Day")[value].agg(["mean", "sem"])
        axis.errorbar(
            means.index, means["mean"], means["sem"], color=color, lw=3, marker="o", ms=8,
            mec="white", mew=1.5, capsize=4, zorder=5,
        )
        axis.set(xticks=days, xlim=(min(days) - 0.3, max(days) + 0.3), xlabel="Time (days)")
        axis.set_title(f"Group {group_name}  (n = {subset[subject_id].nunique()})", color=color, weight="bold")
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.25)
    axes[0].set_ylabel("Hemolysis %")
    figure.suptitle("Hemolysis % over time by group (thin = individual, thick = mean ± SEM)", weight="bold")

    number_of_lines = len(decisions) + 1
    figure.tight_layout(rect=(0, 0.05 + 0.055 * number_of_lines, 1, 1))
    figure.text(0.02, 0.02 + 0.05 * (number_of_lines - 1), f"One-way ANOVA between groups (alpha = {alpha}):", weight="bold")
    for index, (line, significant) in enumerate(decisions):
        figure.text(
            0.04, 0.02 + 0.05 * (number_of_lines - 2 - index), line,
            color="#b2182b" if significant else "#444",
            weight="bold" if significant else "normal",
        )

    return {
        "group_table": pd.DataFrame(group_rows),
        "anova_table": pd.DataFrame(anova_rows),
        "detected_columns": {
            "ID": subject_id, "Group": group, "Time": time, "Hemolysis": value,
        },
        "figure": figure,
    }
