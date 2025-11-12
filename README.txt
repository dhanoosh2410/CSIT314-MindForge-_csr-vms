CSR Volunteer Management System 

Description abouth the web app: Volunteer platform built with Flask following Boundary–Control–Entity (BCE) framework and onbject oriented. Supports four roles: User Admin, CSR Representative, Person-In-Need (PIN), and Platform Manager.

Tech Stack:
-DB: SQLite (csr_vms.db)
-Frontend: HTML/CSS 
-Backend: Python 3.13, Flask, Jinja2, SQLAlchemy (SQLite)

## Where is the SQLite file?
The database file is created **on first run** in the working folder as **`csr_vms.db`** (configured in `app/__init__.py` as `sqlite:///csr_vms.db`).  
You will see it appear after you start the server and load any page (e.g., the login page). If you run the app from a different folder, the DB will be created **in that folder**.

HOW TO RUN THE APP:  

Open two terminals on Visual Studio Code

Terminal 1:
```
# (1) create a virtualenv
py -3.13 -m venv .venv

# (2) Activate virtualenv 
.\.venv\Scripts\Activate.ps1

# (3) install deps
pip install -r requirements.txt

# (4) run
python app.py

# open http://127.0.0.1:5000/ 
```

Terminal 2:
```
# (1) create a virtualenv
py -3.13 -m venv .venv

# (2) Activate virtualenv 
.\.venv\Scripts\Activate.ps1

# (3) Seed test data
python tools/seed_test_data.py

# This will add 100 data to the database
```

To gain access to each roles, use the following demo accounts:

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
CSR_VMS_FLASK_BCE/
├─ app.py                      # App factory + blueprint registration  (Boundary wiring)
│
├─ boundary/
│  └─ routes.py                # Boundary: HTTP routes, session/role checks, navigation
│
├─ control/
│  ├─ auth_controller.py       # Control: Login/Logout orchestration
│  ├─ csr_controller.py        # Control: CSR use cases
│  ├─ pin_controller.py        # Control: PIN use cases
│  ├─ pm_controller.py         # Control: Platform Manager use cases
│  └─ user_admin_controller.py # Control: User Admin use cases
│
├─ entity/
│  └─ models.py                # Entity: SQLAlchemy models + domain behavior
│
├─ templates/                  # Boundary: Jinja pages
│  ├─ base.html
│  ├─ login.html
│  ├─ user_admin.html
│  ├─ csr_rep.html
│  ├─ pin.html
│  └─ pm.html
│
├─ static/
│  └─ css/style.css            # Boundary: global styling
│
├─ tools/seed_test_data.py     # One-time seed script
└─ README.txt

```