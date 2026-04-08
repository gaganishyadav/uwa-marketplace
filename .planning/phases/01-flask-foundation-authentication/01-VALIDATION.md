---
phase: 1
slug: flask-foundation-authentication
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4 |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | AUTH-01 | unit | `pytest tests/test_auth.py::test_register_success -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | AUTH-01 | unit | `pytest tests/test_auth.py::test_register_invalid_email -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | AUTH-01 | unit | `pytest tests/test_auth.py::test_register_duplicate_email -x` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | AUTH-01 | unit | `pytest tests/test_auth.py::test_register_weak_password -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | AUTH-02 | unit | `pytest tests/test_auth.py::test_login_success -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | AUTH-02 | unit | `pytest tests/test_auth.py::test_login_wrong_password -x` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | AUTH-02 | unit | `pytest tests/test_auth.py::test_unverified_redirect -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 1 | AUTH-04 | unit | `pytest tests/test_auth.py::test_logout -x` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 2 | SEC-06 | unit | `pytest tests/test_auth.py::test_csrf_required -x` | ❌ W0 | ⬜ pending |
| 01-05-01 | 05 | 2 | SEC-06 | unit | `pytest tests/test_models.py::test_password_hashing -x` | ❌ W0 | ⬜ pending |
| 01-06-01 | 06 | 2 | AUTH-01 | unit | `pytest tests/test_models.py::test_otp_generation -x` | ❌ W0 | ⬜ pending |
| 01-07-01 | 07 | 2 | AUTH-01 | unit | `pytest tests/test_models.py::test_reset_token -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — pytest fixtures (Flask app client, test database, test config)
- [ ] `tests/test_auth.py` — covers AUTH-01, AUTH-02, AUTH-04, SEC-06 route tests
- [ ] `tests/test_models.py` — covers password hashing, OTP, reset token tests
- [ ] Framework install: pytest already available (8.3.4)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| OTP email delivery | AUTH-01 | Requires real SMTP server | Register with real email, check inbox for OTP |
| Password reset email | AUTH-01 | Requires real SMTP server | Click "Forgot Password", check email for reset link |
| Auth page visual design | AUTH-01 | Visual verification | Compare rendered auth.html with DESIGN.md system |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
