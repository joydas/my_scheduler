from flask import Flask, render_template, request, jsonify
import os
from utils.excel_parser import read_excel_data
from utils.date_utils import format_scheduler_output
from scheduler import Scheduler

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

resources = []
work_items = []
scheduled_result = []


@app.route("/")
def index():
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    global resources, work_items
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(filepath)

    try:
        resources, work_items = read_excel_data(filepath)
        display_resources = format_scheduler_output(resources)
        display_work_items = format_scheduler_output(work_items)
        return render_template("initial.html", resources=display_resources, work_items=display_work_items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/run-scheduler", methods=["POST"])
def run_scheduler():
    global resources, work_items, scheduled_result
    scheduler = Scheduler(resources, work_items)
    scheduled_result = scheduler.schedule_work_items()
    display_result = format_scheduler_output(scheduled_result)
    return render_template("result.html", result=display_result)


if __name__ == "__main__":
    app.run(debug=True)
