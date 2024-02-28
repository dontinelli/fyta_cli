# coding: utf-8

from datetime import datetime
import pytz

from .fyta_client import Client
from .utils import safe_get

PLANT_STATUS = {
    1: "too_low",
    2: "low",
    3: "perfect",
    4: "high",
    5: "too_high",
    }

class FytaConnector(object):

    expiration: datetime | None = None

    def __init__(self, email, password, access_token = "", expiration = None, timezone: pytz.timezone = pytz.utc):

        self.email = email
        self.password = password
        self.client = Client(email, password, access_token, expiration)
        self.online = False
        self.plant_list = {}
        self.plants = {}
        self.timezone = timezone

    async def test_connection(self) -> bool:

        return await self.client.test_connection()


    async def login(self) -> dict:
        login = await self.client.login()
        self.access_token = login["access_token"]
        self.expiration = login["expiration"]
        self.online = True

        return login


    async def update_plant_list(self):
        self.plant_list = await self.client.get_plants()

        return self.plant_list


    async def update_all_plants(self):
        plants = {}

        plant_list = await self.update_plant_list()

        for plant in plant_list.keys():
            current_plant = await self.update_plant_data(plant)
            if current_plant is not {}:
                plants |= {plant: current_plant}

        self.plants = plants

        return plants

    async def update_plant_data(self, plant_id: int):

        p = await self.client.get_plant_data(plant_id)
        plant_data = p["plant"]

        if plant_data["sensor"] is None:
            return {}

        current_plant = {}
        current_plant |= {"online": True}
        current_plant |= {"battery_status:": safe_get(plant_data, "sensor.is_battery_low", bool)}
        current_plant |= {"sw_version": safe_get(plant_data, "sensor.version", str)}
        current_plant |= {"plant_id": safe_get(plant_data, "id", int)}
        current_plant |= {"name": safe_get(plant_data, "nickname", str)}
        current_plant |= {"scientific_name": safe_get(plant_data, "scientific_name", str)}
        current_plant |= {"status": safe_get(plant_data, "status", int)}
        current_plant |= {"temperature_status": safe_get(plant_data, "measurements.temperature.status", int)}
        current_plant |= {"light_status": safe_get(plant_data, "measurements.light.status", int)}
        current_plant |= {"moisture_status": safe_get(plant_data, "measurements.moisture.status", int)}
        current_plant |= {"salinity_status": safe_get(plant_data, "measurements.salinity.status", int)}
        current_plant |= {"ph": safe_get(plant_data, "measurements.ph.values.current", float)}
        current_plant |= {"temperature": safe_get(plant_data, "measurements.temperature.values.current", float)}
        current_plant |= {"light": safe_get(plant_data, "measurements.light.values.current", float)}
        current_plant |= {"moisture": safe_get(plant_data, "measurements.moisture.values.current", float)}
        current_plant |= {"salinity": safe_get(plant_data, "measurements.salinity.values.current", float)}
        current_plant |= {"battery_level": safe_get(plant_data, "measurements.battery", float)}
        current_plant |= {"last_updated": self.timezone.localize(datetime.fromisoformat(plant_data["sensor"]["received_data_at"]))}

        return current_plant

    @property
    def fyta_id(self) -> str:
        """ID for FYTA object"""
        return self.email

    @property
    def data(self) -> dict:
        """ID for FYTA object"""
        return self.plants
