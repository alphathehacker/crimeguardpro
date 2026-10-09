# CrimeGuardPro — Crime File Management System

A web application for digitising how criminal case records are filed, tracked and retrieved. Citizens can file and follow cases, officers manage FIRs and case progress, and admins oversee the system — each with their own role-based dashboard.

**Live demo:** https://crimeguardpro.onrender.com

## Features by role

- **Citizen** — register/login, file cases, track case status
- **Officer** — manage FIRs and cases assigned to them, update progress
- **Admin** — oversee users, officers and cases across the system
- **Auth** — JWT-based login with role-based access to routes/dashboards

## Tech stack

- **Backend:** Python (Flask), Flask-CORS, Gunicorn
- **Database:** MongoDB (PyMongo)
- **Auth:** JWT (PyJWT), bcrypt password hashing
- **Structure:** `models/` (case, officer/FIR, user), `routes/` (admin, auth, case, citizen, dashboard, officer)

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Create a `.env` file with the values the app expects (names only — never commit real secrets):

- `MONGO_URI` — MongoDB connection string
- `SECRET_KEY` — Flask/JWT secret

See `START_SERVER.md` for server notes and `API_TESTING_GUIDE.md` for how to test the API endpoints.

## Screenshots

_(to be added)_
