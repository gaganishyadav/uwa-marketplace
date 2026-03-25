# UWA Campus Swap-Meet — Requirements

## User Authentication

| Feature | Scope | Priority |
|---------|-------|----------|
| User registration (email, password, student ID optional) | v1 | P0 |
| Secure login with session management | v1 | P0 |
| Password reset (email-based) | v2 | P1 |
| Logout | v1 | P0 |
| Remember me (persistent sessions) | v2 | P2 |

## Marketplace Features

| Feature | Scope | Priority |
|---------|-------|----------|
| Public gallery (all active listings) | v1 | P0 |
| Create listing (title, description, price, category, photos) | v1 | P0 |
| Edit own listings | v1 | P0 |
| Delete own listings | v1 | P0 |
| Mark item as sold | v1 | P1 |
| AJAX search (by keyword, category, price range) | v1 | P0 |
| Category filtering (Textbooks, Furniture, Electronics, Other) | v1 | P0 |

## Campus Map Integration

| Feature | Scope | Priority |
|---------|-------|----------|
| Leaflet.js map of UWA campus | v1 | P0 |
| Predefined meetup spots (Library, Guild Village, etc.) | v1 | P0 |
| Seller selects meetup spot when creating listing | v1 | P0 |
| Buyer sees selected spot on map | v1 | P0 |

## Messaging

| Feature | Scope | Priority |
|---------|-------|----------|
| Send message to listing owner | v1 | P0 |
| View message thread per listing | v1 | P0 |
| Inbox view (all conversations) | v1 | P1 |
| Message notifications | v2 | P2 |

## Security

| Feature | Scope | Priority |
|---------|-------|----------|
| Salted password hashing (werkzeug.security) | v1 | P0 |
| CSRF protection (Flask-WTF) | v1 | P0 |
| Input validation and sanitization | v1 | P0 |
| SQL injection prevention (ORM parameterized queries) | v1 | P0 |
| Secrets in .env (python-dotenv) | v1 | P0 |
| Session security (secure cookies, timeout) | v1 | P0 |

## Testing

| Feature | Scope | Priority |
|---------|-------|----------|
| Unit tests for models (5+ tests) | v1 | P0 |
| Unit tests for password hashing | v1 | P0 |
| Unit tests for route access control | v1 | P0 |
| Selenium tests for login flow | v1 | P0 |
| Selenium tests for posting listing | v1 | P0 |
| Selenium tests for AJAX search | v1 | P0 |

## Data Model

- **Users**: id, email, password_hash, student_id, created_at
- **Listings**: id, user_id, title, description, price, category, meetup_spot, image_path, status, created_at
- **Messages**: id, listing_id, sender_id, receiver_id, content, created_at

## Categories

1. Textbooks
2. Furniture
3. Electronics
4. Campus Essentials
5. Other

## Campus Meetup Spots

1. Reid Library
2. Eileen Joy/Music Library
3. Barry J Marshall Library
4. Guild Village
5. Oak Lawn
6. Tropical Grove
7. Somerville Auditorium

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01: User registration | Phase 1 | Pending |
| AUTH-02: Secure login with session management | Phase 1 | Pending |
| AUTH-04: Logout | Phase 1 | Pending |
| MARKET-01: Public gallery | Phase 2 | Pending |
| MARKET-02: Create listing | Phase 2 | Pending |
| MARKET-03: Edit own listings | Phase 2 | Pending |
| MARKET-04: Delete own listings | Phase 2 | Pending |
| MARKET-05: Mark item as sold | Phase 2 | Pending |
| MARKET-06: AJAX search | Phase 3 | Pending |
| MARKET-07: AJAX price range search | Phase 3 | Pending |
| MARKET-08: Category filtering | Phase 3 | Pending |
| MAP-01: Leaflet.js campus map | Phase 4 | Pending |
| MAP-02: Predefined meetup spots | Phase 4 | Pending |
| MAP-03: Seller selects meetup spot | Phase 4 | Pending |
| MAP-04: Buyer sees selected spot | Phase 4 | Pending |
| MSG-01: Send message to listing owner | Phase 5 | Pending |
| MSG-02: View message thread | Phase 5 | Pending |
| MSG-03: Inbox view | Phase 5 | Pending |
| SEC-01: Salted password hashing | Phase 6 | Pending |
| SEC-02: CSRF protection | Phase 6 | Pending |
| SEC-03: Input validation and sanitization | Phase 6 | Pending |
| SEC-04: SQL injection prevention | Phase 6 | Pending |
| SEC-05: Secrets in .env | Phase 6 | Pending |
| SEC-06: Session security | Phase 6 | Pending |
| TEST-01: Unit tests for models | Phase 7 | Pending |
| TEST-02: Unit tests for password hashing | Phase 7 | Pending |
| TEST-03: Unit tests for route access control | Phase 7 | Pending |
| TEST-04: Selenium tests for login flow | Phase 7 | Pending |
| TEST-05: Selenium tests for posting listing | Phase 7 | Pending |
| TEST-06: Selenium tests for AJAX search | Phase 7 | Pending |

---
*Generated: 2026-03-25*
*Traceability updated: 2026-03-25*
