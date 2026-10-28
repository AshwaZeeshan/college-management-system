# College Management System

A desktop application built with Python, Tkinter and SQLite for a university Database Systems project by Shifa Zeeshan and Mahnoor Khan.

## Features

- Separate accounts and interfaces for administrators, students, professors and lab attendants.
- Manage student, professor, lab attendant and course records.
- Track course enrollments, teaching assignments and lab duties.
- Edit profiles, upload profile photos and change passwords.
- Enable or disable user accounts from the admin interface.
- Export student, professor, course, enrollment, lab and summary reports as PDF, Excel or CSV files.
- Use relational tables, foreign keys, constraints, indexes, views and triggers in SQLite.

## Requirements

- Python 3.10 or later, with Tkinter. On Windows, select Tcl/Tk support when installing Python.
- Packages listed in `requirements.txt`.

## Run locally

Open a terminal in the project folder:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

On macOS or Linux, use `.venv/bin/python` in place of `.venv\Scripts\python.exe`. Tkinter may require a separate system package on Linux.

The first launch creates `college.db` beside the source files and populates demonstration records. Report exports are saved in `reports/`. Both are excluded from version control.

### Demo sign-in

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@college.edu` | `Admin@1234` |
| Student | `student101@college.edu` | `Sample@1234` |
| Professor | `prof201@college.edu` | `Sample@1234` |
| Lab attendant | `lab301@college.edu` | `Sample@1234` |

These are built-in credentials for the local educational demo.

## Project files

| File | Purpose |
| --- | --- |
| `app.py` | Application entry point and main interface |
| `db.py` | Database schema, migrations and sample data |
| `auth.py` | Login, registration and input validation |
| `login_window.py` | Login and registration interface |
| `admin_dashboard.py` | Administrator dashboard |
| `profile_window.py` | Profile management interface |
| `reports.py` | PDF, Excel and CSV generation |
| `tests/test_database.py` | Fresh database, migration, authentication and export checks |

## Run checks

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Checks use temporary databases and do not modify your application database.

## Authors

- Shifa Zeeshan
- Mahnoor Khan 
