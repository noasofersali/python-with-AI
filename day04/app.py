import base64
import io
from pathlib import Path
from uuid import uuid4

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from logic import ALPHA, analyze_csv

app = Flask(__name__)
UPLOAD_FOLDER = Path(__file__).resolve().parent / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    results = None
    alpha_value = request.form.get("alpha", str(ALPHA))

    if request.method == "POST":
        uploaded_file = request.files.get("file")
        if uploaded_file is None or not uploaded_file.filename:
            error = "Please choose a CSV file to upload."
        elif Path(uploaded_file.filename).suffix.lower() != ".csv":
            error = "Only .csv files are accepted."
        else:
            try:
                alpha = float(alpha_value)
            except ValueError:
                error = "Significance level (alpha) must be a number between 0 and 1."
            if error is None:
                try:
                    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
                    filename = f"{uuid4().hex}_{secure_filename(uploaded_file.filename)}"
                    saved_path = app.config["UPLOAD_FOLDER"] / filename
                    uploaded_file.save(saved_path)
                    analysis = analyze_csv(saved_path, alpha=alpha)

                    image_buffer = io.BytesIO()
                    analysis["figure"].savefig(image_buffer, format="png", dpi=150, bbox_inches="tight")
                    plt.close(analysis["figure"])
                    plot_data = base64.b64encode(image_buffer.getvalue()).decode("ascii")
                    results = {
                        "group_table": analysis["group_table"].to_html(
                            index=False, classes="results-table", border=0, na_rep="—",
                            float_format=lambda value: f"{value:.3f}",
                        ),
                        "anova_table": analysis["anova_table"].to_html(
                            index=False, classes="results-table", border=0, na_rep="—",
                            float_format=lambda value: f"{value:.3f}",
                        ),
                        "detected_columns": analysis["detected_columns"],
                        "plot_data": plot_data,
                    }
                except ValueError as exc:
                    error = str(exc)
                except (OSError, UnicodeDecodeError) as exc:
                    error = f"Could not read or process that CSV file: {exc}"

    return render_template("index.html", error=error, results=results, alpha_value=alpha_value)


if __name__ == "__main__":
    app.run()
