# Hemolysis CSV web app

Install the dependencies and start the app from this folder:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open the local address printed by Flask, then upload a `.csv` file. Uploads are
saved in `uploads/`. The page displays per-group statistics, one-way ANOVA
results, and a hemolysis plot. The significance level defaults to `0.05`.
