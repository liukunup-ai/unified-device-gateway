from typing import Any, Optional, Dict
import requests
from w3c.webdriver.errors import raise_if_error, WebDriverException, get_error_class
from w3c.webdriver.types import Capabilities, Timeouts


class WebDriverClient:
    """HTTP client for WebDriver wire protocol."""
    
    def __init__(
        self,
        remote_url: str = "http://localhost:4444/wd/hub",
        desired_capabilities: Optional[Capabilities] = None,
        required_capabilities: Optional[Capabilities] = None,
        session_id: Optional[str] = None,
        timeout: int = 30,
    ):
        self.remote_url = remote_url.rstrip("/")
        self.session_id = session_id
        self.timeout = timeout
        
        caps = desired_capabilities or Capabilities()
        self.capabilities = caps.model_dump(exclude_none=True)
        if required_capabilities:
            self.required_capabilities = required_capabilities.model_dump(exclude_none=True)
        else:
            self.required_capabilities = {}
    
    def _request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        session_specific: bool = True,
    ) -> dict:
        if session_specific and self.session_id:
            path = path.replace("{session id}", self.session_id)
        
        url = f"{self.remote_url}{path}"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if data:
            response = requests.request(
                method,
                url,
                json=data,
                headers=headers,
                timeout=self.timeout,
            )
        else:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=self.timeout,
            )
        
        try:
            result = response.json()
        except ValueError:
            result = {"value": {"error": "unknown error", "message": response.text}}
        
        if response.status_code >= 400:
            raise_if_error(result)
            status = response.status_code
            message = result.get("value", {}).get("message", "Unknown error") if isinstance(result, dict) else "Unknown error"
            error_code = result.get("value", {}).get("error", "unknown error") if isinstance(result, dict) else "unknown error"
            error_class = get_error_class(error_code)
            raise error_class(message)
        
        return result
    
    def get(self, path: str, session_specific: bool = True) -> dict:
        return self._request("GET", path, session_specific=session_specific)
    
    def post(self, path: str, data: Optional[dict] = None, session_specific: bool = True) -> dict:
        return self._request("POST", path, data=data, session_specific=session_specific)
    
    def delete(self, path: str, session_specific: bool = True) -> dict:
        return self._request("DELETE", path, session_specific=session_specific)
    
    def new_session(self, capabilities: Optional[dict] = None) -> str:
        """Create a new WebDriver session."""
        merged_caps = self.capabilities.copy()
        if capabilities:
            merged_caps.update(capabilities)
        
        response = self.post("/session", data={"capabilities": merged_caps}, session_specific=False)
        value = response.get("value", {})
        self.session_id = value.get("sessionId")
        return self.session_id
    
    def status(self) -> dict:
        """Get WebDriver server status."""
        return self.get("/status", session_specific=False)
    
    def delete_session(self) -> dict:
        """Delete the current session."""
        if not self.session_id:
            return {}
        result = self.delete("/session/{session id}")
        self.session_id = None
        return result
    
    def get_timeouts(self) -> Timeouts:
        """Get current timeouts."""
        response = self.get("/timeouts")
        value = response.get("value", {})
        return Timeouts(**value)
    
    def set_timeouts(self, timeouts: Timeouts) -> dict:
        """Set timeouts."""
        return self.post("/timeouts", data=timeouts.model_dump(exclude_none=True))
    
    def get_current_url(self) -> str:
        """Get current URL."""
        response = self.get("/url")
        return response.get("value", "")
    
    def get_title(self) -> str:
        """Get page title."""
        response = self.get("/title")
        return response.get("value", "")
    
    def get_page_source(self) -> str:
        """Get page source."""
        response = self.get("/source")
        return response.get("value", "")
    
    def get_window_handle(self) -> str:
        """Get current window handle."""
        response = self.get("/window")
        return response.get("value", "")
    
    def close_window(self) -> dict:
        """Close current window."""
        return self.delete("/window")
    
    def get_window_handles(self) -> list[str]:
        """Get all window handles."""
        response = self.get("/window/handles")
        return response.get("value", [])
    
    def get_window_rect(self) -> dict:
        """Get window rect."""
        response = self.get("/window/rect")
        return response.get("value", {})
    
    def set_window_rect(self, x: Optional[int] = None, y: Optional[int] = None, width: Optional[int] = None, height: Optional[int] = None) -> dict:
        """Set window rect."""
        data = {}
        if x is not None:
            data["x"] = x
        if y is not None:
            data["y"] = y
        if width is not None:
            data["width"] = width
        if height is not None:
            data["height"] = height
        return self.post("/window/rect", data=data)
    
    def maximize_window(self, handle: Optional[str] = None) -> dict:
        """Maximize window."""
        data = {"name": "window"} if handle else {}
        return self.post("/window/maximize", data=data)
    
    def minimize_window(self) -> dict:
        """Minimize window."""
        return self.post("/window/minimize")
    
    def fullscreen_window(self) -> dict:
        """Fullscreen window."""
        return self.post("/window/fullscreen")
    
    def get_active_element(self) -> str:
        """Get active element."""
        response = self.get("/element/active")
        value = response.get("value", {})
        return value.get("element-6066-11e4-a52e-4eca3254111e", "")
    
    def find_element(self, strategy: str, selector: str) -> str:
        """Find single element."""
        response = self.post(
            "/element",
            data={"using": strategy, "value": selector},
        )
        value = response.get("value", {})
        return value.get("element-6066-11e4-a52e-4eca3254111e", "")
    
    def find_elements(self, strategy: str, selector: str) -> list[str]:
        """Find multiple elements."""
        response = self.post(
            "/elements",
            data={"using": strategy, "value": selector},
        )
        value = response.get("value", [])
        return [e.get("element-6066-11e4-a52e-4eca3254111e", "") for e in value]
    
    def find_element_from(self, element_id: str, strategy: str, selector: str) -> str:
        """Find element from element."""
        path = f"/element/{element_id}/element"
        response = self.post(
            path,
            data={"using": strategy, "value": selector},
        )
        value = response.get("value", {})
        return value.get("element-6066-11e4-a52e-4eca3254111e", "")
    
    def find_elements_from(self, element_id: str, strategy: str, selector: str) -> list[str]:
        """Find elements from element."""
        path = f"/element/{element_id}/elements"
        response = self.post(
            path,
            data={"using": strategy, "value": selector},
        )
        value = response.get("value", [])
        return [e.get("element-6066-11e4-a52e-4eca3254111e", "") for e in value]
    
    def find_element_from_shadow_root(self, shadow_id: str, strategy: str, selector: str) -> str:
        """Find element from shadow root."""
        path = f"/shadow/{shadow_id}/element"
        response = self.post(
            path,
            data={"using": strategy, "value": selector},
        )
        value = response.get("value", {})
        return value.get("element-6066-11e4-a52e-4eca3254111e", "")
    
    def find_elements_from_shadow_root(self, shadow_id: str, strategy: str, selector: str) -> list[str]:
        """Find elements from shadow root."""
        path = f"/shadow/{shadow_id}/elements"
        response = self.post(
            path,
            data={"using": strategy, "value": selector},
        )
        value = response.get("value", [])
        return [e.get("element-6066-11e4-a52e-4eca3254111e", "") for e in value]
    
    def get_element_attribute(self, element_id: str, name: str) -> Optional[str]:
        """Get element attribute."""
        path = f"/element/{element_id}/attribute/{name}"
        response = self.get(path)
        return response.get("value")
    
    def get_element_property(self, element_id: str, name: str) -> Optional[str]:
        """Get element property."""
        path = f"/element/{element_id}/property/{name}"
        response = self.get(path)
        return response.get("value")
    
    def get_element_css_value(self, element_id: str, property_name: str) -> str:
        """Get element CSS value."""
        path = f"/element/{element_id}/css/{property_name}"
        response = self.get(path)
        return response.get("value", "")
    
    def get_element_text(self, element_id: str) -> str:
        """Get element text."""
        path = f"/element/{element_id}/text"
        response = self.get(path)
        return response.get("value", "")
    
    def get_element_tag_name(self, element_id: str) -> str:
        """Get element tag name."""
        path = f"/element/{element_id}/name"
        response = self.get(path)
        return response.get("value", "")
    
    def get_element_rect(self, element_id: str) -> dict:
        """Get element rect."""
        path = f"/element/{element_id}/rect"
        response = self.get(path)
        return response.get("value", {})
    
    def is_element_selected(self, element_id: str) -> bool:
        """Check if element is selected."""
        path = f"/element/{element_id}/selected"
        response = self.get(path)
        return response.get("value", False)
    
    def is_element_enabled(self, element_id: str) -> bool:
        """Check if element is enabled."""
        path = f"/element/{element_id}/enabled"
        response = self.get(path)
        return response.get("value", False)
    
    def get_element_shadow_root(self, element_id: str) -> str:
        """Get element shadow root."""
        path = f"/element/{element_id}/shadow"
        response = self.get(path)
        value = response.get("value", {})
        return value.get("shadow-6066-11e4-a52e-4eca3254111e", "")
    
    def get_computed_role(self, element_id: str) -> str:
        """Get computed role."""
        path = f"/element/{element_id}/computedrole"
        response = self.get(path)
        return response.get("value", "")
    
    def get_computed_label(self, element_id: str) -> str:
        """Get computed label."""
        path = f"/element/{element_id}/computedlabel"
        response = self.get(path)
        return response.get("value", "")
    
    def element_click(self, element_id: str) -> dict:
        """Click element."""
        path = f"/element/{element_id}/click"
        return self.post(path)
    
    def element_clear(self, element_id: str) -> dict:
        """Clear element input."""
        path = f"/element/{element_id}/clear"
        return self.post(path)
    
    def element_send_keys(self, element_id: str, text: str) -> dict:
        """Send keys to element."""
        path = f"/element/{element_id}/value"
        return self.post(path, data={"text": text})
    
    def switch_to_window(self, handle: str) -> dict:
        """Switch to window."""
        return self.post("/window", data={"name": handle})
    
    def switch_to_frame(self, id: Optional[int | str] = None) -> dict:
        """Switch to frame."""
        return self.post("/frame", data={"id": id} if id is not None else {})
    
    def switch_to_parent_frame(self) -> dict:
        """Switch to parent frame."""
        return self.post("/frame/parent")
    
    def new_window(self, type: str = "tab") -> dict:
        """Create new window."""
        response = self.post("/window/new", data={"type": type})
        return response.get("value", {})
    
    def get_all_cookies(self) -> list[dict]:
        """Get all cookies."""
        response = self.get("/cookie")
        return response.get("value", [])
    
    def get_named_cookie(self, name: str) -> dict:
        """Get named cookie."""
        path = f"/cookie/{name}"
        response = self.get(path)
        return response.get("value", {})
    
    def add_cookie(self, name: str, value: str, path: Optional[str] = None, domain: Optional[str] = None, secure: Optional[bool] = None, http_only: Optional[bool] = None, expiry: Optional[int] = None, same_site: Optional[str] = None) -> dict:
        """Add cookie."""
        data = {"name": name, "value": value}
        if path:
            data["path"] = path
        if domain:
            data["domain"] = domain
        if secure is not None:
            data["secure"] = secure
        if http_only is not None:
            data["httpOnly"] = http_only
        if expiry:
            data["expiry"] = expiry
        if same_site:
            data["sameSite"] = same_site
        return self.post("/cookie", data=data)
    
    def delete_cookie(self, name: str) -> dict:
        """Delete cookie."""
        path = f"/cookie/{name}"
        return self.delete(path)
    
    def delete_all_cookies(self) -> dict:
        """Delete all cookies."""
        return self.delete("/cookie")
    
    def perform_actions(self, actions: list[dict]) -> dict:
        """Perform actions."""
        return self.post("/actions", data={"actions": actions})
    
    def release_actions(self) -> dict:
        """Release all actions."""
        return self.delete("/actions")
    
    def dismiss_alert(self) -> dict:
        """Dismiss alert."""
        return self.post("/alert/dismiss")
    
    def accept_alert(self) -> dict:
        """Accept alert."""
        return self.post("/alert/accept")
    
    def get_alert_text(self) -> str:
        """Get alert text."""
        response = self.get("/alert/text")
        return response.get("value", "")
    
    def send_alert_text(self, text: str) -> dict:
        """Send text to alert."""
        return self.post("/alert/text", data={"text": text})
    
    def take_screenshot(self) -> str:
        """Take full page screenshot."""
        response = self.get("/screenshot")
        return response.get("value", "")
    
    def take_element_screenshot(self, element_id: str) -> str:
        """Take element screenshot."""
        path = f"/element/{element_id}/screenshot"
        response = self.get(path)
        return response.get("value", "")
    
    def execute_script(self, script: str, *args: Any) -> Any:
        """Execute synchronous script."""
        response = self.post("/execute/sync", data={"script": script, "args": list(args)})
        return response.get("value")
    
    def execute_async_script(self, script: str, *args: Any) -> Any:
        """Execute asynchronous script."""
        response = self.post("/execute/async", data={"script": script, "args": list(args)})
        return response.get("value")
    
    def print_page(self, orientation: str = "portrait", scale: float = 1.0, background: bool = False, margin: float = 1.0, page_ranges: Optional[list[str]] = None) -> str:
        """Print page as PDF."""
        data = {
            "orientation": orientation,
            "scale": scale,
            "background": background,
            "margin": {"top": margin, "bottom": margin, "left": margin, "right": margin},
        }
        if page_ranges:
            data["pageRanges"] = page_ranges
        response = self.post("/print", data=data)
        return response.get("value", "")


