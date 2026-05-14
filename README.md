# UWA Campus Swap-Meet

A Flask-based **student marketplace for UWA** where students can buy and sell
textbooks, electronics, furniture, and other campus essentials, with safe
on-campus meetup spots powered by an interactive map of UWA buildings.

This is a CITS5505 Agile Web Development group project (Semester 1, 2026).

## What it does

- **Sellers** list items with photos, prices, categories, and a meetup spot
  selected on an interactive map of the UWA campus.
- **Buyers** browse a gallery of active listings, search and filter by keyword,
  category, or price range, and message sellers directly through an in-app inbox
  with real-time WebSocket updates.
- **Sellers** mark items as sold once a deal is closed; sold items stay visible
  with a "Sold" badge so other users can see what's already been bought.
- **Admins** moderate the platform: feature top listings, delete inappropriate
  ones, and ban users who violate the platform rules.

The application uses a **session-based pending-registration flow with OTP email
verification** to keep unverified accounts out of the database, and includes
per-account login lockout, per-sender message rate limits, and magic-byte image
upload validation against content-type spoofing.

## Team members

| UWA ID | Name | GitHub username |
|--------|------|-----------------|
| 24267814 | Yuxing Zhou | [@zyxasd707](https://github.com/zyxasd707) |
| _TODO_ | Gaganish Yadav | [@gaganishyadav](https://github.com/gaganishyadav) |
| _TODO_ | Nicholas Tiew | [@Nickguin](https://github.com/Nickguin) |
| _TODO_ | Sawetr Suchit-rattanant | [@sawetr](https://github.com/sawetr) |

> Teammates: please replace the `TODO` cells with your UWA student IDs.

## Tech stack

- **Backend:** Flask (Python 3.13) + Flask-SQLAlchemy + Flask-Migrate (Alembic)
- **Database:** SQLite
- **Realtime:** Flask-SocketIO (WebSocket-based messaging)
- **Auth:** Flask session cookies + Flask-WTF (CSRF) + email OTP (Flask-Mail)
- **Frontend:** Jinja2 templates + Tailwind CSS + jQuery
- **Maps:** MazeMap (for UWA campus meetup-spot picker)
- **Testing:** pytest (unit) + Selenium WebDriver (system tests, real Chrome)

---

## Getting Started

### Prerequisites

- **Python 3.13** (or 3.11+ should also work)
- **Google Chrome** (only needed if you run the Selenium tests)
- **Git**

### Option A — Run inside a virtual environment (recommended)

A virtual environment isolates the project's Python dependencies from your
system Python so different projects don't conflict.

```bash
# 1) Clone and enter the project
git clone https://github.com/gaganishyadav/uwa-marketplace.git
cd uwa-marketplace

# 2) Create a virtual environment named 'venv'
python -m venv venv

# 3) Activate it
#    Windows (PowerShell):
.\venv\Scripts\Activate.ps1
#    Windows (cmd):
.\venv\Scripts\activate.bat
#    macOS / Linux:
source venv/bin/activate

# 4) Install dependencies
pip install -r requirements.txt

# 5) Configure environment, run migrations, and start the app
#    (see "Configure environment variables" and "Set up the database" below)
python run.py
```

You'll know the venv is active when your shell prompt starts with `(venv)`.
To leave the venv later, run `deactivate`.

### Option B — Run without a virtual environment

If you don't want to use a virtual environment (e.g. on a fresh machine where
you only run one Python project), you can install dependencies globally:

```bash
git clone https://github.com/gaganishyadav/uwa-marketplace.git
cd uwa-marketplace
pip install -r requirements.txt

# Configure environment, run migrations, and start the app
# (see "Configure environment variables" and "Set up the database" below)
python run.py
```

> ⚠️ This will install the project's dependencies into your system Python.
> Recommended only if you understand the trade-off; Option A is safer.

### Configure environment variables

Copy the example file and fill in real values:

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

Then open `.env` and set:

| Variable | What it does |
|---|---|
| `SECRET_KEY` | **Required.** A random string used to sign session cookies. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`. |
| `DATABASE_URL` | SQLite path. Default `sqlite:///marketplace.db` is fine. |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS` | SMTP server for sending OTP emails. Defaults work for Gmail. |
| `MAIL_USERNAME`, `MAIL_PASSWORD` | Your SMTP credentials (Gmail requires an *app password*, not your account password). |
| `MAIL_DEFAULT_SENDER` | The `From` address shown on outgoing emails. |
| `MAIL_SUPPRESS_SEND` | Set to `true` for local development — OTP codes will be logged to the console instead of actually emailed. Set to `false` only when SMTP is correctly configured. |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Used by the `seed-admin` CLI command to create the initial admin account. |

### Set up the database

This applies all Alembic migrations and creates the SQLite database with the
correct schema:

```bash
flask --app run.py db upgrade
```

### (Optional) Seed development data

To populate the database with a small catalog of demo listings:

```bash
flask --app run.py seed
```

To create the initial admin account from the `ADMIN_EMAIL` / `ADMIN_PASSWORD`
in your `.env`:

```bash
flask --app run.py seed-admin
```

### Run the application

```bash
python run.py
```

Open <http://127.0.0.1:5000> in your browser. Chrome / Firefox / Edge all work.

> **What does `python run.py` do?** It loads your `.env`, calls
> `create_app()` to build the Flask app, then starts Flask-SocketIO's dev
> server (which serves both HTTP and WebSocket on port 5000).

### Pulling new changes from `main`

If models / migrations were added after a `git pull`, re-run:

```bash
flask --app run.py db upgrade
```

If `requirements.txt` was updated, re-install:

```bash
pip install -r requirements.txt
```

---

## Running the tests

This project ships with **96 unit tests** and **5 Selenium WebDriver system
tests**, satisfying the rubric's *"5+ unit tests and 5+ selenium tests, run
against a live version of the server"* requirement.

### Unit tests (fast)

These exercise the routes and models through Flask's test client. They run in
under 15 seconds and don't need a browser. The suite covers all the core
domains of the application:

| File | What it tests |
|---|---|
| `test_admin.py` | Admin moderation actions: ban / unban / permanent-ban user, delete listing, feature listing, admin seed CLI command |
| `test_auth.py` | Registration (session-based OTP flow), OTP verification, login, lockout after repeated failed attempts, password reset, logout |
| `test_marketplace.py` | Listing CRUD: create with image upload, edit, mark-sold, delete; gallery and dashboard rendering; magic-byte image validation |
| `test_messaging.py` | Buyer-seller messaging: send, inbox, thread reply, sold-listing badges, per-sender rate limit (20/min) |
| `test_models.py` | Model-level invariants: password hashing, reset token generation/verification, user defaults |
| `test_search.py` | `/api/search` route: keyword, category, price-range, combined filters, empty state, LIKE-wildcard escaping |

#### Run all unit tests

```bash
# Easiest: run everything except the selenium files
pytest tests/ -v --ignore-glob='tests/test_selenium_*.py'

# Or list each file explicitly
pytest tests/test_admin.py tests/test_auth.py tests/test_marketplace.py \
       tests/test_messaging.py tests/test_models.py tests/test_search.py -v
```

Expected result: `96 passed in ~15s`.

#### Run a single unit-test file

Useful when iterating on one area of the codebase:

```bash
pytest tests/test_admin.py -v        # admin moderation
pytest tests/test_auth.py -v         # registration, OTP, login, lockout
pytest tests/test_marketplace.py -v  # listing CRUD + upload
pytest tests/test_messaging.py -v    # messaging + rate limit
pytest tests/test_models.py -v       # model invariants
pytest tests/test_search.py -v       # /api/search filters
```

#### Run a single test function

```bash
pytest tests/test_auth.py::test_login_lockout_triggers_after_max_attempts -v
```

### Selenium system tests (slower, real browser)

These spin up a real Flask + SocketIO server in a background thread on a
per-test port and drive a real Chrome browser through the full user flow.
Selenium auto-downloads the matching `chromedriver` on first run (you don't
need to install it manually).

The 5 selenium tests cover the full C2C lifecycle:

| File | User story |
|---|---|
| `test_selenium_listing_display.py` | Seller creates a listing with an image → it appears in the gallery (F2) |
| `test_selenium_search_display.py` | Anonymous buyer searches / filters / price-ranges the gallery (F3) |
| `test_selenium_message_display.py` | Buyer messages a seller → seller sees the message in their inbox (F4) |
| `test_selenium_mark_sold_display.py` | Seller marks a listing as sold → "Sold" badge appears everywhere (F5) |
| `test_selenium_admin_display.py` | Admin bans a user → banned user is blocked on next login (F6) |

#### Run all 5 selenium tests

```bash
pytest tests/test_selenium_*.py -v
```

Expected result: `5 passed in ~40s` (after first run; the first run takes
~10s longer because Chrome downloads its driver).

#### Run a single selenium test file

```bash
pytest tests/test_selenium_listing_display.py -v    # F2 create-listing
pytest tests/test_selenium_search_display.py -v     # F3 search/filter
pytest tests/test_selenium_message_display.py -v    # F4 messaging
pytest tests/test_selenium_mark_sold_display.py -v  # F5 mark-sold
pytest tests/test_selenium_admin_display.py -v      # F6 admin-ban
```

#### Run a single selenium test function

```bash
pytest tests/test_selenium_message_display.py::test_buyer_sends_message_and_seller_sees_it_in_inbox -v
```

### Selenium options: headless mode and demo pacing

By default Selenium tests open a visible Chrome window. You can override this
via environment variables:

| Env var | What it does |
|---|---|
| `HEADLESS=1` | Run Chrome in headless mode (no window). Use this for CI / fast iteration. |
| `DEMO_PAUSE=3` | Add a 3-second sleep between each UI step so a viewer / screen-recorder can follow along. Default 0 = no pause. |

Example — record a slow walk-through of the messaging test:

**PowerShell:**
```powershell
$env:DEMO_PAUSE="3"; pytest tests/test_selenium_message_display.py -v
```

**Bash / Zsh:**
```bash
DEMO_PAUSE=3 pytest tests/test_selenium_message_display.py -v
```

### Running the whole test suite

```bash
pytest -v
```

Expected result: `101 passed in ~55s` (96 unit + 5 selenium).

---

## Project structure

```
uwa-marketplace/
├── app/
│   ├── __init__.py          # Flask app factory + Jinja filters
│   ├── routes.py            # All HTTP routes
│   ├── socket_events.py     # WebSocket message handlers
│   ├── models.py            # SQLAlchemy models (User, Listing, Message)
│   ├── forms.py             # WTForms validators
│   ├── static/              # CSS, JS, uploaded images
│   └── templates/           # Jinja2 templates
├── migrations/              # Alembic database migrations
├── tests/                   # 96 unit tests + 5 selenium tests
├── .env.example             # Template for required environment variables
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── README.md                # This file
```

## Troubleshooting

- **`RuntimeError: SECRET_KEY is not set`** — copy `.env.example` to `.env`
  and fill in `SECRET_KEY`. The app refuses to start without one (intentional,
  for security).
- **`flask: command not found`** — make sure your virtual environment is
  activated, then re-run `pip install -r requirements.txt`.
- **Selenium test fails with `WebDriverException: chromedriver`** — install or
  update Google Chrome. Selenium 4.27 auto-downloads the matching driver on
  first run; you don't need to install chromedriver manually.
- **Port 5000 already in use** — kill the existing process or change the port
  in `run.py` (`socketio.run(app, port=5001, debug=True)`).
- **Selenium tests fail with port-binding errors** — the selenium tests use
  ports 5555-5559. Make sure nothing else is listening on those ports.
