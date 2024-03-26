"""Client to access FYTA API."""
# The documentation for the API can be found here:
# https://fyta-io.notion.site/FYTA-Public-API-d2f4c30306f74504924c9a40402a3afd

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any

from aiohttp import BasicAuth, ClientSession

from .fyta_exceptions import (
    FytaConnectionError,
    FytaAuthentificationError,
    FytaPasswordError,
    FytaPlantError,
    )

FYTA_AUTH_URL = 'https://web.fyta.de/api/auth/login'
FYTA_PLANT_URL = 'https://web.fyta.de/api/user-plant'

_LOGGER = logging.getLogger(__name__)


class Client():
    """Client class to access FYTA API."""
    def __init__(self, email: str, password: str, access_token = "", expiration = None):

        self.email = email
        self.password = password
        self.access_token = access_token
        self.expiration = expiration

        self.session: ClientSession = ClientSession()
        self._close_session = True

        self.request_timeout = 10

    async def test_connection(self) -> bool:
        """Test the connection to FYTA-Server"""

        response = await self.session.post(FYTA_AUTH_URL)
        r=await response.text()

        if r == '{"message": "Unsupported Media Type"}':
            return True

        return False


    async def login(self) -> dict[str,str | datetime]:
        """Handle a request to FYTA."""

        if self.access_token != "" and self.expiration.timestamp() > datetime.now().timestamp():
            return {"access_token": self.access_token, "expiration": self.expiration}

        payload = {
            'email': self.email,
            'password': self.password,
        }

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.post(
                    url=FYTA_AUTH_URL,
                    auth=BasicAuth(self.email, self.password),
                    json=payload
                )

        except asyncio.TimeoutError as exception:
            _LOGGER.exception("timeout error")
            msg = "Timeout occurred while connecting to Fyta-server"
            raise FytaConnectionError(msg) from exception

        json_response = await response.json()

        if json_response == {"statusCode":404,"error":"Not Found"}:
            _LOGGER.exception("Authentication failed")
            raise FytaAuthentificationError
        if json_response == {
            "statusCode":401,
            "error":"Unauthorized",
            "errors":[{"message":"Could not authenticate user"}]
        }:
            raise FytaPasswordError

        self.access_token = json_response["access_token"]
        #self.refresh_token = json_response["refresh_token"]
        self.expiration = datetime.now() + timedelta(seconds=int(json_response["expires_in"]))

        return {"access_token": self.access_token, "expiration": self.expiration}

    async def get_plants(self) -> dict[int,str]:
        """Get a list of all available plants from FYTA"""

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        if self.expiration.timestamp() > datetime.now().timestamp():
            await self.login() #get new access token, if current token expired

        header = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.get(url=FYTA_PLANT_URL, headers = header)
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to Fyta-server"
            raise FytaConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")

        if content_type.count("text/html") > 0:
            text = await response.text()
            msg = "Error occurred while fetching plant data"
            raise FytaPlantError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        json_response = await response.json()

        plant_list: dict = json_response["plants"]

        plants: dict[int,str] = {}
        for plant in plant_list:
            plants |= {int(plant["id"]): plant["nickname"]}

        return plants

    async def get_plant_data(self, plant_id: int) -> dict[str,Any]:
        """Get information about a specific plant"""

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        if self.expiration.timestamp() > datetime.now().timestamp():
            await self.login() #get new access token, if current token expired

        header = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        url = f"{FYTA_PLANT_URL}/{plant_id}"

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.get(url=url, headers = header)
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to Fyta-server"
            raise FytaConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")

        if content_type.count("text/html") > 0:
            text = await response.text()
            msg = f"Error occurred while fetching plant data for plant {plant_id}"
            raise FytaPlantError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        plant: dict[str,Any] = await response.json()

        return plant

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()
