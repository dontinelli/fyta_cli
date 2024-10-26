"""Connector class to manage access to FYTA API."""

from datetime import datetime, tzinfo, UTC
from zoneinfo import ZoneInfo

from .fyta_client import Client
from .fyta_models import Credentials, Plant


class FytaConnector:
    """Connector class to access FYTA API."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments

    def __init__(
        self,
        email: str,
        password: str,
        access_token: str = "",
        expiration: datetime | None = None,
        tz: str = "",
    ) -> None:
        """Initialize connector class."""

        timezone: tzinfo = UTC if tz == "" else ZoneInfo(tz)
        ex: datetime = (
            datetime.now(timezone)
            if expiration is None
            else expiration.astimezone(timezone)
        )
        self.online: bool = False
        self.plant_list: dict[int, str] = {}
        self.plants: dict[int, Plant] = {}

        self.client = Client(email, password, access_token, ex, timezone)

    async def test_connection(self) -> bool:
        """Test if connection to FYTA API works."""

        return await self.client.test_connection()

    async def login(self) -> Credentials:
        """Login with credentials to get access token."""

        login = await self.client.login()

        if login != {}:
            self.online = True

        return login

    async def update_plant_list(self) -> dict[int, str]:
        """Get list of all available plants."""

        self.plant_list = await self.client.get_plants()

        return self.plant_list

    async def update_all_plants(self) -> dict[int, Plant]:
        """Get data of all available plants."""

        plants: dict[int, Plant] = {}

        plant_list: dict[int, str] = await self.update_plant_list()

        for plant in plant_list:
            current_plant: Plant | None = await self.update_plant_data(plant)
            if current_plant is not None:
                plants |= {plant: current_plant}

        self.plants = plants

        return plants

    async def update_plant_data(self, plant_id: int) -> Plant | None:
        """Get data of specific plant."""

        p: dict = await self.client.get_plant_data(plant_id)

        if ("plant" not in p) or (p["plant"]["sensor"] is None):
            return None

        plant_data: dict = p["plant"]

        current_plant = Plant.from_dict(plant_data)
        if current_plant.last_updated is not None:
            current_plant.last_updated = current_plant.last_updated.astimezone(self.client.timezone)

        return current_plant

    @property
    def access_token(self) -> str:
        """Access token for FYTA API."""
        return self.client.access_token

    @property
    def data(self) -> dict[int, Plant]:
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
