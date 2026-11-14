# Day 04 – Blood Hemolysis Results: Flask Web Application

## Overview

This project turns my previous assignment (day03), a Python program that analyzes **blood hemolysis results**, into a **web application** built with [Flask](https://flask.palletsprojects.com/).

Instead of running the analysis from the command line, the user can now open a web page, **upload a CSV file** with hemolysis results, and see the analysis results directly in the browser.

## What the website does

1. Shows a web page with an upload form.
2. Lets the user upload a **CSV file** with blood hemolysis data (only `.csv` files are accepted).
3. Saves the uploaded file to the `uploads/` folder.
4. Runs the original analysis code from day03 (`logic.py`) on the uploaded data.
5. Shows the results on the page: tables as HTML tables and plots as images.
6. Shows a clear error message if no file was selected or the file isn't a CSV.

## Project structure

| File / folder | What it is |
|---|---|
| `logic.py` | The **business logic**: my original code from the **day03** assignment, which does the hemolysis data analysis. Any `input()`/`print()` calls were separated out, so the calculations are clean functions that take arguments and return results. What the code does was not changed. |
| `app.py` | The **Flask web app** (the web interface). It receives the uploaded CSV, calls the functions from `logic.py`, and sends the results to the web page. |
| `templates/` | Holds the **HTML templates**. Flask fills them with the results each time a file is uploaded. |
| `templates/index.html` | The main page: the upload form and the results area. |
| `uploads/` | The folder where uploaded CSV files are saved. `app.py` creates it automatically if it doesn't exist. |
| `requirements.txt` | The list of Python packages the project needs (e.g. Flask, pandas, matplotlib). |
| `README.md` | This file. |

## How to run

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
2. Start the app:
   ```
   python app.py
   ```
3. Open a browser and go to: <http://127.0.0.1:5000>
4. Upload a CSV file with hemolysis results and view the analysis.

> Note: the app runs **locally** on my computer (`127.0.0.1` means "this computer"). It works only while `app.py` is running in the terminal.

## What I learned in this assignment

- **Business logic vs. interface:** the *business logic* is the part of the program that does the real work (the hemolysis calculations). The *interface* is how the user interacts with it (before: the command line; now: a web page). Keeping them separate means the same logic can be reused with a different interface without rewriting it.
- **Flask basics:** how a Flask app works as a small web server, how a *route* (`@app.route("/")`) connects a web address to a Python function, and how `GET` (opening the page) and `POST` (submitting the form) requests differ.
- **Templates:** an HTML template is a page with placeholders (`{{ result }}`) and conditions (`{% if result %}`). Flask fills in a fresh copy of the page with new results on each upload, while the template file itself stays the same.
- **`requirements.txt`:** a standard file listing the packages a project needs, so anyone can install everything with one command.
- **Static website vs. web application:** a static site (like my GitHub Pages site from the first assignment) is just HTML files. A Flask app is a Python program that has to be *running* to work. To share it with a public link, it would need to be deployed to a server (e.g. Render or PythonAnywhere).


## Prompt used to create the web app

The Flask app was created with GitHub Copilot (Agent mode) in VS Code, using this prompt:

> #logic.py contains my previous assignment's code (the business logic).
> Create a new file **app.py** in the same folder that is a Flask web app. It should **import and use the functions from logic.py**.
> The web page should let me **upload CSV files** through a form, save them to an `uploads/` folder, run the business logic on them, and **display the results on the page** (tables as HTML tables, and any plots as images). Only accept `.csv` files, and show a clear error message if the file is missing or wrong. If the logic also needs other parameters, add form fields for them.
> If logic.py has `input()` or `print()` mixed into the calculations, separate them into clean functions that take arguments and return results, without changing what the code does.
> Put the HTML in a `templates/` folder, and create a `requirements.txt` (including pandas/matplotlib if logic.py uses them).
> Then tell me how to run it, and briefly explain what each part of app.py does.

A follow-up prompt was used so the app creates the `uploads/` folder automatically:

> Make app.py create the uploads folder automatically when the app starts, if it doesn't already exist.
