"""Connector class to manage access to FYTA API."""

from datetime import datetime, UTC
from typing import Any
from zoneinfo import ZoneInfo

from .fyta_client import Client
from .utils import safe_get

# status = 0 if user_plant deleted, 1 for user_plant in green, 2 for yellow, 3 for red
PLANT_STATUS = {
    0: "deleted",
    1: "doing_great",
    2: "need_attention",
    3: "no_sensor",
}

PLANT_MEASUREMENT_STATUS = {
    0: "no_data",
    1: "too_low",
    2: "low",
    3: "perfect",
    4: "high",
    5: "too_high",
}


class FytaConnector:
    """Connector class to access FYTA API."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments

    def __init__(
        self,
        email: str,
        password: str,
        access_token: str = "",
        expiration: datetime | None = None,
        tz: str = "",
    ) -> None:
        """Initialize connector class."""

        timezone: ZoneInfo = UTC if tz == "" else ZoneInfo(tz)
        ex: datetime = (
            datetime.now(timezone)
            if expiration is None
            else expiration.astimezone(timezone)
        )
        self.online: bool = False
        self.plant_list: dict[int, str] = {}
        self.plants: dict[int, dict[str, Any]] = {}

        self.client = Client(email, password, access_token, ex, timezone)

    async def test_connection(self) -> bool:
        """Test if connection to FYTA API works."""

        return await self.client.test_connection()

    async def login(self) -> dict[str, str | datetime]:
        """Login with credentials to get access token."""

        login = await self.client.login()

        if login != {}:
            self.online = True

        return login

    async def update_plant_list(self) -> dict[int, str]:
        """Get list of all available plants."""

        self.plant_list = await self.client.get_plants()

        return self.plant_list

    async def update_all_plants(self) -> dict[int, dict[str, Any]]:
        """Get data of all available plants."""

        plants: dict[int, dict[str, Any]] = {}

        plant_list = await self.update_plant_list()

        for plant in plant_list:
            current_plant = await self.update_plant_data(plant)
            if current_plant != {}:
                plants |= {plant: current_plant}

        self.plants = plants

        return plants

    async def update_plant_data(self, plant_id: int) -> dict[str, Any]:
        """Get data of specific plant."""

        p: dict = await self.client.get_plant_data(plant_id)

        current_plant = {}

        if ("plant" not in p) or (p["plant"]["sensor"] is None):
            current_plant |= {"sensor_available": False}
        else:
            plant_data: dict = p["plant"]
            current_plant |= {"online": True}
            current_plant |= {"sensor_available": True}
            current_plant |= {
                "battery_status:": safe_get(plant_data, "sensor.is_battery_low", bool)
            }
            current_plant |= {"sw_version": safe_get(plant_data, "sensor.version", str)}
            current_plant |= {"plant_id": safe_get(plant_data, "plant_id", int)}
            current_plant |= {"name": safe_get(plant_data, "nickname", str)}
            current_plant |= {
                "scientific_name": safe_get(plant_data, "scientific_name", str)
            }
            current_plant |= {"status": safe_get(plant_data, "status", int)}
            current_plant |= {
                "plant_thumb_path": safe_get(plant_data, "plant_thumb_path", str)
            }
            current_plant |= {
                "plant_origin_path": safe_get(plant_data, "plant_origin_path", str)
            }
            current_plant |= {
                "temperature_status": safe_get(
                    plant_data, "measurements.temperature.status", int
                )
            }
            current_plant |= {
                "light_status": safe_get(plant_data, "measurements.light.status", int)
            }
            current_plant |= {
                "moisture_status": safe_get(
                    plant_data, "measurements.moisture.status", int
                )
            }
            current_plant |= {
                "salinity_status": safe_get(
                    plant_data, "measurements.salinity.status", int
                )
            }
            current_plant |= {
                "ph": safe_get(plant_data, "measurements.ph.values.current", float)
            }
            current_plant |= {
                "temperature": safe_get(
                    plant_data, "measurements.temperature.values.current", float
                )
            }
            current_plant |= {
                "light": safe_get(
                    plant_data, "measurements.light.values.current", float
                )
            }
            current_plant |= {"light_dli": safe_get(plant_data, "dli_light", float)}
            current_plant |= {
                "moisture": safe_get(
                    plant_data, "measurements.moisture.values.current", float
                )
            }
            current_plant |= {
                "salinity": safe_get(
                    plant_data, "measurements.salinity.values.current", float
                )
            }
            current_plant |= {
                "battery_level": safe_get(plant_data, "measurements.battery", float)
            }
            current_plant |= {
                "last_updated": safe_get(
                    plant_data,
                    "sensor.received_data_at",
                    datetime,
                    self.client.timezone,
                )
            }

        return current_plant

    @property
    def access_token(self) -> str:
        """Access token for FYTA API."""
        return self.client.access_token

    @property
    def data(self) -> dict:
        """ID for FYTA object."""
        return self.plants

    @property
    def email(self) -> str:
        """Email of FYTA account."""
        return self.client.email

    @property
    def expiration(self) -> datetime:
        """Expiration of access token."""
        return self.client.expiration

    @property
    def fyta_id(self) -> str:
        """ID for FYTA object."""
        return self.email
