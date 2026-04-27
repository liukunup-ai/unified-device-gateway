import pytest
from unittest.mock import Mock, patch, MagicMock
from w3c.webdriver import WebDriver, WebDriverClient, Alert, Capabilities


class TestWebDriverClient:
    def test_client_init_default(self):
        client = WebDriverClient()
        assert client.remote_url == "http://localhost:4444/wd/hub"
        assert client.session_id is None
    
    def test_client_init_custom_url(self):
        client = WebDriverClient(remote_url="http://192.168.1.100:4444/wd/hub")
        assert client.remote_url == "http://192.168.1.100:4444/wd/hub"
    
    def test_client_init_with_browser(self):
        caps = Capabilities(browserName="chrome")
        client = WebDriverClient(desired_capabilities=caps)
        assert client.capabilities["browserName"] == "chrome"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_new_session(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": {"sessionId": "abc123"}}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(remote_url="http://localhost:4444/wd/hub")
        session_id = client.new_session({"browserName": "chrome"})
        
        assert session_id == "abc123"
        assert client.session_id == "abc123"
        mock_request.assert_called_once()
    
    @patch("w3c.webdriver.client.requests.request")
    def test_status(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": {"ready": True}}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient()
        result = client.status()
        
        assert result["value"]["ready"] is True
    
    @patch("w3c.webdriver.client.requests.request")
    def test_get_current_url(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": "https://example.com"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        url = client.get_current_url()
        
        assert url == "https://example.com"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_get_title(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": "Example Page"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        title = client.get_title()
        
        assert title == "Example Page"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_find_element(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": {"element-6066-11e4-a52e-4eca3254111e": "elem-001"}}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        element_id = client.find_element("css selector", "#login")
        
        assert element_id == "elem-001"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_find_elements(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {
            "value": [
                {"element-6066-11e4-a52e-4eca3254111e": "elem-001"},
                {"element-6066-11e4-a52e-4eca3254111e": "elem-002"},
            ]
        }
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        elements = client.find_elements("css selector", ".item")
        
        assert len(elements) == 2
        assert elements[0] == "elem-001"
        assert elements[1] == "elem-002"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_get_element_attribute(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": "test-value"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        attr = client.get_element_attribute("elem-001", "data-id")
        
        assert attr == "test-value"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_element_click(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        result = client.element_click("elem-001")
        
        assert result["value"] is None
    
    @patch("w3c.webdriver.client.requests.request")
    def test_element_send_keys(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        result = client.element_send_keys("elem-001", "hello")
        
        assert result["value"] is None
        mock_request.assert_called_once()
    
    @patch("w3c.webdriver.client.requests.request")
    def test_get_window_handle(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": "window-abc123"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        handle = client.get_window_handle()
        
        assert handle == "window-abc123"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_get_window_handles(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": ["window-1", "window-2"]}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        handles = client.get_window_handles()
        
        assert handles == ["window-1", "window-2"]
    
    @patch("w3c.webdriver.client.requests.request")
    def test_get_all_cookies(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": [{"name": "session", "value": "abc"}]}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        cookies = client.get_all_cookies()
        
        assert len(cookies) == 1
        assert cookies[0]["name"] == "session"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_add_cookie(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        result = client.add_cookie("token", "xyz123", path="/")
        
        assert result["value"] is None
    
    @patch("w3c.webdriver.client.requests.request")
    def test_take_screenshot(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": "iVBORw0KGgo="}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        data = client.take_screenshot()
        
        assert data == "iVBORw0KGgo="
    
    @patch("w3c.webdriver.client.requests.request")
    def test_execute_script(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": "result"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        result = client.execute_script("return 'result'")
        
        assert result == "result"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_switch_to_window(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        result = client.switch_to_window("new-handle")
        
        assert result["value"] is None
    
    @patch("w3c.webdriver.client.requests.request")
    def test_switch_to_frame(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        result = client.switch_to_frame(0)
        
        assert result["value"] is None
    
    @patch("w3c.webdriver.client.requests.request")
    def test_get_alert_text(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": "Alert message"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        text = client.get_alert_text()
        
        assert text == "Alert message"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_accept_alert(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        result = client.accept_alert()
        
        assert result["value"] is None
    
    @patch("w3c.webdriver.client.requests.request")
    def test_delete_session(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        result = client.delete_session()
        
        assert result["value"] is None
        assert client.session_id is None


class TestWebDriver:
    def test_webdriver_init_default(self):
        driver = WebDriver()
        assert driver.remote_url == "http://localhost:4444/wd/hub"
    
    def test_webdriver_init_custom_url(self):
        driver = WebDriver(remote_url="http://appium:4723/wd/hub")
        assert driver.remote_url == "http://appium:4723/wd/hub"
    
    def test_webdriver_init_with_browser(self):
        driver = WebDriver(browser="safari")
        assert driver.client.capabilities["browserName"] == "safari"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_start_session(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": {"sessionId": "session-123"}}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        driver = WebDriver()
        session_id = driver.start_session()
        
        assert session_id == "session-123"
        assert driver.session_id == "session-123"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_get(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        driver = WebDriver()
        driver.client.session_id = "abc123"
        driver.get("https://example.com")
        
        mock_request.assert_called_once()
    
    @patch("w3c.webdriver.client.requests.request")
    def test_back(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        driver = WebDriver()
        driver.client.session_id = "abc123"
        driver.back()
        
        mock_request.assert_called_once()
    
    @patch("w3c.webdriver.client.requests.request")
    def test_forward(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        driver = WebDriver()
        driver.client.session_id = "abc123"
        driver.forward()
        
        mock_request.assert_called_once()
    
    @patch("w3c.webdriver.client.requests.request")
    def test_refresh(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        driver = WebDriver()
        driver.client.session_id = "abc123"
        driver.refresh()
        
        mock_request.assert_called_once()
    
    @patch("w3c.webdriver.client.requests.request")
    def test_find_element_by_css(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": {"element-6066-11e4-a52e-4eca3254111e": "elem-001"}}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        driver = WebDriver()
        driver.client.session_id = "abc123"
        element = driver.find_element_by_css("#login")
        
        assert element == "elem-001"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_find_element_by_xpath(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": {"element-6066-11e4-a52e-4eca3254111e": "elem-002"}}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        driver = WebDriver()
        driver.client.session_id = "abc123"
        element = driver.find_element_by_xpath("//button[@id='btn']")
        
        assert element == "elem-002"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_find_element_by_id(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": {"element-6066-11e4-a52e-4eca3254111e": "elem-003"}}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        driver = WebDriver()
        driver.client.session_id = "abc123"
        element = driver.find_element_by_id("submit-btn")
        
        assert element == "elem-003"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_screenshot(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": "base64data"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        driver = WebDriver()
        driver.client.session_id = "abc123"
        data = driver.screenshot()
        
        assert data == "base64data"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_quit(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        driver = WebDriver()
        driver.client.session_id = "abc123"
        driver.quit()
        
        assert driver.session_id is None
    
    @patch("w3c.webdriver.client.requests.request")
    def test_context_manager(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": {"sessionId": "session-456"}}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        with WebDriver() as driver:
            assert driver.session_id == "session-456"
        
        mock_request.assert_called()


class TestAlert:
    @patch("w3c.webdriver.client.requests.request")
    def test_alert_text(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": "Alert!"}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        alert = Alert(client)
        
        assert alert.text == "Alert!"
    
    @patch("w3c.webdriver.client.requests.request")
    def test_alert_accept(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        alert = Alert(client)
        alert.accept()
        
        mock_request.assert_called_once()
    
    @patch("w3c.webdriver.client.requests.request")
    def test_alert_dismiss(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        alert = Alert(client)
        alert.dismiss()
        
        mock_request.assert_called_once()
    
    @patch("w3c.webdriver.client.requests.request")
    def test_alert_send_keys(self, mock_request):
        mock_response = Mock()
        mock_response.json.return_value = {"value": None}
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        client = WebDriverClient(session_id="abc123")
        alert = Alert(client)
        alert.send_keys("password")
        
        mock_request.assert_called_once()


class TestCapabilities:
    def test_capabilities_defaults(self):
        caps = Capabilities()
        assert caps.browserName is None
        assert caps.acceptInsecureCerts is False
        assert caps.setWindowRect is True
    
    def test_capabilities_mobile(self):
        caps = Capabilities(
            browserName="Safari",
            automationName="XCUITest",
            deviceName="iPhone 15",
            platformVersion="17.0",
        )
        assert caps.browserName == "Safari"
        assert caps.automationName == "XCUITest"
        assert caps.deviceName == "iPhone 15"
    
    def test_capabilities_android(self):
        caps = Capabilities(
            browserName="Chrome",
            automationName="uiautomator2",
            deviceName="Android Emulator",
            platformVersion="14.0",
        )
        assert caps.browserName == "Chrome"
        assert caps.automationName == "uiautomator2"


class TestTimeouts:
    def test_timeouts_defaults(self):
        from w3c.webdriver.types import Timeouts
        to = Timeouts()
        assert to.script is None
        assert to.pageLoad is None
        assert to.implicit is None
    
    def test_timeouts_with_values(self):
        from w3c.webdriver.types import Timeouts
        to = Timeouts(script=5000, pageLoad=30000, implicit=10000)
        assert to.script == 5000
        assert to.pageLoad == 30000
        assert to.implicit == 10000