"""Client to access FYTA API"""
# The documentation for the API can be found here:
# https://fyta-io.notion.site/FYTA-Public-API-d2f4c30306f74504924c9a40402a3afd

from __future__ import annotations

import requests
import logging
from datetime import datetime, timedelta

import asyncio
from aiohttp import BasicAuth, ClientSession
from dataclasses import dataclass, field

FYTA_AUTH_URL = 'http://web.fyta.de/api/auth/login'
FYTA_PLANT_URL = 'http://web.fyta.de/api/user-plant'

_LOGGER = logging.getLogger(__name__)

class Client(object):
    def __init__(self, email: str, password: str, access_token = "", expiration = None):

        self.session: ClientSession | None = None

        self.email = email
        self.password = password
        self.access_token = access_token
        self.expiration = expiration
        self.refresh_token = ""

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        self.request_timeout = 10


    async def test_connection(self) -> bool:
        """Test the connection to FYTA-Server"""

        response = await self.session.post(FYTA_AUTH_URL)
        r=await response.text()

        if r == '{"message": "Unsupported Media Type"}':
            return True

        return False


    async def login(self) -> dict[str, str]:
        """Handle a request to FYTA."""

        payload = {
            'email': self.email,
            'password': self.password,
        }

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.post(url=FYTA_AUTH_URL, auth=BasicAuth(self.email, self.password), json=payload)

        except asyncio.TimeoutError as exception:
            _LOGGER.exception("timeout error")
            msg = "Timeout occurred while connecting to Fyta-server"
            #raise HomeassistantAnalyticsConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")

        json_response = await response.json()

        if json_response == '{"statusCode":404,"error":"Not Found"}':
            _LOGGER.exception("Authentication failed")
            raise ConfigEntryAuthFailed

        self.access_token = json_response["access_token"]
        self.refresh_token = json_response["refresh_token"]
        self.expiration = datetime.now() + timedelta(seconds=int(json_response["expires_in"]))

        return {"access_token": self.access_token, "expiration": self.expiration}

    async def get_plants(self, plant_id: int) -> dict:
        """Get a list of all available plants from FYTA"""

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        if self.expiration > datetime.now():
            await self.login() #get new access token, if current token expired

        header = {
            "Authorization": f"Bearer {self.access_token}",
        }

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.post(
                    FYTA_PLANT_URL,
                    headers = header,
                )
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to Fyta-server"
            raise HomeassistantAnalyticsConnectionError(msg) from exception

        json_response = await response.json()

        plants = {}
        for plant in json_response["plants"]:
            plants |= {plant["plant_id"], plant["nickname"]}

        return plants

    async def get_plant_data(self, plant_id: int) -> dict:
        """Get information about a specific plant"""


        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        if self.expiration > datetime.now():
            await self.login() #get new access token, if current token expired

        header = {
            "Authorization": f"Bearer {self.access_token}",
        }
        url = f"{FYTA_PLANT_URL}/{plant_id}"

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.post(
                    url,
                    headers = header,
                )
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to Fyta-server"
            raise HomeassistantAnalyticsConnectionError(msg) from exception

        plant = await response.json()

        return plant

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

