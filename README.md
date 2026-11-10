# EcoMeter

EcoMeter is my personal carbon-footprint tracker. I built it with a React and Vite frontend and a FastAPI backend. It runs locally and does not require an account.

## What it does

- Records activities for electricity, transportation, food, shopping, and waste.
- Shows totals and trends in kg CO₂e on the dashboard and analytics pages.
- Tracks monthly footprint goals and provides recommendations based on recorded activities.
- Stores the emission factors, their sources, and the assumptions used in the calculations. See [EMISSION_FACTORS.md](./EMISSION_FACTORS.md).

## Tools used

- **Frontend:** React, Vite, React Router, Axios, and Recharts
- **Backend:** Python, FastAPI, SQLAlchemy, Pydantic, and PyMySQL
- **Database:** SQLite by default, with optional MySQL support

## Run it locally

Use two PowerShell windows from the project folder.

### 1. Start the backend

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000`. You can check that it is running at `http://127.0.0.1:8000/health`. By default, the backend creates and uses `backend\ecometer.db`.

### 2. Start the frontend

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the local address printed by Vite, usually `http://localhost:5173`.

## Use MySQL instead of SQLite

SQLite is enough for a local setup. To use MySQL, install MySQL Server 8.x, start the service, and create a database and application user. On the Windows machine where I developed EcoMeter, the service is named `MySQL80`, and the MySQL command-line client is installed at the path shown below.

Start the service from an Administrator PowerShell:

```powershell
Start-Service -Name MySQL80
```

Open the MySQL command-line client:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

At the `mysql>` prompt, create the database and a separate application user. Replace the example password with a password of your own:

```sql
CREATE DATABASE ecometer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ecometer_app'@'127.0.0.1' IDENTIFIED BY 'replace-with-your-password';
GRANT ALL PRIVILEGES ON ecometer.* TO 'ecometer_app'@'127.0.0.1';
```

From the project folder, copy the example settings file:

```powershell
Copy-Item backend\.env.example backend\.env
```

Set `DATABASE_URL` in `backend\.env`, using the same password you set in MySQL:

```env
DATABASE_URL=mysql+pymysql://ecometer_app:replace-with-your-password@127.0.0.1:3306/ecometer?charset=utf8mb4
CORS_ORIGINS=http://localhost:5173
```

If your password contains characters that have a special meaning in a URL, percent-encode them in `DATABASE_URL`. Keep `backend\.env` on your machine and do not commit it. The backend uses the configured database when it starts.

## Add demo activities

The seeder adds 232 varied, synthetic activities across roughly one year, ending the day before it is run. The sample includes electricity readings, meals, waste, occasional shopping, and 168 varied commutes (about 14 a month). These are generated examples, not real measurements.

With the backend dependencies installed, run this from the project folder:

```powershell
Set-Location backend
.\.venv\Scripts\python seed_demo_data.py
```

The script prints the date range it added. It writes to the database selected by `DATABASE_URL`, or to the default SQLite database if no MySQL URL is configured. Check `backend\.env` before running it so the samples go into the database you intend to use.

Demo rows are marked with `Demo data:` and can be removed from the Activity log. When the seeder runs again, it leaves a current demo set alone or replaces an older marked set. It does not replace ordinary personal activity rows.

## Existing databases

If you are using a database from an older account-enabled version, the backend migration removes the obsolete account columns while preserving activities and goals. It only removes legacy emissions-basis columns when the saved records are already CO₂e; if it finds older results in another basis, startup stops with an error instead of relabeling them.
