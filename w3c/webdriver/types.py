from typing import Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class LocateStrategy(str, Enum):
    CSS_SELECTOR = "css selector"
    LINK_TEXT = "link text"
    PARTIAL_LINK_TEXT = "partial link text"
    TAG_NAME = "tag name"
    XPATH = "xpath"


class InputSourceType(str, Enum):
    NONE = "none"
    KEY = "key"
    POINTER = "pointer"
    WHEEL = "wheel"


class PointerType(str, Enum):
    MOUSE = "mouse"
    TOUCH = "touch"
    PEN = "pen"


class TimeoutType(str, Enum):
    SCRIPT = "script"
    PAGE_LOAD = "pageLoad"
    IMPLICIT = "implicit"


class FrameReference(BaseModel):
    id: Optional[int | str] = None


class WindowRect(BaseModel):
    x: int
    y: int
    width: int
    height: int


class Cookie(BaseModel):
    name: str
    value: str
    path: Optional[str] = None
    domain: Optional[str] = None
    secure: Optional[bool] = None
    httpOnly: Optional[bool] = None
    expiry: Optional[int] = None
    sameSite: Optional[str] = None


class CookieWithDomain(BaseModel):
    name: str
    value: str
    domain: str
    path: Optional[str] = None
    secure: Optional[bool] = None
    httpOnly: Optional[bool] = None
    expiry: Optional[int] = None
    sameSite: Optional[str] = None


class Timeouts(BaseModel):
    script: Optional[int] = None
    pageLoad: Optional[int] = None
    implicit: Optional[int] = None


class Capabilities(BaseModel):
    browserName: Optional[str] = None
    browserVersion: Optional[str] = None
    platformName: Optional[str] = None
    acceptInsecureCerts: Optional[bool] = False
    pageLoadStrategy: Optional[str] = "normal"
    proxy: Optional[dict[str, Any]] = None
    setWindowRect: Optional[bool] = True
    strictFileInteractability: Optional[bool] = False
    unhandledPromptBehavior: Optional[str] = "dismiss and notify"
    automationName: Optional[str] = None
    platformVersion: Optional[str] = None
    deviceName: Optional[str] = None
    app: Optional[str] = None
    bundleId: Optional[str] = None
    udg_device_id: Optional[str] = None


class Element(BaseModel):
    class Config:
        populate_by_name = True
    
    element_6066_11e4_a52e_4eca3254111e: Optional[str] = Field(None, alias="element-6066-11e4-a52e-4eca3254111e")
    
    @property
    def element_id(self) -> str:
        return self.element_6066_11e4_a52e_4eca3254111e or ""


class ElementLocation(BaseModel):
    x: float
    y: float


class ElementRect(BaseModel):
    x: float
    y: float
    width: float
    height: float


class ActionItem(BaseModel):
    type: str
    value: Optional[list[str] | list[float] | str | int | float] = None
    duration: Optional[int] = None
    origin: Optional[str | dict[str, str]] = None
    x: Optional[float] = None
    y: Optional[float] = None
    deltaX: Optional[float] = None
    deltaY: Optional[float] = None
    deltaZ: Optional[float] = None
    wheelDeltaX: Optional[int] = None
    wheelDeltaY: Optional[int] = None


class Actions(BaseModel):
    actions: list[dict[str, Any]] = Field(default_factory=list)


class MouseButton(str, Enum):
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2


class PrintOptions(BaseModel):
    orientation: Optional[str] = "portrait"
    scale: Optional[float] = 1.0
    background: Optional[bool] = False
    pageWidth: Optional[float] = 8.5
    pageHeight: Optional[float] = 11.0
    marginTop: Optional[float] = 1.0
    marginBottom: Optional[float] = 1.0
    marginLeft: Optional[float] = 1.0
    marginRight: Optional[float] = 1.0
    pageRanges: Optional[list[str]] = Field(default_factory=list)


class WindowTypes(str, Enum):
    WINDOW = "window"
    TAB = "tab"
    FRAME = "frame"


class GetElementShadowRootResponse(BaseModel):
    class Config:
        populate_by_name = True
    
    shadow_6066_11e4_a52e_4eca3254111e: Optional[str] = Field(None, alias="shadow-6066-11e4-a52e-4eca3254111e")
    
    @property
    def shadow_root_id(self) -> str:
        return self.shadow_6066_11e4_a52e_4eca3254111e or ""


class NewWindowResponse(BaseModel):
    handle: str
    type: str


class RectDelta(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class AlertResponse(BaseModel):
    value: Optional[str] = None


class ExecuteScriptResponse(BaseModel):
    pass