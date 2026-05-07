# Admin Feature Testing Guide

This guide explains how to set up admin access and test all admin features of the UWA Swap-Meet marketplace.

---

## 1. Set Up Admin Access

### Step 1: Add admin credentials to `.env`

Open the `.env` file in the project root and add these two lines at the end:

```
ADMIN_EMAIL=admin@uwa.edu.au
ADMIN_PASSWORD=Admin123
```

### Step 2: Apply database migration

```bash
flask db upgrade
```

### Step 3: Seed the admin account

```bash
flask seed-admin
```

You should see: `Admin account created: admin@uwa.edu.au`

(If you run it again, it will say `Admin account already exists` — that's expected.)

### Step 4: Start the dev server

```bash
flask run
```

---

## 2. Log In as Admin

1. Open http://127.0.0.1:5000 in your browser
2. Click **Get Started** to go to the login page
3. Enter:
   - **Email:** `admin@uwa.edu.au`
   - **Password:** `Admin123`
4. You'll receive an OTP (check terminal output since `MAIL_SUPPRESS_SEND=true`)
5. Enter the OTP to verify

You're now logged in as admin. You'll see the same gallery as regular users, but with extra controls.

---

## 3. Test Admin Features

### 3.1 Admin Controls on Gallery Cards

**What to check:** Every listing card on the gallery should show **Delete** and **Feature** buttons at the bottom (in addition to the normal card content).

1. Go to the gallery at http://127.0.0.1:5000/
2. On each listing card, you should see two small buttons:
   - **Delete** (red text) — soft-deletes the listing
   - **Feature** (blue text) — toggles the featured status
3. Click **Feature** on a listing
   - The page reloads
   - A flash message says "Listing featured."
   - The card now shows a **"Featured"** badge on the top-left of the image
   - The listing moves to the top of the gallery
4. Click **Feature** again to unfeature
   - Flash message says "Listing unfeatured."
   - Badge disappears, listing returns to normal position
5. Click **Delete** on a listing
   - Flash message says "Listing deleted by admin."
   - The listing disappears from the gallery

### 3.2 Admin User Moderation

**What to check:** Admin can view any user's profile and ban/unban them.

1. Click on any listing to open its **detail page** (e.g., http://127.0.0.1:5000/listing/1)
2. The **seller's name** (below the listing image) should be a clickable **link**
3. Click the seller name — you land on the **Admin User Detail** page
4. On this page you should see:
   - User avatar (first letter of name)
   - Display name and email
   - Status badge: **Active** (blue)
   - Join date, listing count, email verified status
   - **Moderation Actions** section with:
     - **Ban User** button (amber text)
     - **Permanent Ban** button (red text)

**Test Ban:**
1. Click **Ban User**
   - Flash message: "[Name] has been banned."
   - Status badge changes to **Banned** (red)
   - Buttons change to just **Unban User** (blue)

**Test Unban:**
1. Click **Unban User**
   - Flash message: "[Name] has been unbanned."
   - Status badge returns to **Active**
   - Ban/Permanent Ban buttons reappear

**Test Permanent Ban:**
1. Click **Permanent Ban**
   - Flash message: "[Name] has been permanently banned."
   - Status badge changes to **Permanently Banned** (red)

### 3.3 Banned User Experience

**What to check:** Banned users are completely blocked from the app.

1. First, ban a user (see 3.2 above)
2. Log out (click avatar → **Log Out**)
3. Log in as the banned user
4. You should be immediately redirected to a **"Account Suspended"** page
   - Shows a block icon
   - Message: "Your account has been suspended by an administrator."
   - Only action available: **Log Out** button
5. The banned user cannot access any other page — they're always redirected back to `/banned`

### 3.4 Seller Suspended Label

**What to check:** Listings from banned sellers show a "Seller suspended" label.

1. Ban a user who has active listings (see 3.2)
2. Go back to the gallery
3. That user's listings should still be visible, but with a small **"Seller suspended"** label in italic red text on the card

### 3.5 Non-Admin Access Denied (403)

**What to check:** Regular users cannot access admin URLs.

1. Log out
2. Create a regular account (or log in as a non-admin user)
3. Try visiting these URLs directly:
   - http://127.0.0.1:5000/admin/user/1
   - http://127.0.0.1:5000/admin/delete-listing/1 (POST only, but GET still shows 403 page)
4. You should see a **"Access Denied"** page with:
   - Lock icon
   - Message: "You do not have permission to access this page."
   - **Back to Gallery** link

### 3.6 Featured Listings Sort Order

**What to check:** Featured listings always appear at the top of the gallery.

1. Feature 1-2 listings (see 3.1)
2. Go to the gallery
3. Featured listings (with the blue badge) should appear **before** all other active listings
4. Regular active listings come next, then sold listings
5. The same sort order applies to **search results** — try searching with the search bar

### 3.7 Admin Search Results

**What to check:** Admin controls appear in search results just like the gallery.

1. Go to the gallery
2. Type a search term in the search bar
3. The search results should show the same **Delete** and **Feature** buttons on each card
4. Featured listings in search results show the badge and sort to the top

---

## 4. Quick Test Checklist

| # | Test | Expected Result | Pass? |
|---|------|-----------------|-------|
| 1 | `flask seed-admin` creates admin account | Success message in terminal | |
| 2 | `flask seed-admin` run again | "already exists" message | |
| 3 | Admin login works | Logged in, sees gallery | |
| 4 | Gallery cards show Delete/Feature buttons | Buttons visible on every card | |
| 5 | Feature a listing | Badge appears, listing moves to top | |
| 6 | Unfeature a listing | Badge disappears | |
| 7 | Delete a listing | Listing removed from gallery | |
| 8 | Seller name is clickable on detail page | Links to /admin/user/<id> | |
| 9 | Ban a user | Status changes to Banned | |
| 10 | Unban a user | Status changes to Active | |
| 11 | Permanent ban a user | Status changes to Permanently Banned | |
| 12 | Banned user sees suspended page | Cannot access any other page | |
| 13 | Banned user can still log out | Logout button works on /banned | |
| 14 | Banned seller's cards show "Seller suspended" | Red italic label visible | |
| 15 | Non-admin gets 403 on /admin/* | Access Denied page shown | |
| 16 | Featured listings sort to top in gallery | Featured before active before sold | |
| 17 | Featured listings sort to top in search | Same ordering in search results | |
| 18 | Admin controls appear in search results | Delete/Feature buttons on cards | |

---

## 5. Running Automated Tests

All 18 admin tests can be run with:

```bash
pytest tests/test_admin.py -v
```

Run the full suite (90 tests):

```bash
pytest tests/ -v
```
