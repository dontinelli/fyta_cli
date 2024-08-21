"""Tests for fyta_cli."""

from aioresponses import aioresponses

from src.fyta_cli.fyta_client import FYTA_AUTH_URL
from src.fyta_cli.fyta_connector import FytaConnector
from src.fyta_cli.fyta_models import Credentials

from . import load_fixture


async def test_connection(
    responses: aioresponses,
) -> None:
    """Test connection."""
    responses.post(
        FYTA_AUTH_URL,
        status=200,
        body='{"message": "Unsupported Media Type"}',
    )

    fyta_connector = FytaConnector("example@example.com", "examplepassword")

    assert await fyta_connector.test_connection()

    assert fyta_connector.client.session is not None
    assert not fyta_connector.client.session.closed
    await fyta_connector.client.close()
    assert fyta_connector.client.session.closed


async def test_login(
    responses: aioresponses,
) -> None:
    """Test login."""
    responses.post(
        FYTA_AUTH_URL,
        status=200,
        body=load_fixture("login_response.json"),
    )

    fyta_connector = FytaConnector("example@example.com", "examplepassword")

    credentials: Credentials = await fyta_connector.login()

    assert credentials.access_token =="111111111111111111111111111111111111111"

    assert fyta_connector.client.session is not None
    assert not fyta_connector.client.session.closed
    await fyta_connector.client.close()
    assert fyta_connector.client.session.closed
