"""W3C WebDriver error codes."""


class WebDriverException(Exception):
    """Base WebDriver exception."""
    
    def __init__(self, message: str, error_code: str = "unknown error"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class UnknownCommandError(WebDriverException):
    def __init__(self, message: str = "Unknown command"):
        super().__init__(message, "unknown command")


class UnknownMethodError(WebDriverException):
    def __init__(self, message: str = "Unknown method"):
        super().__init__(message, "unknown method")


class InvalidSessionIdError(WebDriverException):
    def __init__(self, message: str = "Invalid session ID"):
        super().__init__(message, "invalid session id")


class NoSuchWindowError(WebDriverException):
    def __init__(self, message: str = "No such window"):
        super().__init__(message, "no such window")


class NoSuchFrameError(WebDriverException):
    def __init__(self, message: str = "No such frame"):
        super().__init__(message, "no such frame")


class NoSuchElementError(WebDriverException):
    def __init__(self, message: str = "No such element"):
        super().__init__(message, "no such element")


class NoSuchShadowRootError(WebDriverException):
    def __init__(self, message: str = "No such shadow root"):
        super().__init__(message, "no such shadow root")


class StaleElementReferenceError(WebDriverException):
    def __init__(self, message: str = "Stale element reference"):
        super().__init__(message, "stale element reference")


class ElementNotInteractableError(WebDriverException):
    def __init__(self, message: str = "Element not interactable"):
        super().__init__(message, "element not interactable")


class ElementClickInterceptedError(WebDriverException):
    def __init__(self, message: str = "Element click intercepted"):
        super().__init__(message, "element click intercepted")


class ElementNotSelectableError(WebDriverException):
    def __init__(self, message: str = "Element not selectable"):
        super().__init__(message, "element not selectable")


class ElementIsDisabledError(WebDriverException):
    def __init__(self, message: str = "Element is disabled"):
        super().__init__(message, "element is disabled")


class InvalidArgumentError(WebDriverException):
    def __init__(self, message: str = "Invalid argument"):
        super().__init__(message, "invalid argument")


class JavaScriptError(WebDriverException):
    def __init__(self, message: str = "JavaScript error"):
        super().__init__(message, "javascript error")


class MoveTargetOutOfBoundsError(WebDriverException):
    def __init__(self, message: str = "Move target out of bounds"):
        super().__init__(message, "move target out of bounds")


class NoSuchAlertError(WebDriverException):
    def __init__(self, message: str = "No such alert"):
        super().__init__(message, "no such alert")


class NoSuchCookieError(WebDriverException):
    def __init__(self, message: str = "No such cookie"):
        super().__init__(message, "no such cookie")


class InvalidCookieDomainError(WebDriverException):
    def __init__(self, message: str = "Invalid cookie domain"):
        super().__init__(message, "invalid cookie domain")


class UnableToSetCookieError(WebDriverException):
    def __init__(self, message: str = "Unable to set cookie"):
        super().__init__(message, "unable to set cookie")


class UnableToCaptureScreenError(WebDriverException):
    def __init__(self, message: str = "Unable to capture screen"):
        super().__init__(message, "unable to capture screen")


class UnexpectedAlertOpenError(WebDriverException):
    def __init__(self, message: str = "Unexpected alert open"):
        super().__init__(message, "unexpected alert open")


class NoAlertOpenError(WebDriverException):
    def __init__(self, message: str = "No alert open"):
        super().__init__(message, "no alert open")


class NoSuchDocumentError(WebDriverException):
    def __init__(self, message: str = "No such document"):
        super().__init__(message, "no such document")


class InvalidCoordinatesError(WebDriverException):
    def __init__(self, message: str = "Invalid coordinates"):
        super().__init__(message, "invalid coordinates")


class InvalidElementStateError(WebDriverException):
    def __init__(self, message: str = "Invalid element state"):
        super().__init__(message, "invalid element state")


class DetachedShadowRootError(WebDriverException):
    def __init__(self, message: str = "Detached shadow root"):
        super().__init__(message, "detached shadow root")


class TimeoutError(WebDriverException):
    def __init__(self, message: str = "Timeout"):
        super().__init__(message, "timeout")


ERROR_CODE_MAP = {
    "unknown command": UnknownCommandError,
    "unknown method": UnknownMethodError,
    "invalid session id": InvalidSessionIdError,
    "no such window": NoSuchWindowError,
    "no such frame": NoSuchFrameError,
    "no such element": NoSuchElementError,
    "no such shadow root": NoSuchShadowRootError,
    "stale element reference": StaleElementReferenceError,
    "element not interactable": ElementNotInteractableError,
    "element click intercepted": ElementClickInterceptedError,
    "element not selectable": ElementNotSelectableError,
    "element is disabled": ElementIsDisabledError,
    "invalid argument": InvalidArgumentError,
    "javascript error": JavaScriptError,
    "move target out of bounds": MoveTargetOutOfBoundsError,
    "no such alert": NoSuchAlertError,
    "no such cookie": NoSuchCookieError,
    "invalid cookie domain": InvalidCookieDomainError,
    "unable to set cookie": UnableToSetCookieError,
    "unable to capture screen": UnableToCaptureScreenError,
    "unexpected alert open": UnexpectedAlertOpenError,
    "no alert open": NoAlertOpenError,
    "no such document": NoSuchDocumentError,
    "invalid coordinates": InvalidCoordinatesError,
    "invalid element state": InvalidElementStateError,
    "detached shadow root": DetachedShadowRootError,
    "timeout": TimeoutError,
}


def get_error_class(error_code: str):
    """Get the appropriate exception class for an error code."""
    return ERROR_CODE_MAP.get(error_code, WebDriverException)


def raise_if_error(response: dict):
    """Raise an exception if the response contains an error."""
    value = response.get("value")
    if value is None:
        return
    
    if isinstance(value, dict):
        error = value.get("error")
        message = value.get("message", "Unknown error")
        if error:
            error_class = get_error_class(error)
            raise error_class(message)