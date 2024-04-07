"""Utility functions for the FYTA integration."""
from datetime import datetime
from zoneinfo import ZoneInfo

def safe_get(plant_data: dict, key_path: str, expected_type, tz: ZoneInfo | None = None):
    """Get a value from a nested dictionary and cast it to the expected type.

    Args:
        plant_data: The dictionary to get the value from.
        key_path: The path to the value in the dictionary. Seüarated by dots.
        expected_type: The expected type of the value (int, float, bool and str supported).
        tz: Timezone needed to localize datetime (only required, if expected_type is datetime). 

    Returns: The value from the dictionary or None if the value is not found or the type is not
    as expected.
    """
    keys = key_path.split(".")
    value = plant_data
    try:
        for key in keys:
            value = value.get(key)
            if value is None:
                return None
    except AttributeError:
        return None
    return_value = None
    if expected_type == int:
        return_value = __get_int(value)
    if expected_type == float:
        return_value =  __get_float(value)
    if expected_type == bool:
        return_value = __get_bool(value)
    if expected_type == str:
        return_value = str(value)
    if expected_type == datetime:
        return_value = __get_datetime(value, tz)

    if "status" in keys and (return_value < 1 or return_value > 5):
        #FYTA status has a scale from 1 to 5; return None, if no correct status is set
        return_value = None

    return return_value


def __get_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
    return None


def __get_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def __get_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def __get_datetime(value: str, tz: str):
    try:
        return datetime.fromisoformat(value).astimezone(tz)
    except (ValueError, TypeError):
        return None
    