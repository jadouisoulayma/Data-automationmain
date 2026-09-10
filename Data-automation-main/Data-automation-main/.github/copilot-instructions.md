# DataAutomation Project - Django Workspace

## Project Overview
Django-based data automation platform similar to Google Colab for executing Python scripts with Excel input/output.

## Features
- ✅ Login-only authentication (admin creates users)
- ✅ Create and modify Python scripts
- ✅ Execute scripts with logs and results
- ✅ Excel file input/output support
- ✅ Execution history by user
- ✅ Download last 10 result files
- ✅ FIFO storage (max 10 files per project)

## Tech Stack
- Django 6.0 (Python web framework)
- SQLite (built-in database)
- Bootstrap 5.3 (UI framework)
- openpyxl/pandas (Excel handling)
- Python 3.12

## Quick Start

### 1. Create Superuser (First Time)
```bash
./create_superuser.sh
```

### 2. Start Server
```bash
./start_server.sh
```

### 3. Access Application
- Main App: http://127.0.0.1:8000/
- Admin Panel: http://127.0.0.1:8000/admin/

## Project Structure
```
dataAutomation/
├── config/              # Django settings
├── scripts/             # Main app (models, views, urls)
├── templates/           # HTML templates with Bootstrap
├── static/              # Static files (CSS, JS)
├── media/               # User uploads (inputs/outputs)
├── venv/                # Virtual environment
├── manage.py            # Django management
├── requirements.txt     # Dependencies
└── README.md            # Full documentation
```

## Development Notes
- Database: SQLite (db.sqlite3)
- Language: French (fr-fr)
- Timezone: Africa/Tunis
- Script timeout: 5 minutes
- Executions: Unlimited (all logs kept)
- File storage: Max 5 files/script, 100 total
- Storage: Automatic file cleanup to save space

## Status
✅ **PROJECT COMPLETE AND READY TO USE**

All features implemented:
- User authentication system
- Script CRUD operations
- Script execution with file handling
- Execution history and logs
- File download system
- FIFO storage management
- Bootstrap UI
- Admin panel configuration