class WebDriver:
    """High-level WebDriver client with convenient methods."""
    
    def __init__(
        self,
        remote_url: str = "http://localhost:4444/wd/hub",
        desired_capabilities: Optional[Capabilities] = None,
        browser: Optional[str] = None,
    ):
        self.remote_url = remote_url
        self.client = WebDriverClient(
            remote_url=remote_url,
            session_id=None,
        )
        
        if browser:
            caps = desired_capabilities or Capabilities()
            caps.browserName = browser
            self.client.capabilities = caps.model_dump(exclude_none=True)
    
    def start_session(self, capabilities: Optional[Capabilities] = None) -> str:
        """Start a new session."""
        caps = capabilities or Capabilities()
        merged = self.client.capabilities.copy()
        if capabilities:
            merged.update(capabilities.model_dump(exclude_none=True))
        
        return self.client.new_session(merged)
    
    @property
    def session_id(self) -> Optional[str]:
        return self.client.session_id
    
    def get(self, url: str) -> None:
        """Navigate to URL."""
        self.client.post("/url", data={"url": url})
    
    def back(self) -> None:
        """Go back in history."""
        self.client.post("/back")
    
    def forward(self) -> None:
        """Go forward in history."""
        self.client.post("/forward")
    
    def refresh(self) -> None:
        """Refresh page."""
        self.client.post("/refresh")
    
    @property
    def current_url(self) -> str:
        return self.client.get_current_url()
    
    @property
    def title(self) -> str:
        return self.client.get_title()
    
    @property
    def page_source(self) -> str:
        return self.client.get_page_source()
    
    @property
    def window_handle(self) -> str:
        return self.client.get_window_handle()
    
    @property
    def window_handles(self) -> list[str]:
        return self.client.get_window_handles()
    
    def find_element(self, strategy: str, selector: str) -> str:
        """Find element by strategy and selector."""
        return self.client.find_element(strategy, selector)
    
    def find_elements(self, strategy: str, selector: str) -> list[str]:
        """Find elements by strategy and selector."""
        return self.client.find_elements(strategy, selector)
    
    def find_element_by_css(self, selector: str) -> str:
        """Find element by CSS selector."""
        return self.client.find_element("css selector", selector)
    
    def find_elements_by_css(self, selector: str) -> list[str]:
        """Find elements by CSS selector."""
        return self.client.find_elements("css selector", selector)
    
    def find_element_by_id(self, id: str) -> str:
        """Find element by ID."""
        return self.client.find_element("css selector", f"#{id}")
    
    def find_element_by_xpath(self, xpath: str) -> str:
        """Find element by XPath."""
        return self.client.find_element("xpath", xpath)
    
    def find_element_by_tag(self, tag: str) -> str:
        """Find element by tag name."""
        return self.client.find_element("tag name", tag)
    
    def find_element_by_link_text(self, text: str) -> str:
        """Find element by link text."""
        return self.client.find_element("link text", text)
    
    def find_element_by_partial_link_text(self, text: str) -> str:
        """Find element by partial link text."""
        return self.client.find_element("partial link text", text)
    
    def switch_to_window(self, handle: str) -> None:
        """Switch to window."""
        self.client.switch_to_window(handle)
    
    def switch_to_frame(self, index: Optional[int | str] = None) -> None:
        """Switch to frame."""
        self.client.switch_to_frame(index)
    
    def switch_to_default_content(self) -> None:
        """Switch to default content."""
        self.client.switch_to_frame(None)
    
    def switch_to_alert(self) -> "Alert":
        return Alert(self.client)
    
    def maximize(self) -> None:
        """Maximize window."""
        self.client.maximize_window()
    
    def minimize(self) -> None:
        """Minimize window."""
        self.client.minimize_window()
    
    def fullscreen(self) -> None:
        """Fullscreen window."""
        self.client.fullscreen_window()
    
    def set_window_size(self, width: int, height: int) -> None:
        """Set window size."""
        self.client.set_window_rect(width=width, height=height)
    
    def set_window_position(self, x: int, y: int) -> None:
        """Set window position."""
        self.client.set_window_rect(x=x, y=y)
    
    def get_window_rect(self) -> dict:
        """Get window rect."""
        return self.client.get_window_rect()
    
    def get_cookies(self) -> list[dict]:
        """Get all cookies."""
        return self.client.get_all_cookies()
    
    def add_cookie(self, name: str, value: str, **kwargs) -> None:
        """Add cookie."""
        self.client.add_cookie(name, value, **kwargs)
    
    def delete_cookie(self, name: str) -> None:
        """Delete cookie."""
        self.client.delete_cookie(name)
    
    def delete_all_cookies(self) -> None:
        """Delete all cookies."""
        self.client.delete_all_cookies()
    
    def execute_script(self, script: str, *args: Any) -> Any:
        """Execute script."""
        return self.client.execute_script(script, *args)
    
    def execute_async_script(self, script: str, *args: Any) -> Any:
        """Execute async script."""
        return self.client.execute_async_script(script, *args)
    
    def screenshot(self) -> str:
        """Take screenshot."""
        return self.client.take_screenshot()
    
    def save_screenshot(self, filename: str) -> None:
        """Save screenshot to file."""
        import base64
        data = self.screenshot()
        if data:
            with open(filename, "wb") as f:
                f.write(base64.b64decode(data))
    
    def quit(self) -> None:
        """Quit session."""
        self.client.delete_session()
        self.client.session_id = None
    
    def close(self) -> None:
        """Close current window."""
        self.client.close_window()
    
    def __enter__(self):
        self.start_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()
        return False


class Alert:
    def __init__(self, client: WebDriverClient):
        self._client = client
    
    @property
    def text(self) -> str:
        return self._client.get_alert_text()
    
    def accept(self) -> None:
        self._client.accept_alert()
    
    def dismiss(self) -> None:
        self._client.dismiss_alert()
    
    def send_keys(self, text: str) -> None:
        self._client.send_alert_text(text)