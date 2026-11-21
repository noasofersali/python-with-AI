# Hemolysis CSV analysis

This Flask app accepts a hemolysis CSV, displays the group statistics and ANOVA
results, and renders the individual measurements and group means in an
interactive three-panel Plotly chart. Right-click a measurement to exclude it;
right-click it again to restore it. Statistics and mean/error bars update
without reloading the page. Plotly.js is loaded from its CDN, so the browser
needs internet access to render the chart.

## Run

From this folder, install dependencies and start Flask:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> and upload a `.csv` file.

## Project files

- `logic.py` identifies and analyzes the CSV columns, retains the existing
  statistics, gives each measurement a stable ID, and returns chart data.
- `app.py` handles uploads, renders the page, and registers the recalculation
  blueprint.
- `interactive.py` provides `/recalculate`, which reruns the analysis while
  excluding the submitted measurement IDs.
- `templates/index.html` contains the upload form, results tables, and chart
  container.
- `static/interactive_plot.js` renders the Plotly subplots, handles right-click
  exclude/restore actions, and updates the tables and chart through `fetch`.
- `uploads/` stores uploaded CSV files.
