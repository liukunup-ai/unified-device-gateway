# WebDriver Client Design

**Date**: 2026-04-27

## Overview

Implement a W3C WebDriver client library for unified control of Android (Chrome) and iOS (Safari) browsers via Appium/Selenium WebDriver servers.

## Requirements

1. **Device scope**: Both Android (Chrome) and iOS (Safari)
2. **Implementation**: WebDriver client library (not server)
3. **Endpoints**: All W3C WebDriver endpoints (~70)

## Architecture

```
udg/webdriver/
├── __init__.py           # Public API: WebDriver class
├── client.py            # HTTP client, request/response handling
├── session.py          # Session management
├── errors.py           # W3C error codes
├── types.py            # Capabilities, Timeouts, etc.
└── commands/          # Command implementations by category
    ├── __init__.py
    ├── session.py      # New/Delete Session, Status
    ├── navigation.py  # Navigate, Back, Forward, Refresh, Get URL/Title
    ├── window.py      # Window handle, frames, rect, fullscreen
    ├── elements.py    # Find elements, click, send keys, etc.
    ├── cookies.py     # Cookie CRUD
    ├── actions.py    # Actions API (key, pointer, wheel)
    ├── alert.py      # Alert handling
    ├── script.py     # Execute script (sync/async)
    └── screenshot.py # Take screenshot
```

## Key Design Decisions

| Aspect | Decision |
|--------|----------|
| Server URL | Configurable, default `http://localhost:4444/wd/hub` |
| Protocol | W3C WebDriver JSON wire protocol |
| Session | Per-browser via Appium/Selenium |
| Error handling | W3C error codes |

## Public API

```python
from udg.webdriver import WebDriver

driver = WebDriver("http://localhost:4444/wd/hub")
driver.get("https://example.com")
element = driver.find_element("css selector", "#login")
element.click()
driver.quit()
```

## Implementation Phases

1. **Phase 1**: Core client + session (~10 endpoints)
2. **Phase 2**: Navigation + window (~15 endpoints)
3. **Phase 3**: Element operations (~25 endpoints)
4. **Phase 4**: Advanced (actions, cookies, script, screenshot)

Total: ~70 W3C endpoints.

## Compatibility

- Android: Chrome via Appium uiautomator2
- iOS: Safari via Appium XCUITest