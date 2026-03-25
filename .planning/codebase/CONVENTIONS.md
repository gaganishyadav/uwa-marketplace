# Coding Conventions

**Analysis Date:** 2026-03-25

## Naming Patterns

**Files:**
- HTML: lowercase with hyphens for compound words (e.g., `index.html`, future pages like `listing.html`, `profile.html`)
- CSS: lowercase with hyphens (e.g., `styles.css` in `css/` directory)
- Python (planned): snake_case for modules (e.g., `models.py`, `routes.py`, `test_unit.py`)
- Tests: prefixed with `test_` (e.g., `test_unit.py`, `test_selenium.py`)

**Functions:**
- Python: snake_case (e.g., `create_listing()`, `hash_password()`, `get_user_by_id()`)

**Variables:**
- Python: snake_case (e.g., `password_hash`, `user_id`, `listing_title`)
- CSS: hyphenated for custom properties (e.g., `--color-primary`, `--font-headline`)

**Classes:**
- Python: PascalCase for SQLAlchemy models (e.g., `User`, `Listing`)

## Code Style

**Formatting:**
- HTML: 4-space indentation, semantic tags
- CSS: 4-space indentation, organized by sections with comment headers
- Python: 4-space indentation (PEP 8)

**Linting:**
- Not currently configured
- Python: flake8 or pylint recommended (planned)

## Import Organization

**Python (planned structure):**
1. Standard library imports
2. Third-party imports (Flask, SQLAlchemy, etc.)
3. Local application imports

```python
# Standard library
import os
from datetime import datetime

# Third-party
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# Local
from app.models import User, Listing
```

**Path Aliases:**
- None currently configured
- Planned: Flask's template and static folder handling

**CSS imports:**
- Google Fonts loaded via `<link>` in `<head>`
- Local stylesheets referenced with relative paths: `css/styles.css`

## Error Handling

**Patterns:**
- Flask routes: Use `flash()` for user-facing errors
- Database: SQLAlchemy session rollback on transaction errors
- Forms: Flask-WTF validation with error messages

## Logging

**Framework:** Flask's built-in logging (planned)

**Patterns:**
- Use `app.logger` for application logging
- Log security events (login attempts, failed auth)
- Log database errors for debugging

## Comments

**When to Comment:**
- CSS: Section headers with design system context (e.g., `/* UWA SWAP-MEET DESIGN SYSTEM */`)
- Python: Docstrings for model classes and route functions
- HTML: Section comments for major blocks (e.g., `<!-- Navigation -->`, `<!-- Hero Section -->`)

**JSDoc/TSDoc:**
- Not applicable (no TypeScript)
- Python: Use docstrings for functions/classes following PEP 257

```python
def create_listing(title, description, price, category, user_id):
    """Create a new marketplace listing.

    Args:
        title: Listing title
        description: Item description
        price: Price in AUD
        category: Category enum
        user_id: Foreign key to User

    Returns:
        Listing object
    """
```

## Function Design

**Size:** Keep under 50 lines where possible

**Parameters:**
- Use keyword arguments for clarity
- Group related parameters

**Return Values:**
- Routes: Return rendered templates or JSON responses
- Model methods: Return query results or None

## Module Design

**Exports:**
- Python: Use explicit imports, avoid `import *`

**Barrel Files:**
- Flask app factory pattern via `app/__init__.py`

## HTML/CSS Conventions

**HTML:**
- Semantic HTML5 elements (`<nav>`, `<section>`, `<footer>`)
- BEM-like class naming: `.nav`, `.nav-container`, `.nav-brand`
- Section IDs for anchor navigation: `#browse`, `#how-it-works`, `#about`

**CSS:**
- CSS custom properties in `:root` for design tokens
- Organized by component sections
- Mobile-first responsive design with `@media` queries
- Smooth scroll behavior: `html { scroll-behavior: smooth; }`

**Design System Variables:**
- Colors: `--color-primary`, `--color-secondary`, `--color-background`
- Typography: `--font-headline` (Manrope), `--font-body` (Inter)
- Spacing: `--space-xs` through `--space-2xl`
- Border radius: `--radius-sm` through `--radius-full`
- Shadows: `--shadow-sm` through `--shadow-xl`
- Transitions: `--transition-fast`, `--transition-normal`

**Gradient Usage:**
- Primary: `linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-container) 100%)`
- Accent: `linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%)`

**Glass Morphism Effect:**
- Background: `rgba(255, 255, 255, 0.8)`
- Backdrop filter: `blur(8px)` or `blur(12px)`

---

*Convention analysis: 2026-03-25*
