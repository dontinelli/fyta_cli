"""Client to access FYTA API"""
# The documentation for the API can be found here:
# https://fyta-io.notion.site/FYTA-Public-API-d2f4c30306f74504924c9a40402a3afd

from __future__ import annotations

FYTA_AUTH_URL = 'http://web.fyta.de/api/auth'
FYTA_PLANT_URL = 'http://web.fyta.de/api/user-plant'

import requests
from datetime import datetime

import asyncio
from aiohttp import ClientSession
from dataclasses import dataclass, field

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

        if await response.text() == '{"message":"Missing Authentication Token"}':
            return True

        return False


    async def login(self) -> dict[str, str]:
        """Handle a request to FYTA."""

        header = {
            "Content-Type": "application/json",
        }
        payload = {
            'email': self.email,
            'password': self.password,
        }

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.post(
                    FYTA_AUTH_URL,
                    data = payload,
                    headers = header,
                )
        except asyncio.TimeoutError as exception:
            msg = "Timeout occurred while connecting to Fyta-server"
            raise HomeassistantAnalyticsConnectionError(msg) from exception

        content_type = response.headers.get("Content-Type", "")

        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected response from Fyta-Server"
            raise HomeassistantAnalyticsError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        json_response = await response.json()

        #print(content_type)
        #print(header)
        #print(payload)
        #print(json_response)

        self.access_token = json_response["access_token"]
        self.refresh_token = json_response["refresh_token"]
        self.expiration = datetime.now() + datetime.time( 0, 0, json_response["expires_in"])

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

        content_type = response.headers.get("Content-Type", "")

        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected response from Homeassistant Analytics"
            raise HomeassistantAnalyticsError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

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

        content_type = response.headers.get("Content-Type", "")

        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected response from Homeassistant Analytics"
            raise HomeassistantAnalyticsError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        plant = await response.json()

        return plant

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

