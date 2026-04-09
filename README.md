# UWA Campus Swap-Meet

A Flask-based student marketplace for UWA to buy/sell textbooks, furniture, and campus essentials with safe campus meetups.

## Getting Started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up the database

```bash
flask db upgrade
```

This creates the SQLite database with the correct schema.

### 3. Run the application

```bash
flask run
```

Open http://127.0.0.1:5000 in your browser.

### Pulling new changes?

If models changed after a `git pull`, apply the new migrations:

```bash
flask db upgrade
```

### Running tests

```bash
pytest
```

## Tech Stack

- **Backend:** Flask (Python 3.x), SQLAlchemy ORM
- **Database:** SQLite (via Flask-SQLAlchemy)
- **Frontend:** HTML5, CSS, Tailwind, jQuery, Jinja2
- **Migrations:** Flask-Migrate (Alembic)
