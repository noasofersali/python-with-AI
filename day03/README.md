# Hemolysis Analysis

## What the code does
- Lets you pick a CSV file and finds the ID, group, time and Hemolysis % columns automatically, even if their names are only similar.
- At each time point (days 0, 1, 2), compares the 3 groups with a **one-way ANOVA**, followed by a Tukey post-hoc test when the result is significant.
- Draws a panel with one plot per group: each individual is a thin line and the group mean ± SEM is a thick line, with one color per group.
- Writes the ANOVA decision (significant / not significant) for each day under the panel and saves the figure as a PNG.

**Run:** `pip install pandas scipy matplotlib`, then `python hemolysis_analysis.py`

## How I built it 
1. Described the task: analyse Hemolysis % in 3 groups at 3 time points, run a one-way ANOVA at each time point, and plot each individual's values over time for each group.
2. CSV headers- Asked for the code to recognise the columns automatically, even when their names are only similar.
3. Describe how the panel should look like- the three group plots to be combined into one panel for comparison.
4. Asked about existing libraries that could replace writing everything from scratch.
