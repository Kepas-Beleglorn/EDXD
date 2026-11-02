# `edxd_timestamp.json` — Journal Timestamp

**Location:** `APP_DIR/edxd_timestamp.json`

**Purpose:** Stores the ISO 8601 timestamp of the last processed journal entry. Used by the Journal Historian and Journal Controller to resume processing from where they left off, avoiding re-processing of already-handled journal files. On a full Journal Historian reprocess, this file is deleted so all journal entries are re-read.

**Written by:** `JournalController` via `data_helper.update_last_timestamp()` after each journal event

**Read by:** `JournalController` via `data_helper.read_last_timestamp()` to determine which events to process

## Structure

```json
{
  "last_timestamp": "2026-04-30T21:37:46Z"
}
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `last_timestamp` | `str` | ISO 8601 UTC timestamp of the last processed journal event, e.g., `"2026-04-30T21:37:46Z"` |
