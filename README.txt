# CSR Volunteer Management System (Flask, BCE, SQLite)

This app implements the CSR Volunteer Management System using **Flask** with a strict **B-C-E (Boundary–Control–Entity)** structure and **SQLite**.

## Where is the SQLite file?
The database file is created **on first run** in the working folder as **`csr_vms.db`** (configured in `app/__init__.py` as `sqlite:///csr_vms.db`).  
You will see it appear after you start the server and load any page (e.g., the login page). If you run the app from a different folder, the DB will be created **in that folder**.

## Quick Start

```bash
# create a virtualenv
py -3.13 -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# install deps
pip install -r requirements.txt

# run
python app.py
# open http://127.0.0.1:5000/
```

### Demo Logins
- User Admin — `user_admin1 / user_admin1!`
- CSR Representative — `csr_user1 / csr_user1!`
- Person in Need — `pin_user1 / pin_user1!`
- Platform Manager — `pm_user1 / pm_user1!`

On first run the app **auto-seeds**:
- 4 fixed demo accounts (one per role)
- 100 test user profiles
- Sample categories & ~40 seeded PIN requests

## Project Structure (B-C-E)

```
app/
  boundary/              # BOUNDARY — Flask routes (HTTP/UI)
    routes.py
  control/               # CONTROL  — Use-case logic
    auth_controller.py
    user_admin_controller.py
    csr_controller.py
    pin_controller.py
    pm_controller.py
    report_controller.py
  entity/                # ENTITY   — Data models & persistence
    models.py
  templates/             # BOUNDARY — Jinja2 templates (UI)
  static/css/            # BOUNDARY — Styles (your palette & layout)
app.py                   # BOUNDARY — WSGI entry point
requirements.txt
README.md / README.txt
```

## How the App Works (per role)

### User Admin
- Login/Logout.
- **Search/List/Create/Update/Suspend** users.
- **Create/Update/Search** user profiles.
- UI: `Admin → Users & Profiles` table with inline update forms and search bar.

### CSR Representative
- Login/Logout.
- View PIN requests (auto-increments **views**), **filter by category**.
- Save requests to **Shortlist**.
- View **History** of completed services with **category + date range** filters.

### Person-In-Need (PIN)
- Login/Logout.
- **Create/View/Update/Delete/Search** own requests.
- See **views** and **shortlist** counters.
- View **Completed Matches** history with filters.

### Platform Manager
- Login/Logout.
- **Create/View/Update/Delete/Search** service **categories**.
- **Reports:** Daily / Weekly / Monthly aggregates for requests & completed services.

## Styling / UI
- Font: Canva Sans fallback (`font-family: 'Canva Sans', Arial, sans-serif`).
- Colors: `--red:#ff2828; --yellow:#ffa51f; --dark-blue:#004aad; --light-blue:#c2e9ff; --green:#00bf63`.
- Layout mirrors your Login and User Admin design language (top bar, left menu, light-blue content area, bold headers, rounded cards).

## Notes
- DB URI: `sqlite:///csr_vms.db` (relative to **current working directory**).
- If you want the DB inside a specific folder, run the app from that folder, or change the URI to an absolute path.
- The code is annotated with **BOUNDARY/CONTROL/ENTITY** comments to meet BCE requirements.



GITHUB repo:

Below are the codes to update the entire project folder in the repo.

cd "C:\Users\dhano\OneDrive\Desktop\csit314\csr_vms_flask_bce"
git init
git add -A
git commit -m "feat: Flask BCE app (login UI + modules)"

git branch -M main
git remote add origin https://github.com/dhanoosh2410/CSIT314-MindForge-_csr-vms.git
git push -u origin main --force


Below are the code to update the repo's files according to the changes made in the local project folder

# 1) Go to your project folder
cd "C:\Users\dhano\OneDrive\Desktop\csit314\csr_vms_flask_bce"

# 2) (One-time) set your identity
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# 3) Make sure the remote is set to your repo
git remote -v
# If you don't see origin, add it:
git remote add origin https://github.com/dhanoosh2410/CSIT314-MindForge-_csr-vms.git

# 4) See changes
git status

# 5) Stage & commit
git add -A
git commit -m "Update: login UI + merged module templates + CSS"

# 6) Pull latest (rebase keeps history clean)
git pull --rebase origin main   # use 'master' if your default branch is master

# 7) Push
git push origin main

Below are code to pull the updates from github:

git remote -v
You should see something like:
origin  https://github.com/dhanoosh2410/CSIT314-MindForge-_csr-vms.git (fetch)
origin  https://github.com/dhanoosh2410/CSIT314-MindForge-_csr-vms.git (push)

git fetch origin

git checkout main
git pull origin main

git status
