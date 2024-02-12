"""Asynchronous Python client for FYTA."""


class HomeassistantFytaError(Exception):
    """Generic exception."""


class HomeassistantFytaConnectionError(HomeassistantFytaError):
    """Homeassistant Analytics connection exception."""

class HomeassistantFytaAuthentificationError(HomeassistantFytaError):
    """Homeassistant Fyta Password exception (wrong password)."""

class HomeassistantFytaPasswordError(HomeassistantFytaError):
    """Homeassistant Fyta Password exception (wrong password)."""

class HomeassistantFytaPlantError(HomeassistantFytaError):
    """Homeassistant Fyta exception in getting plants."""
