"""Tests for fyta_cli."""

from datetime import datetime, timedelta, UTC

from aioresponses import aioresponses

import pytest
from syrupy.assertion import SnapshotAssertion

from fyta_cli.fyta_client import FYTA_AUTH_URL, FYTA_PLANT_URL
from fyta_cli.fyta_connector import FytaConnector
from fyta_cli.fyta_exceptions import (
    FytaAuthentificationError,
    FytaConnectionError,
    FytaError,
    FytaPasswordError,
    FytaPlantError,
)
from fyta_cli.fyta_models import Credentials, Plant

from . import load_fixture


@pytest.mark.parametrize(
    ("response", "return_value"),
    [
        ('{"message": "Unsupported Media Type"}', True),
        ('', False),
    ],
)
async def test_connection(
    responses: aioresponses,
    response: str,
    return_value: bool,
) -> None:
    """Test connection."""
    responses.post(
        FYTA_AUTH_URL,
        body=response,
    )

    fyta_connector = FytaConnector("example@example.com", "examplepassword")

    assert await fyta_connector.test_connection() == return_value

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

    assert credentials.access_token == "111111111111111111111111111111111111111"
    assert fyta_connector.email == "example@example.com"
    assert fyta_connector.fyta_id == "example@example.com"

    assert fyta_connector.client.session is not None
    assert not fyta_connector.client.session.closed
    await fyta_connector.client.close()
    assert fyta_connector.client.session.closed


async def test_login_existing_credentials(
) -> None:
    """Test login."""

    current_expiration: datetime = datetime.now() + timedelta(days=1)

    fyta_connector = FytaConnector(
        "example@example.com",
        "examplepassword",
        "111111111111111111111111111111111111111",
        current_expiration
    )

    await fyta_connector.login()

    assert fyta_connector.access_token == "111111111111111111111111111111111111111"
    assert fyta_connector.expiration == current_expiration.astimezone(UTC)

    assert fyta_connector.client.session is not None
    assert not fyta_connector.client.session.closed
    await fyta_connector.client.close()
    assert fyta_connector.client.session.closed


@pytest.mark.parametrize(
    ("response", "request_timeout", "error"),
    [
        ('{"message": "Unsupported Media Type"}', True, FytaConnectionError),
        ('{"statusCode": 404, "error": "Not Found"}', False, FytaAuthentificationError),
        ('{"statusCode": 401,"error": "Unauthorized","errors": [{"message": "Could not authenticate user"}]}', False, FytaPasswordError),  # pylint: disable=line-too-long
    ],
)
async def test_login_exceptions(
    responses: aioresponses,
    response: str,
    request_timeout: bool,
    error: FytaError,
) -> None:
    """Test login."""
    responses.post(
        FYTA_AUTH_URL,
        timeout=request_timeout,
        body=response,
    )

    fyta_connector = FytaConnector("example@example.com", "examplepassword")

    with pytest.raises(error):  # type: ignore [call-overload]
        await fyta_connector.login()

    await fyta_connector.client.close()
    assert fyta_connector.client.session.closed


async def test_get_plant_list(
    responses: aioresponses,
    snapshot: SnapshotAssertion
) -> None:
    """Test login."""
    responses.get(
        FYTA_PLANT_URL,
        status=200,
        body=load_fixture("get_user_plants.json"),
    )

    fyta_connector = FytaConnector(
        "example@example.com",
        "examplepassword",
        "111111111111111111111111111111111111111",
        datetime.now() + timedelta(days=1),
    )

    await fyta_connector.update_plant_list()

    assert fyta_connector.data == snapshot

    await fyta_connector.client.close()
    assert fyta_connector.client.session.closed


@pytest.mark.parametrize(
    ("headers", "request_timeout", "error"),
    [
        ({"Content-Type": ""}, True, FytaConnectionError),
        ({"Content-Type": "text/html"}, False, FytaPlantError),
    ],
)
async def test_get_plant_list_exceptions(
    responses: aioresponses,
    headers: dict[str, str],
    request_timeout: bool,
    error: FytaError,
) -> None:
    """Test login."""
    responses.get(
        FYTA_PLANT_URL,
        timeout=request_timeout,
        headers=headers,
    )

    fyta_connector = FytaConnector(
        "example@example.com",
        "examplepassword",
        "111111111111111111111111111111111111111",
        datetime.now() + timedelta(days=1),
    )
    await fyta_connector.client.close()
    fyta_connector.client.session = None  # type: ignore [assignment]

    with pytest.raises(error):  # type: ignore [call-overload]
        await fyta_connector.update_plant_list()


async def test_get_plant_data(
    responses: aioresponses,
    snapshot: SnapshotAssertion
) -> None:
    """Test login."""
    responses.get(
        FYTA_PLANT_URL,
        status=200,
        body=load_fixture("get_user_plants.json"),
    )
    responses.get(
        FYTA_PLANT_URL + f"/{0}",
        status=200,
        body=load_fixture("get_plant_details_0.json"),
    )
    responses.get(
        FYTA_PLANT_URL + f"/{1}",
        status=200,
        body=load_fixture("get_plant_details_1.json"),
    )
    responses.get(
        FYTA_PLANT_URL + f"/{2}",
        status=200,
        body=load_fixture("get_plant_details_2.json"),
    )
    responses.post(
        FYTA_PLANT_URL + f"/measurements/{0}",
        status=200,
        body=load_fixture("get_measurements.json"),
    )
    responses.post(
        FYTA_PLANT_URL + f"/measurements/{1}",
        status=200,
        body=load_fixture("get_measurements.json"),
    )
    responses.post(
        FYTA_PLANT_URL + f"/measurements/{2}",
        status=200,
        body=load_fixture("get_measurements.json"),
    )

    fyta_connector = FytaConnector(
        "example@example.com",
        "examplepassword",
        "111111111111111111111111111111111111111",
        datetime.now() + timedelta(days=1)
    )
    plants: dict[int, Plant] = await fyta_connector.update_all_plants()

    assert plants == snapshot

    await fyta_connector.client.close()
    assert fyta_connector.client.session.closed


@pytest.mark.parametrize(
    ("headers", "request_timeout", "error"),
    [
        ({"Content-Type": "application/json"}, True, FytaConnectionError),
        ({"Content-Type": "text/html"}, False, FytaPlantError),
    ],
)
async def test_get_plant_data_exceptions(
    responses: aioresponses,
    headers: dict[str, str],
    request_timeout: bool,
    error: FytaError,
) -> None:
    """Test login."""
    responses.get(
        FYTA_PLANT_URL + "/0",
        headers=headers,
        timeout=request_timeout,
        body=load_fixture("get_plant_details_0.json"),
    )
    responses.get(
        FYTA_PLANT_URL + "/1",
        headers=headers,
        timeout=request_timeout,
        body=load_fixture("get_plant_details_1.json"),
    )

    fyta_connector = FytaConnector(
        "example@example.com",
        "examplepassword",
        "111111111111111111111111111111111111111",
        datetime.now() + timedelta(days=1)
    )
    await fyta_connector.client.close()
    fyta_connector.client.session = None  # type: ignore [assignment]

    with pytest.raises(error):  # type: ignore [call-overload]
        await fyta_connector.client.get_plant_data(0)

    with pytest.raises(error):  # type: ignore [call-overload]
        await fyta_connector.client.get_plant_data(1)

    await fyta_connector.client.close()
    assert fyta_connector.client.session.closed
