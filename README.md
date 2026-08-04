# REFERRED DB

REFERRED DB is a Django-based laboratory data management system for referred isolate records, antimicrobial susceptibility data, final reports, WGS outputs, concordance analysis, and turnaround time monitoring.

The project follows the structure and workflow patterns of the EGASP project and is based on the Argon Dashboard Django template.

> Note: This system is still under active development. Review configuration, access controls, migrations, and deployment settings before production use.

## System Description

REFERRED DB supports the day-to-day handling of referred antimicrobial resistance laboratory data. It centralizes raw referral records, patient and isolate details, antimicrobial susceptibility results, generated laboratory reports, final reviewed records, and whole genome sequencing outputs in one web-based workflow.

The system is organized around the laboratory data lifecycle:

- Encode or upload referred isolate records.
- Validate and complete demographic, site, organism, specimen, and antibiotic result information.
- Group records into batches for review and report generation.
- Generate laboratory result PDFs for individual records or batches.
- Move reviewed records into the final database workflow.
- Upload and review WGS result files from tools such as BactScout, GTDB-Tk, GAMBIT, MLST, CheckM2, AssemblyScan, and AMRFinderPlus.
- Review emerging-resistance, classification, concordance, and turnaround time monitoring outputs.
- Maintain reference tables used by forms, dropdowns, reports, and validation logic.

The application is intended for authorized laboratory staff, reviewers, administrators, and data managers who need a controlled system for entering, checking, reviewing, exporting, and reporting referred isolate data.

## New User Instructions

Use these steps when accessing the system for the first time.

1. Ask the system administrator for your account.

   New users must have a valid username and password before using the system. Your role controls which pages and actions are available to you.

2. Open the system in a browser.

   Use the URL provided by your administrator. For local development, the default address is:

   ```text
   http://127.0.0.1:8000/
   ```

3. Log in.

   Go to `/login/`, enter your username and password, then submit the form. If you cannot log in, use the password reset option or contact the administrator.

4. Review the dashboard and menu.

   After login, use the sidebar or navigation menu to open the major work areas:

   - raw referred data
   - batches
   - final data
   - WGS projects
   - settings and reference tables
   - reports, concordance, and TAT pages

5. Enter or upload raw referred data.

   Use the raw data forms for manual entry, or use the upload tools when working from Excel files. Check required fields carefully before saving. When uploading files, use the expected templates and verify the imported records after upload.

6. Review and edit records.

   Open the raw data table to search, review, edit, or delete records as allowed by your role. Confirm site code, organism, specimen type, antibiotic results, referral date, and accession details before generating reports or copying records to final data.

7. Create and review batches.

   Use the batch pages to group records for review and reporting. Check batch contents before generating PDFs or moving records forward.

8. Generate reports.

   Use the laboratory result pages to generate individual or batch PDFs. Review generated reports for completeness before releasing or sharing them.

9. Work with final data.

   After records have been reviewed, use the final data workflow to manage finalized entries, final antibiotic results, downloads, emerging lists, concordance analysis, and WGS classification where applicable.

10. Upload WGS data when needed.

    Use the WGS project pages to upload sample information and tool outputs. Review matched records and exported summaries after upload.

11. Maintain settings only if authorized.

    Administrators and authorized users can update reference data such as site codes, organisms, antibiotics, breakpoints, specimen types, recommendations, contacts, phenotypes, TAT configuration, and non-working days. These settings affect validation, dropdowns, analysis, and reports, so changes should be reviewed carefully.

12. Log out after use.

    Use the logout option when finished, especially on shared workstations.

For help with access, missing pages, upload errors, incorrect dropdown values, or report output issues, contact the system administrator or project maintainer.

## Features

- User authentication with login, registration, logout, and password reset views.
- Raw referred isolate data entry, upload, review, editing, search, batching, and export.
- Final data review and reporting workflows.
- Antimicrobial susceptibility test result entry and export for raw and final records.
- PDF generation for individual and batch laboratory results.
- WGS upload and review workflows for sample information, BactScout, GTDB-Tk, GAMBIT, MLST, CheckM2, AssemblyScan, and AMRFinderPlus outputs.
- Field-mapping tools for uploaded Excel workbooks.
- Configurable reference data for sites, organisms, specimens, antibiotics, breakpoints, phenotypes, recommendations, contacts, and non-working days.
- Emerging-resistance and classification review screens.
- Concordance batch and accession analysis with Excel and PDF exports.
- TAT monitoring, review, analysis, owner performance, and IPCR export support.

