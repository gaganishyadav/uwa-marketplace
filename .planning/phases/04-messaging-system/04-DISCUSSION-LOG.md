# Phase 4: Messaging System - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-25
**Phase:** 04-messaging-system
**Areas discussed:** Message Initiation Flow, Message Thread Layout, Inbox Design, Validation & Edge Cases, Read/Unread Indicators, Sold/Deleted Listing Behavior

---

## Message Initiation Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Modal | Click "Message Seller" -> modal pops up with text field. Consistent with existing Edit Listing modal pattern. | ✓ |
| Navigate to thread page | Click -> navigate to /conversation/<listing_id> page | |
| Inline expandable form | Click -> form expands below button on listing detail page | |

**User's choice:** Modal — consistent with existing Edit Listing modal pattern already in codebase.

---

## Message Thread Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Chat bubbles | Messages as bubbles aligned left (seller) and right (buyer) like Messenger. Timestamps below each bubble. | ✓ |
| Email-style blocks | Each message as a block with sender name, timestamp above, content below. More formal. | |

**User's choice:** Chat bubbles — conversational and familiar.

---

## Inbox Design

| Option | Description | Selected |
|--------|-------------|----------|
| List rows | Each conversation as a row: listing thumbnail, title, other user's name, last message preview, timestamp. Like email inbox. | ✓ |
| Cards | Each conversation as a card with listing image, title, last message, avatar. More visual but takes more space. | |

**User's choice:** List rows — compact and scannable.

---

## Thread View

| Option | Description | Selected |
|--------|-------------|----------|
| Same page, replace | Click conversation -> thread opens in-place, replacing inbox list. Back button returns. | ✓ |
| Separate thread page | Click -> navigate to /thread/<id> page. Full page for conversation. | |

**User's choice:** Same page, replace — simple one-page approach.

---

## Validation & Edge Cases

| Option | Description | Selected |
|--------|-------------|----------|
| Basic validation | Block self-messaging, reject empty, max 1000 chars. Inline errors. | ✓ |
| Minimal validation | Just block empty and self-messaging. No max length. | |

**User's choice:** Basic validation.

---

## Read/Unread Tracking

| Option | Description | Selected |
|--------|-------------|----------|
| No unread tracking | No read/unread for v1. Show all conversations newest first. | ✓ |
| Unread badges + highlighting | Bold unread conversations, badge count in nav. Requires is_read flag. | |

**User's choice:** No unread tracking — keep it simple.

---

## Sold/Deleted Listing Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Keep visible, block new | Sold: conversations visible for 30 days then auto-delete, no new messages. Deleted: show "Listing removed". | ✓ |
| Hide conversations | Conversations for sold/deleted listings hidden from inbox entirely. | |

**User's choice:** Keep visible for 30 days after sold, then auto-delete. Block new messages. Deleted listings show "Listing removed".

---

## Claude's Discretion

- Message model implementation details
- Thread pagination/scroll behavior
- Auto-delete implementation approach
- Modal form styling
- Route structure

## Deferred Ideas

None.
