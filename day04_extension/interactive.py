import re
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from logic import ALPHA, analyze_csv

interactive_bp = Blueprint("interactive", __name__)
UPLOAD_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


def statistics_tables(analysis):
    return {
        "group_table": analysis["group_table"].to_html(
            index=False, classes="results-table", border=0, na_rep="—",
            float_format=lambda value: f"{value:.3f}",
        ),
        "anova_table": analysis["anova_table"].to_html(
            index=False, classes="results-table", border=0, na_rep="—",
            float_format=lambda value: f"{value:.3f}",
        ),
    }


@interactive_bp.post("/recalculate")
def recalculate():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Expected a JSON request body."), 400

    upload_id = payload.get("upload_id")
    excluded_point_ids = payload.get("excluded_point_ids")
    alpha = payload.get("alpha", ALPHA)
    if not isinstance(upload_id, str) or not UPLOAD_ID_PATTERN.fullmatch(upload_id):
        return jsonify(error="Invalid upload identifier."), 400
    if (
        not isinstance(excluded_point_ids, list)
        or any(not isinstance(point_id, str) for point_id in excluded_point_ids)
    ):
        return jsonify(error="Excluded point IDs must be a list of strings."), 400
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
        return jsonify(error="Alpha must be a number between 0 and 1."), 400

    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    matching_files = [
        path for path in upload_folder.glob(f"{upload_id}_*")
        if path.is_file() and path.suffix.lower() == ".csv"
    ]
    if len(matching_files) != 1:
        return jsonify(error="The uploaded CSV could not be found. Upload it again."), 404

    try:
        analysis = analyze_csv(
            matching_files[0],
            alpha=float(alpha),
            excluded_point_ids=excluded_point_ids,
        )
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400

    return jsonify({
        **statistics_tables(analysis),
        "plot_data": analysis["plot_data"],
    })
