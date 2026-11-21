"""
Tests for logic.py - CSV loading only.
"""
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from logic import analyze_csv

# =====================================================================
# Test is valid for up to 12 timepoints.
# =====================================================================
@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


@pytest.fixture
def data():
    """Fake data: 3 groups x 4 units x 2 days = 24 rows."""
    rows = []
    for g, base in zip("ABC", (0.20, 0.30, 0.40)):
        for unit in range(1, 5):
            for day in (0, 7):
                rows.append({"Unit ID": f"{g}{unit}", "Group": g, "Day": day,
                             "Hemolysis %": round(base + 0.01 * unit + 0.1 * (day == 7), 3)})
    return pd.DataFrame(rows)


# =====================================================================
# PART 1 - IS THE FILE FOUND AND READ?
# =====================================================================
def test_part1_file_is_found_and_read(data, tmp_path):
    path = tmp_path / "data.csv"
    data.to_csv(path, index=False)

    result = analyze_csv(path)

    assert result["group_table"]["N"].sum() == 24


def test_part1_missing_file_gives_an_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        analyze_csv(tmp_path / "does_not_exist.csv")


# =====================================================================
# PART 2 - ARE THE COLUMNS RECOGNISED?
# =====================================================================
def test_part2_columns_are_recognised(data, tmp_path):
    path = tmp_path / "data.csv"
    data.to_csv(path, index=False)

    result = analyze_csv(path)

    assert result["detected_columns"] == {
        "ID": "Unit ID",
        "Group": "Group",
        "Time": "Day",
        "Hemolysis": "Hemolysis %",
    }

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

  # =====================================================================
# PART 3 - IS THE ANOVA CALCULATED CORRECTLY?  (golden values)
# =====================================================================
def make_two_day_csv(groups, tmp_path):
    """Write a CSV from {"A": [values...], ...}. Day 1 = the values given.
    Day 2 = the same values + a small shift. (analyze_csv needs at least 2 days.)"""
    rows = []
    for group, values in groups.items():
        for i, value in enumerate(values, start=1):
            rows.append({"Unit ID": f"{group}{i}", "Group": group, "Day": 1, "Hemolysis %": value})
            rows.append({"Unit ID": f"{group}{i}", "Group": group, "Day": 2, "Hemolysis %": value + 0.05 * i})
    path = tmp_path / "golden.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_part3_anova_matches_independent_calculation(tmp_path):
    # Right answer for these numbers, worked out by hand and with statsmodels:
    #     F = 16.2126,  df = (2, 9),  p = 0.0010385
    path = make_two_day_csv({
        "A": [0.21, 0.25, 0.30, 0.27],
        "B": [0.35, 0.41, 0.38, 0.44],
        "C": [0.22, 0.28, 0.26, 0.31],
    }, tmp_path)

    anova = analyze_csv(path)["anova_table"]
    day1 = anova[anova["Day"] == 1].iloc[0]          # check day 1 only

    assert day1["F"] == pytest.approx(16.2126, rel=1e-4)
    assert day1["df between"] == 2
    assert day1["df within"] == 9
    assert day1["p"] == pytest.approx(0.0010385, rel=1e-3)
    assert day1["Decision"].startswith("SIGNIFICANT")   # p < 0.05


def test_part3_identical_groups_are_not_significant(tmp_path):
    # Two groups with exactly the same values -> no difference at all: F = 0, p = 1
    same = [0.21, 0.25, 0.30, 0.27]
    path = make_two_day_csv({"A": same, "B": same}, tmp_path)

    anova = analyze_csv(path)["anova_table"]
    day1 = anova[anova["Day"] == 1].iloc[0]

    assert day1["F"] == pytest.approx(0, abs=1e-9)
    assert day1["p"] == pytest.approx(1, abs=1e-9)
    assert day1["Decision"].startswith("NOT significant")  