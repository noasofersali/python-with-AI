import re
from difflib import SequenceMatcher
from tkinter import Tk, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

ALPHA = 0.05
COLORS = ["#2166ac", "#d6604d", "#1b9e77", "#7570b3"]   # one color per group

# ===== 1. Pick the CSV and load it =====
print("Opening the file picker...")
root = Tk(); root.withdraw(); root.attributes("-topmost", True)
root.update(); root.lift(); root.focus_force()          # make sure the window appears in front
path = filedialog.askopenfilename(parent=root, title="Choose the CSV file",
                                  filetypes=[("CSV", "*.csv"), ("All files", "*.*")])
root.destroy()
if not path:
    raise SystemExit("No file selected - run again and pick the CSV.")
df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig").dropna(how="all", axis=1)
df.columns = df.columns.astype(str).str.strip()
print("Loaded:", path, "| columns:", list(df.columns))

# ===== 2. Find the columns automatically (similar names + what's inside them) =====
KEYS = {"value": ["hemolysis", "haemolysis", "hemolisis", "hemo", "המוליזה"],
        "id":    ["id", "subject", "sample", "patient", "bag", "donor", "unit", "נבדק"],
        "group": ["group", "grp", "treatment", "arm", "condition", "קבוצה"],
        "time":  ["time", "day", "days", "hour", "hrs", "week", "visit", "זמן", "יום"]}
score = lambda col, role: max(1.0 if k in col.lower() else
                              SequenceMatcher(None, col.lower(), k).ratio() for k in KEYS[role])
num = df.apply(lambda s: pd.to_numeric(s.astype(str).str.strip("% ").str.replace(",", "."), errors="coerce"))
numeric = [c for c in df if num[c].notna().mean() > 0.8]
uniq = lambda c: df[c].nunique() / len(df)

hemo_cols = [c for c in numeric if score(c, "value") > 0.75]
if len(hemo_cols) > 1:                       # WIDE file: one hemolysis column per day -> reshape
    rest = [c for c in df if c not in hemo_cols]
    ID = max(rest, key=lambda c: score(c, "id") + uniq(c))
    GROUP = max([c for c in rest if c != ID], key=lambda c: score(c, "group"))
    df = df.melt([ID, GROUP], hemo_cols, "Time", "Hemolysis %")
    TIME, VALUE = "Time", "Hemolysis %"
else:                                        # LONG file: one row per subject per day
    VALUE = max(numeric, key=lambda c: 3 * score(c, "value") + uniq(c))
    rest = [c for c in df if c != VALUE]
    ID = max(rest, key=lambda c: 2 * score(c, "id") + uniq(c) - (df[c].nunique() == len(df)))
    rest = [c for c in rest if c != ID and 2 <= df[c].nunique() <= 12]
    fixed = {c: (df.groupby(ID)[c].nunique() == 1).mean() for c in rest}  # group never changes within a subject
    GROUP = max(rest, key=lambda c: score(c, "group") + 2 * fixed[c])
    TIME = max([c for c in rest if c != GROUP], key=lambda c: score(c, "time") + 2 * (1 - fixed[c]))
print(f"Detected -> ID: '{ID}' | Group: '{GROUP}' | Time: '{TIME}' | Hemolysis: '{VALUE}'")

df[VALUE] = pd.to_numeric(df[VALUE].astype(str).str.strip("% ").str.replace(",", "."), errors="coerce")
df[GROUP] = df[GROUP].astype(str)
df = df.dropna(subset=[VALUE])
df["Day"] = df[TIME].astype(str).str.extract(r"(\d+\.?\d*)")[0].astype(float)  # "Day 2"/"T2"/2 -> 2
groups, days = sorted(df[GROUP].unique()), sorted(df["Day"].unique())

# ===== 3. One-way ANOVA (+ Tukey) at each day =====
results = []
for d in days:
    samples = [df[(df["Day"] == d) & (df[GROUP] == g)][VALUE] for g in groups]
    F, p = stats.f_oneway(*samples)
    dfb, dfw = len(groups) - 1, sum(map(len, samples)) - len(groups)
    print(f"\n=== Day {d:g} ===")
    for g, s in zip(groups, samples):
        print(f"  {g}: n={len(s)}, mean={s.mean():.3f}, SD={s.std():.3f}, Shapiro p={stats.shapiro(s).pvalue:.3f}")
    print(f"  Levene p={stats.levene(*samples).pvalue:.3f} | ANOVA F({dfb},{dfw})={F:.2f}, p={p:.4f}")
    verdict = "NOT significant - no difference between groups"
    if p < ALPHA:
        tk = stats.tukey_hsd(*samples).pvalue
        pairs = [f"{groups[i]} vs {groups[j]}" for i in range(len(groups))
                 for j in range(i + 1, len(groups)) if tk[i, j] < ALPHA]
        verdict = "SIGNIFICANT difference between groups" + (f" (Tukey: {', '.join(pairs)})" if pairs else "")
    ptxt = "p < 0.001" if p < 0.001 else f"p = {p:.3f}"
    results.append((f"Day {d:g}:  F({dfb}, {dfw}) = {F:.2f}, {ptxt}  ->  {verdict}", p < ALPHA))
    print("  DECISION ->", verdict)

# ===== 4. Panel: one plot per group =====
fig, axes = plt.subplots(1, len(groups), figsize=(5 * len(groups), 5.2), sharey=True)
for ax, g, c in zip(axes, groups, COLORS):
    sub = df[df[GROUP] == g]
    for _, ind in sub.groupby(ID):                      # individuals: thin faded lines
        ind = ind.sort_values("Day")
        ax.plot(ind["Day"], ind[VALUE], color=c, lw=1, alpha=0.35, marker="o", ms=4)
    m = sub.groupby("Day")[VALUE].agg(["mean", "sem"])  # group mean +- SEM: thick line
    ax.errorbar(m.index, m["mean"], m["sem"], color=c, lw=3, marker="o", ms=8,
                mec="white", mew=1.5, capsize=4, zorder=5)
    ax.set(xticks=days, xlim=(min(days) - 0.3, max(days) + 0.3), xlabel="Time (days)")
    ax.set_title(f"Group {g}  (n = {sub[ID].nunique()})", color=c, weight="bold")
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", alpha=0.25)
axes[0].set_ylabel("Hemolysis %")
fig.suptitle("Hemolysis % over time by group (thin = individual, thick = mean ± SEM)", weight="bold")

# ANOVA decisions under the panel
n = len(results) + 1
fig.tight_layout(rect=(0, 0.05 + 0.055 * n, 1, 1))
fig.text(0.02, 0.02 + 0.05 * (n - 1), f"One-way ANOVA between groups (alpha = {ALPHA}):", weight="bold")
for i, (line, sig) in enumerate(results):
    fig.text(0.04, 0.02 + 0.05 * (n - 2 - i), line, color="#b2182b" if sig else "#444",
             weight="bold" if sig else "normal")
fig.savefig(re.sub(r"\.csv$", "", path) + "_panel.png", dpi=300, bbox_inches="tight")
plt.show()