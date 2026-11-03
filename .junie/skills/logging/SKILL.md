---
name: logging
description: Enforces consistent logging in all new EDXD code. Whenever you implement new code, logging must be part of it — debug, info, warn, and error entries should be included where they make sense, matching the existing logging style.
---

# EDXD Logging Skill

Whenever you implement new code in EDXD, logging must be part of that implementation. New code should include appropriate log entries for `debug`, `info`, `warning`, and `error` levels depending on the functionality. All logging must fit the existing logging conventions in the codebase.

## When to trigger

- You are about to write or modify any Python code in the EDXD project.
- The user asks you to implement a new feature, fix a bug, or refactor existing code.
- You are creating a new module, class, or function.

**DO NOT trigger** when editing non-Python files (e.g., Markdown, TOML, Dockerfiles) or when the change is purely cosmetic (e.g., renaming a variable without changing behavior).

## The golden rule

> **No new code without logging.** Every new function, method, class, or module must include logging that follows the established patterns. Logging is not optional — it is a first-class concern alongside correctness and performance.

## Logging setup in every module

Every Python module that performs any meaningful work must declare a module-level logger:

```python
import logging

logger = logging.getLogger(__name__)
```

Place this near the top of the file, after imports. Use `__name__` — never hard-code a logger name. This ensures the logger name reflects the module path (e.g., `EDXD.data_handler.helper.spansh.spansh`).

## Log levels — when to use each

### `logger.debug()` — Fine-grained diagnostic detail

Use for information that is useful during development and debugging but noisy in production:

- **Data inspection:** values of variables, intermediate computation results, loop iterations.
- **Parsing attempts:** when trying to parse a filename, JSON, or any structured data.
- **Missing optional data:** when a key is absent but the code handles it gracefully.
- **Cache checks:** whether a value was found in cache or needs to be fetched.
- **File operations:** before saving or loading a file.

Examples from the codebase:

```python
logger.debug("Saving data to %s", path)
logger.debug("Could not parse timestamp from journal filename: %s", f.name)
logger.debug("Missing parent star for %s[%s]: %s", body.body_name, body_id, parent_item)
logger.debug("Enum value not found %s(%s): %s", enum_class, value, e)
```

### `logger.info()` — Lifecycle and operational events

Use for notable events that indicate normal progress of the application:

- **Initialization:** when a component starts, a file is opened, a service connects.
- **Configuration changes:** when settings are loaded, changed, or applied.
- **State transitions:** when the application moves between major states.
- **External interactions:** successful API calls, version checks, lock acquisition/release.
- **User-facing actions:** when a user-triggered action completes successfully.

Examples from the codebase:

```python
logger.info("Journal reader initialized for folder: %s", folder)
logger.info("Journal file opened: %s", self.cur.name)
logger.info("New journal detected: %s", self.cur.name)
logger.info("Config loaded from %s", CFG_FILE)
logger.info("Lock acquired using %s method", self.method)
logger.info("Lock released")
logger.info("Log level changed to: %s", log_level_str)
logger.info("Latest release version: %s", version)
```

### `logger.warning()` — Recoverable issues

Use for situations that are unexpected but the code can continue:

- **Failed file load with fallback:** when a file cannot be loaded but a default is returned.
- **Deprecated paths:** when code takes a fallback or legacy path.
- **Missing optional configuration:** when a config key is absent but a sensible default is used.
- **Non-critical API failures:** when an external service returns unexpected data but the request can be retried or ignored.

Examples from the codebase:

```python
logger.warning("Failed to load %s: %s", path, e)
```

### `logger.error()` — Errors and exceptions

Use for failures that prevent a specific operation from completing:

- **Exception handlers:** always log the exception with context in `except` blocks.
- **Failed file save:** when writing data fails.
- **API failures:** when an external request fails and cannot be retried.
- **Data corruption:** when expected data is missing or malformed.
- **Encoding/decoding failures:** when converting between formats fails.

Examples from the codebase:

```python
logger.error("Failed to save %s: %s", path, e)
logger.error("Failed to parse journal event: %s", e)
logger.error("get_system_data[%s]: %s - %s", system_id, lookup_star_class, e)
logger.error("get_parent_star_ids[1] %s/%s/%s/%s: %s", current_body.body_id, current_body.body_name, current_body.body_type, current_body.parents, e)
logger.error("encode_body_type: %s", e)
```

## Message formatting rules

### Always use lazy formatting with `%` placeholders

**NEVER** use f-strings, `.format()`, or string concatenation in log calls:

