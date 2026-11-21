from difflib import SequenceMatcher

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


def analyze_csv(path, alpha=ALPHA, excluded_point_ids=None):
    """Analyze a hemolysis CSV and return its tables and interactive chart data."""
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
    df["_point_id"] = [f"measurement-{index}" for index in range(len(df))]
    excluded_point_ids = set(excluded_point_ids or [])
    included_df = df[~df["_point_id"].isin(excluded_point_ids)]
    groups = sorted(df[group].unique())
    days = sorted(df["Day"].unique())
    if len(groups) < 2 or not days:
        raise ValueError("The CSV must contain at least two groups and valid time/day values.")

    group_rows = []
    anova_rows = []
    plot_decisions = []
    for day in days:
        samples = [
            included_df[(included_df["Day"] == day) & (included_df[group] == group_name)][value]
            for group_name in groups
        ]
        has_all_groups = all(len(sample) > 0 for sample in samples)
        if has_all_groups:
            f_statistic, p_value = stats.f_oneway(*samples)
            levene_p = stats.levene(*samples).pvalue
        else:
            f_statistic, p_value, levene_p = float("nan"), float("nan"), float("nan")
        df_between = len(groups) - 1
        df_within = sum(map(len, samples)) - len(groups)
        for group_name, sample in zip(groups, samples):
            group_rows.append({
                "Day": day,
                "Group": group_name,
                "N": len(sample),
                "Mean": sample.mean(),
                "SD": sample.std(),
                "Shapiro p": stats.shapiro(sample).pvalue if len(sample) >= 3 else float("nan"),
            })
        verdict = "NOT significant - no difference between groups"
        if not has_all_groups:
            verdict = "Not available - at least one group has no included measurements"
        elif p_value < alpha:
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
        plot_decisions.append(
            (f"Day {day:g}:  F({df_between}, {df_within}) = {f_statistic:.2f}, "
             f"{p_text}  ->  {verdict}", p_value < alpha)
        )

    group_plot_data = []
    individual_plot_data = []
    mean_plot_data = []
    for index, group_name in enumerate(groups):
        color = COLORS[index % len(COLORS)]
        group_df = df[df[group] == group_name]
        group_plot_data.append({
            "name": str(group_name),
            "color": color,
            "subject_count": int(group_df[subject_id].nunique()),
        })
        for individual_id, individual in group_df.groupby(subject_id, sort=False):
            individual = individual.sort_values("Day")
            individual_plot_data.append({
                "group": str(group_name),
                "color": color,
                "x": [float(day) for day in individual["Day"]],
                "y": [float(value) for value in individual[value]],
                "point_ids": individual["_point_id"].tolist(),
                "value_text": [str(float(measurement)) for measurement in individual[value]],
            })

        included_group_df = included_df[included_df[group] == group_name]
        means = included_group_df.groupby("Day")[value].agg(["mean", "sem"])
        mean_plot_data.append({
            "group": str(group_name),
            "color": color,
            "x": [float(day) for day in means.index],
            "mean": [float(measurement) for measurement in means["mean"]],
            "sem": [
                None if pd.isna(measurement) else float(measurement)
                for measurement in means["sem"]
            ],
        })

    return {
        "group_table": pd.DataFrame(group_rows),
        "anova_table": pd.DataFrame(anova_rows),
        "detected_columns": {
            "ID": subject_id, "Group": group, "Time": time, "Hemolysis": value,
        },
        "plot_data": {
            "groups": group_plot_data,
            "days": [float(day) for day in days],
            "individuals": individual_plot_data,
            "means": mean_plot_data,
            "decisions": [
                {"text": line, "significant": bool(significant)}
                for line, significant in plot_decisions
            ],
            "alpha": alpha,
            "excluded_point_ids": sorted(excluded_point_ids),
        },
    }
