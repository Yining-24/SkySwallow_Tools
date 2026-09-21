# SkySwallow Tools

A practical reporting-automation project for Excel-based trade workflows.

The project converts structured transaction worksheets into calculated profit details and consolidated management reports. It is being expanded into a local internal web application using Flask, React, and Ant Design.

## Current Features

- Calculates gross profit and gross margin for individual orders
- Validates workbook structure and reports missing or inconsistent data
- Preserves workbook formatting while writing calculated results
- Creates separate customer and overall summary worksheets
- Supports optional employee and customer-category mappings
- Produces commission estimates using configurable business rules
- Creates backups before modifying source workbooks

## Web Application Status

The Flask application shell and homepage are working locally.

Planned features include:

- React and Ant Design user interface
- Browser-based Excel upload
- Role-based access for administrators, finance staff, and other users
- Temporary file storage and automatic deletion
- Downloadable result files without overwriting the uploaded original
- Windows packaging and automatic startup

## Technology

- Python
- Flask
- openpyxl
- React and Ant Design — planned frontend
- Git and GitHub

## Project Structure

```text
SkySwallow_Tools/
├── skyswallow_tools/          # Flask application
├── tina_明细利润.py            # Detailed profit calculation
├── tina_生成总表.py            # Summary workbook generation
├── README_运行说明.md           # Detailed Chinese usage guide
└── README.md
```

## Local Development

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the current dependencies:

```bash
python -m pip install Flask openpyxl
```

Start the Flask development server:

```bash
python -m flask --app skyswallow_tools run --debug --port 5001
```

Then open:

```text
http://127.0.0.1:5001/
```

Debug mode is intended only for local development and must not be used for production deployment.

## Data and Privacy

This repository contains source code and documentation only. It does not include real customer workbooks, company credentials, or production secrets.

Uploaded business files will be processed locally by the deployed application and will not be stored in this repository.

## Detailed Usage

See [README_运行说明.md](README_运行说明.md) for the current command-line workflow and workbook format.