```python
# WRONG — f-string evaluates even if log level is disabled
logger.debug(f"Processing body {body_id} with {len(data)} entries")

# WRONG — string concatenation
logger.error("Failed to load " + str(path) + ": " + str(e))

# CORRECT — lazy formatting, only evaluated when the message is actually logged
logger.debug("Processing body %s with %d entries", body_id, len(data))
logger.error("Failed to load %s: %s", path, e)
```

This is critical for `debug` logs, which are suppressed in production — f-strings would still execute the string formatting even when the log is not emitted.

### Include context in every message

Every log message should contain enough context to identify what operation was being performed:

- **File paths** when doing I/O
- **System IDs, body IDs, or other identifiers** when processing data
- **Function/method name** in error messages when the context is not obvious from the logger name
- **Exception details** in error handlers

Pattern for error messages with function context:

```python
logger.error("get_star_class_from_spansh[%s]: %s - %s", system_id, e, body)
```

Pattern for I/O operations:

```python
logger.warning("Failed to load %s: %s", path, e)
logger.debug("Saving data to %s", path)
```

## Logging in exception handlers

Every `except` block should log at the appropriate level:

```python
try:
    response.raise_for_status()
except Exception as e:
    logger.error("get_system_data[%s]: %s - %s", system_id, lookup_star_class, e)
    return

try:
    return json.loads(path.read_text())
except FileNotFoundError:
    return default
except Exception as e:
    logger.warning("Failed to load %s: %s", path, e)
    return default
```

Rules:
- **Silent fallbacks** (e.g., `FileNotFoundError` returning a default) may skip logging if the absence is expected.
- **Unexpected exceptions** (broad `except Exception`) must always be logged.
- Include the exception object `e` in the log message so the traceback or error message is captured.

## Logging in loops and batch operations

For loops that process many items:

- Log `debug` for per-item details (e.g., skipping an item, parsing attempt).
- Log `info` once for the overall operation start/completion with a count.
- Log `error` for per-item failures.

```python
logger.info("Processing %d bodies", len(bodies))
for body in bodies:
    try:
        result = process(body)
    except Exception as e:
        logger.error("Failed to process body %s: %s", body.body_id, e)
        continue
    logger.debug("Processed body %s: %s", body.body_id, result)
logger.info("Finished processing bodies")
```

## Logging in GUI components

GUI modules (in `EDXD/gui/`) follow the same rules:

- Log `info` for window creation, destruction, and major state changes.
- Log `debug` for event handling details.
- Log `error` for GUI failures (e.g., failed to render, failed to load resource).

```python
logger.info("Config loaded from %s", CFG_FILE)
logger.info("Log directory opened: %s", log_dir)
```

## Logging in data handlers and background threads

Background threads (e.g., `JournalReader`, `StatusWatcher`, `JournalController`) must log their lifecycle:

- `info` on thread start and stop
- `info` on significant events (new journal detected, file opened)
- `error` on parse failures or unexpected data
- `debug` on per-event processing

## What NOT to do

- **Do NOT use `print()`** for any diagnostic output — always use the logger.
- **Do NOT hard-code logger names** — always use `logging.getLogger(__name__)`.
- **Do NOT use f-strings in log calls** — use `%`-style lazy formatting.
- **Do NOT log secrets, tokens, or sensitive user data.**
- **Do NOT suppress exceptions silently** without logging them.
- **Do NOT log at `info` level in tight loops** — this will flood the log. Use `debug` for per-iteration messages.

## Quick reference — log level decision guide

| Situation | Level |
|---|---|
| Module initialized, file opened, config loaded | `info` |
| User action completed, state changed | `info` |
| API call succeeded with notable result | `info` |
| Variable value, loop iteration, cache check | `debug` |
| Parsing attempt, optional key missing | `debug` |
| File load failed but default returned | `warning` |
| Deprecated path taken | `warning` |
| Exception caught, operation failed | `error` |
| File save failed | `error` |
| API request failed | `error` |
| Data corruption detected | `error` |

## Verification checklist

After writing new code, verify:

1. [ ] The module has `logger = logging.getLogger(__name__)` at the top.
2. [ ] Every `except` block logs the exception (unless the absence is expected and documented).
3. [ ] All log messages use `%`-style lazy formatting, not f-strings.
4. [ ] Log messages include enough context (IDs, paths, function names) to diagnose issues.
5. [ ] No `print()` statements remain in the new code.
6. [ ] Log levels are appropriate — `debug` for detail, `info` for lifecycle, `warning` for recoverable issues, `error` for failures.
