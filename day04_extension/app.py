from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from interactive import interactive_bp, statistics_tables
from logic import ALPHA, analyze_csv

app = Flask(__name__)
UPLOAD_FOLDER = Path(__file__).resolve().parent / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.register_blueprint(interactive_bp)


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
                    upload_id = uuid4().hex
                    filename = f"{upload_id}_{secure_filename(uploaded_file.filename)}"
                    saved_path = app.config["UPLOAD_FOLDER"] / filename
                    uploaded_file.save(saved_path)
                    analysis = analyze_csv(saved_path, alpha=alpha)

                    results = {
                        **statistics_tables(analysis),
                        "detected_columns": analysis["detected_columns"],
                        "plot_data": analysis["plot_data"],
                        "upload_id": upload_id,
                    }
                except ValueError as exc:
                    error = str(exc)
                except (OSError, UnicodeDecodeError) as exc:
                    error = f"Could not read or process that CSV file: {exc}"

    return render_template("index.html", error=error, results=results, alpha_value=alpha_value)


if __name__ == "__main__":
    app.run()
