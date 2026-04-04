# Roadmap: UWA Campus Swap-Meet

## Overview

This roadmap delivers a hyper-local student marketplace for UWA, progressing from foundation through authentication, marketplace features, search, messaging, and campus map integration. The project is organized into 7 phases aligned with three academic milestones, ensuring students can securely trade goods with safe campus meetups.

**Milestone 1 (Phases 1-2):** Foundation + Basic Marketplace
**Milestone 2 (Phases 3-5):** Discovery + Messaging
**Milestone 3 (Phases 6-7):** Security + Testing + Polish

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Flask Foundation & Authentication** - Project setup, user registration, login, logout
- [ ] **Phase 2: Marketplace Core** - Listing CRUD, public gallery, category management
- [ ] **Phase 3: Search & Discovery** - AJAX search, filtering, category UI
- [ ] **Phase 4: Campus Map Integration** - Leaflet.js integration with meetup spot selection
- [ ] **Phase 5: Messaging System** - Buyer-seller messaging with inbox
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
- [ ] 01-PLAN.md -- Flask foundation: app factory, User model, forms, test infrastructure
- [ ] 02-PLAN.md -- Auth routes, templates, static migration, integration tests, human verification

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
**Plans**: TBD

**UI hint**: yes

### Phase 4: Campus Map Integration
**Goal**: Users can select and view campus meetup locations using interactive map
**Depends on**: Phase 2
**Requirements**: MAP-01, MAP-02, MAP-03, MAP-04
**Success Criteria** (what must be TRUE):
  1. Seller can select predefined meetup spot when creating listing
  2. Buyer sees selected meetup spot pinned on interactive campus map
  3. Map displays all 7 UWA campus locations (libraries, guild, oak lawn, etc.)
  4. Map is responsive and loads without blocking page render
**Plans**: TBD

**UI hint**: yes

### Phase 5: Messaging System
**Goal**: Buyers and sellers can communicate about listings
**Depends on**: Phase 2
**Requirements**: MSG-01, MSG-02, MSG-03
**Success Criteria** (what must be TRUE):
  1. Buyer can send message to listing owner from listing page
  2. User can view message thread for each listing
  3. User can view inbox with all conversations
  4. Messages show sender, timestamp, and content in readable format
**Plans**: TBD

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
| 1. Flask Foundation & Authentication | 1/2 | In progress | - |
| 2. Marketplace Core | 0/0 | Not started | - |
| 3. Search & Discovery | 0/0 | Not started | - |
| 4. Campus Map Integration | 0/0 | Not started | - |
| 5. Messaging System | 0/0 | Not started | - |
| 6. Security Hardening | 0/0 | Not started | - |
| 7. Testing Suite | 0/0 | Not started | - |

---

*Last updated: 2026-04-04*
