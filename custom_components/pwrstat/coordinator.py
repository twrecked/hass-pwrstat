"""DataUpdateCoordinator for pwrstat integration."""

import asyncio
from datetime import timedelta
import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class PwrStatCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """pwrstat-api coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        ups_name: str,
        ups_url: str,
        ups_poll_every: int,
    ) -> None:
        """Initialize the pwrstat coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=ups_name,
            update_interval=timedelta(seconds=ups_poll_every),
        )
        self.ups_name = ups_name
        self.ups_url = ups_url
        self.ups_poll_every = ups_poll_every

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the pwrstat API endpoint."""
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                response = await session.get(self.ups_url)
                if response.status != 200:
                    raise UpdateFailed(
                        f"Error fetching data from {self.ups_url}: HTTP {response.status}"
                    )
                data = await response.json()
                if not isinstance(data, dict):
                    raise UpdateFailed(f"Unexpected data format received from {self.ups_url}")
                _LOGGER.debug("%s: fetched pwrstat data: %s", self.ups_name, data)
                return data
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout communicating with pwrstat API at {self.ups_url}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Client error communicating with pwrstat API at {self.ups_url}: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with pwrstat API: {err}") from err
