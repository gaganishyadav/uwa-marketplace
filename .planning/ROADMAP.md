# Roadmap: UWA Campus Swap-Meet

## Overview

This roadmap delivers a hyper-local student marketplace for UWA, progressing from foundation through authentication, marketplace features, search, messaging, and admin controls. The project is organized into 7 phases aligned with three academic milestones, ensuring students can securely trade goods on campus.

**Milestone 1 (Phases 1-2):** Foundation + Basic Marketplace
**Milestone 2 (Phases 3-4):** Discovery + Messaging
**Milestone 3 (Phases 5-7):** Security + Testing + Admin + Polish

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Flask Foundation & Authentication** - Project setup, user registration, login, logout
- [ ] **Phase 2: Marketplace Core** - Listing CRUD, public gallery, category management
- [x] **Phase 3: Search & Discovery** - AJAX search, filtering, category UI
- [x] **Phase 4: Messaging System** - Buyer-seller messaging with inbox
- [x] **Phase 5: Admin Account & Authority** - Admin roles, admin dashboard, user/listing management
- [ ] **Phase 6: Security Hardening** - CSRF, password hashing, session security, input validation
- [ ] **Phase 7: Testing Suite** - Unit tests, Selenium tests, coverage

## Phase Details

### Phase 1: Flask Foundation & Authentication
**Goal**: Users can create accounts and securely access the platform
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-04, SEC-06
**Success Criteria** (what must be TRUE):
  1. User can register account with email, password, and optional student ID
  2. User can log in and stay logged in across browser sessions
  3. User can log out from any page
  4. User sessions timeout after inactivity for security
**Plans**: 2 plans

Plans:
- [x] 01-PLAN.md -- Flask foundation: app factory, User model, forms, test infrastructure
- [x] 02-PLAN.md -- Auth routes, templates, static migration, integration tests, human verification

**UI hint**: yes

### Phase 2: Marketplace Core
**Goal**: Users can create, view, edit, and delete marketplace listings
**Depends on**: Phase 1
**Requirements**: MARKET-01, MARKET-02, MARKET-03, MARKET-04, MARKET-05
**Success Criteria** (what must be TRUE):
  1. User can create listing with title, description, price, category, and photo
  2. User can view public gallery of all active listings in grid format
  3. User can edit own listings (changes reflect immediately)
  4. User can delete own listings (removed from gallery)
  5. User can mark item as sold (listing shows sold status)
**Plans**: TBD

**UI hint**: yes

### Phase 3: Search & Discovery
**Goal**: Users can find relevant listings using real-time search and category filtering
**Depends on**: Phase 2
**Requirements**: MARKET-06, MARKET-07, MARKET-08
**Success Criteria** (what must be TRUE):
  1. User can search listings by keyword without page reload (AJAX)
  2. User can filter by category (Textbooks, Furniture, Electronics, Other)
  3. User can filter by price range (min/max inputs)
  4. Search results update in real-time as user types
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md -- Search API endpoint, HTML partial template, unit tests (TDD)
- [x] 03-02-PLAN.md -- Search UI: gallery template, CSS styles, jQuery AJAX search.js
- [x] 03-03-PLAN.md -- Flask seed CLI command for mock data

**UI hint**: yes

### Phase 4: Messaging System
**Goal**: Buyers and sellers can communicate about listings
**Depends on**: Phase 2
**Requirements**: MSG-01, MSG-02, MSG-03
**Success Criteria** (what must be TRUE):
  1. Buyer can send message to listing owner from listing page
  2. User can view message thread for each listing
  3. User can view inbox with all conversations
  4. Messages show sender, timestamp, and content in readable format
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md -- Data layer: Message model, sold_at field, soft-delete refactor, MessageForm, migration
- [x] 04-02-PLAN.md -- Messaging routes and send message flow: send_message, inbox, thread routes, message modal, nav link
- [x] 04-03-PLAN.md -- Inbox UI and tests: inbox.html template, chat bubble CSS, unit tests for MSG-01/02/03

**UI hint**: yes

### Phase 5: Admin Account & Authority
**Goal**: Admin users can manage users, listings, and moderate the marketplace from the existing gallery (no separate dashboard)
**Depends on**: Phase 1
**Requirements**: ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04, ADMIN-05, ADMIN-06, ADMIN-07, ADMIN-08, ADMIN-09, ADMIN-10
**Success Criteria** (what must be TRUE):
  1. Admin account exists with elevated privileges (is_admin flag on User model)
  2. Admin can view and manage all users (view, ban/unban)
  3. Admin can view and manage all listings (delete, feature/unfeature)
  4. Admin controls are integrated into the gallery (no separate dashboard)
  5. Regular users cannot access admin routes (receive 403 Forbidden)
  6. Banned users are completely blocked from the app
  7. Featured listings appear at the top of the gallery with a badge
**Plans**: 4 plans

Plans:
- [x] 05-01-PLAN.md -- Data layer: is_admin/ban_status on User, is_featured on Listing, migration, seed-admin CLI
- [x] 05-02-PLAN.md -- Backend: admin_required decorator, admin routes, ban interception, 403 handler, featured-first sorting
- [x] 05-03-PLAN.md -- Templates and CSS: admin card controls, featured badge, admin user page, banned page, 403 page
- [x] 05-04-PLAN.md -- Tests: admin_client fixture, all ADMIN-01 through ADMIN-10 tests

**UI hint**: yes

### Phase 6: Security Hardening
**Goal**: Platform protects against common web vulnerabilities and securely stores credentials
**Depends on**: Phase 1, Phase 2
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04, SEC-05
**Success Criteria** (what must be TRUE):
  1. All passwords stored as salted hashes (not plaintext)
  2. All form submissions protected by CSRF tokens
  3. User input is validated and sanitized before database storage
  4. Database queries use parameterized queries (ORM protection)
  5. Sensitive configuration (SECRET_KEY) stored in .env file
**Plans**: TBD

### Phase 7: Testing Suite
**Goal**: Codebase has comprehensive test coverage for models, auth, and user journeys
**Depends on**: Phase 1, Phase 2, Phase 3
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06
**Success Criteria** (what must be TRUE):
  1. 5+ unit tests cover models, password hashing, and route access control
  2. 5+ Selenium tests cover login, posting listing, and AJAX search flows
  3. All tests pass consistently
  4. Test suite can run via single command (pytest/pytest-selenium)
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Flask Foundation & Authentication | 2/2 | Complete | 2026-04-04 |
| 2. Marketplace Core | 3/3 | Complete | - |
| 3. Search & Discovery | 3/3 | Complete | 2026-04-20 |
| 4. Messaging System | 3/3 | Complete | 2026-04-25 |
| 5. Admin Account & Authority | 4/4 | Complete | 2026-05-06 |
| 6. Security Hardening | 0/0 | Not started | - |
| 7. Testing Suite | 0/0 | Not started | - |

---

*Last updated: 2026-05-05*