## Tech Stack

- Python 3.12
- Django 5.0
- PostgreSQL
- Gunicorn
- WhiteNoise
- Nginx and Docker Compose for containerized deployment
- Pandas and OpenPyXL for spreadsheet import/export
- ReportLab, xhtml2pdf, and pypdf for PDF/report generation

## Project Structure

```text
REFERRED_DB/
+-- apps/
|   +-- authentication/   # Login, registration, logout, password reset
|   +-- home/             # Raw referred data, settings, batches, TAT, reports
|   +-- home_final/       # Final records, concordance, final reporting
|   +-- wgs_app/          # WGS project uploads, processing views, exports
|   +-- templates/        # Shared Django templates
|   +-- static/           # CSS, JS, images, vendor assets
|   +-- template_docs/    # Excel templates and reference upload files
+-- core/                 # Django settings, URLs, WSGI/ASGI
+-- media/                # Uploaded/generated files in local development
+-- nginx/                # Nginx config for Docker deployment
+-- manage.py
+-- requirements.txt
+-- Dockerfile
+-- docker-compose.yml
```

## Requirements

- Python 3.12 or compatible Python 3.x runtime
- PostgreSQL database
- `pip`
- Optional: Docker and Docker Compose

## Environment Variables

Create a `.env` file in the project root before running the app.

```env
SECRET_KEY=replace-with-a-secure-secret-key
DEBUG=True
SERVER=localhost

DB_NAME=referred_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

STATIC_ROOT=D:/REFERRED_DB_052325/REFERRED_DB/staticfiles
STATICFILES_DIRS=D:/REFERRED_DB_052325/REFERRED_DB/apps/static
MEDIA_ROOT=D:/REFERRED_DB_052325/REFERRED_DB/media
```

For Docker Compose, the database service exposes PostgreSQL on host port `5433` and container port `5432`. If Django runs inside Docker, set `DB_HOST=db` and `DB_PORT=5432`.

## Local Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py runserver
```

Open the app at:

```text
http://127.0.0.1:8000/
```

## Common Commands

```powershell
# Apply database migrations
python manage.py migrate

# Create migrations after model changes
python manage.py makemigrations

# Create an admin user
python manage.py createsuperuser

# Collect static assets
python manage.py collectstatic

# Run the development server
python manage.py runserver
```

## Docker Setup

Create the `.env` file first, then run:

```powershell
docker compose up --build
```

The Compose stack starts:

- `db`: PostgreSQL 13
- `web`: Django served by Gunicorn
- `nginx`: reverse proxy on port `80`

## Main Routes

- `/` - dashboard/home
- `/login/` - login
- `/register/` - registration
- `/admin/` - Django admin
- `/settings/` - reference data and configuration
- `/batch/` and `/batches/` - batch creation and review
- `/show/` - raw referred data table
- `/final/show_final_table` - final data table
- `/wgs/projects/` - WGS projects
- `/wgs/wgs/data-overview` - WGS data overview
- `/final/concordance_analysis/` - concordance analysis dashboard
- `/tat/running/`, `/tat/review/`, and `/tat/analysis/` - TAT workflows

## Data Files

Reference templates and upload workbooks are stored under:

```text
apps/template_docs/
```

Uploaded and generated files are stored under:

```text
media/
```

Treat files in `media/` as environment-specific runtime data. Avoid committing generated uploads unless they are intentionally used as fixtures or examples.

## Development Notes

- Keep model changes paired with migrations.
- Review role-based access wrappers in `apps/home/permissions.py` before adding or exposing settings-management routes.
- Large spreadsheet uploads may require careful validation because `DATA_UPLOAD_MAX_NUMBER_FIELDS` is configured for antibiotic-heavy forms.
- `TIME_ZONE` is set to `Asia/Manila`.
- Production deployments should use strong secrets, a locked-down `ALLOWED_HOSTS` list, database backups, HTTPS termination, and reviewed static/media storage paths.
