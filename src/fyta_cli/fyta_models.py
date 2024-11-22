"""Models for FYTA."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any

from mashumaro import DataClassDictMixin, field_options


@dataclass
class Credentials():
    """Fyta login model."""

    access_token: str
    expiration: datetime


class PlantStatus(IntEnum):
    """Plant status enum."""
    DELETED = 0
    DOING_GREAT = 1
    NEED_ATTENTION = 2
    NO_SENSOR = 3


class PlantMeasurementStatus(IntEnum):
    """Plant measurement status enum."""
    NO_DATA = 0
    TOO_LOW = 1
    LOW = 2
    PERFECT = 3
    HIGH = 4
    TOO_HIGH = 5

class SensorStatus(IntEnum):
    """Sensor status enum."""
    NONE = 0
    CORRECT = 1
    ERROR = 2

@dataclass
class Plant(DataClassDictMixin):
    """Plant model."""

    # pylint: disable=too-many-instance-attributes

    battery_level: float | None
    fertilise_last: datetime | None
    fertilise_next: datetime | None
    last_updated: datetime | None
    light: float | None
    light_status: PlantMeasurementStatus
    low_battery: bool
    name: str = field(metadata=field_options(alias="nickname"))
    moisture: float  | None
    moisture_status: PlantMeasurementStatus
    notification_light: bool
    notification_nutrition: bool
    notification_temperature: bool
    notification_water: bool
    nutrients_status: PlantMeasurementStatus
    sensor_available: bool
    sensor_id: str | None
    sensor_status: SensorStatus
    sensor_update_available: bool
    sw_version: str
    status: PlantStatus
    online: bool
    ph: float | None
    plant_id: int
    plant_origin_path: str
    plant_thumb_path: str
    productive_plant: bool =field(metadata=field_options(alias="is_productive_plant"))
    repotted: bool
    salinity: float | None
    salinity_status: PlantMeasurementStatus
    scientific_name: str
    temperature: float  | None
    temperature_status: PlantMeasurementStatus

    @classmethod
    def __pre_deserialize__(cls, d: dict[Any, Any]) -> dict[Any, Any]:

        d |= {"sensor_available": True}
        d |= {"online": True}

        if d.get("measurements") is not None:
            d |= {"battery_level": d["measurements"]["battery"]}
            d |= {"light": d["measurements"]["light"]["values"]["current"]}
            d |= {"light_status": int(d["measurements"]["light"].get("status") or 0)}
            d |= {"moisture": d["measurements"]["moisture"]["values"]["current"]}
            d |= {"moisture_status": int(d["measurements"]["moisture"].get("status") or 0)}
            d |= {"nutrients_status": int(d["measurements"]["nutrients"].get("status") or 0)}
            d |= {"ph": d["measurements"].get("ph").get("values").get("current")}
            d |= {"salinity": d["measurements"]["salinity"]["values"]["current"]}
            d |= {"salinity_status": int(d["measurements"]["salinity"].get("status") or 0)}
            d |= {"temperature": d["measurements"]["temperature"]["values"]["current"]}
            d |= {"temperature_status": int(d["measurements"]["temperature"].get("status") or 0)}

        if d.get("sensor") is not None:
            d |= {"last_updated": d["sensor"]["received_data_at"]}
            d |= {"low_battery": d["sensor"]["is_battery_low"]}
            d |= {"sensor_id": d["sensor"]["id"]}
            d |= {"sw_version": d["sensor"]["version"]}
        d |= {"sensor_status": int(d.get("sensor",{}).get("status") or 0)}

        d |= {"notification_light": d.get("notifications",{}).get("light",False)}
        d |= {"notification_nutrition": d.get("notifications",{}).get("nutrition",False)}
        d |= {"notification_temperature": d.get("notifications",{}).get("temperature",False)}
        d |= {"notification_water": d.get("notifications",{}).get("water",False)}

        d |= {"fertilise_last": d.get("fertilisation",{}).get("last_fertilised_at")}
        d |= {"fertilise_next": d.get("fertilisation",{}).get("fertilise_at")}
        d |= {"repotted": d.get("fertilisation",{}).get("was_repotted",False)}

        return d
