Project Specification: UWA Campus Swap-Meet

1. Executive Summary

Project Name: UWA Campus Swap-Meet

Objective: To develop a hyper-local, student-centric marketplace application that facilitates the buying, selling, and swapping of academic materials and campus essentials within the University of Western Australia community.

2. Technical Stack & Constraints

To ensure full compliance with the CITS3403/CITS5505 unit requirements, the following stack is mandatory:

Backend: Python 3.x using the Flask framework.

Database: SQLite managed via Flask-SQLAlchemy (ORM).

Frontend: HTML5, CSS (via Tailwind CSS), and jQuery.

Templating: Jinja2 for dynamic page generation.

Forbidden Technologies: Do NOT use React, Angular, Vue, SASS, or MySQL.

3. Security & Data Integrity

# Important : I will think about this later.
Authentication: User passwords must be stored using salted hashes (werkzeug.security).

Protection: Mandatory implementation of CSRF tokens using Flask-WTF.

Secrets: All sensitive keys (Secret Key, API keys) must be stored in a .env file and accessed via python-dotenv.

4. Functional Requirements

A. User Management

Secure Registration and Login/Logout functionality.

Persistence of user sessions across browser restarts.

B. Marketplace Gallery

Public Feed: A grid-based view of all active listings from all users.

AJAX Filtering: Real-time search and category filtering (e.g., "Textbooks", "Furniture") using jQuery/AJAX to prevent full-page reloads.

C. Listing Lifecycle

Users can create listings with titles, descriptions, prices, and categories.

Users have full CRUD (Create, Read, Update, Delete) permissions over their own items.

D. Location & Mapping

Leaflet.js Integration: Interactive map of the UWA campus.

Meetup Spots: Sellers can designate specific safe meeting locations (e.g., Reid Library, Guild Village) by dropping a pin on the map.

5. Database Schema

User Table: id, username, email, password_hash.

Listing Table: id, title, description, price, category, timestamp, latitude, longitude, user_id (FK).

6. Testing Strategy

Unit Tests (5+): Focus on model validation, password hashing, and route access control.

Selenium Tests (5+): Focus on the user journey, including login flow, item posting, and AJAX search functionality.

7. Project Structure

/
├── app/
│   ├── static/          # CSS, JS, and image assets
│   ├── templates/       # Jinja2 templates (base.html, index.html, etc.)
│   ├── models.py        # SQLAlchemy Database models
│   ├── routes.py        # Flask route handlers
│   └── __init__.py      # App factory and configuration
├── tests/
│   ├── test_unit.py     # Backend unit tests
│   └── test_selenium.py # Frontend integration tests
├── .env                 # Environment variables (excluded from Git)
├── requirements.txt     # Python dependencies
└── run.py               # Entry point for the application


8. Milestone Objectives

Checkpoint 1: Repository setup, README completion, and initial Flask environment.

Checkpoint 2: Responsive UI design and Jinja2 template integration.

Checkpoint 3: Database integration, Security implementation, and AJAX features.