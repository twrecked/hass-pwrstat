"""
This component provides support for pwrstat-api, a REST API wrapping
Cyberpower's pwrstat command.

"""

import logging
import asyncio
from datetime import timedelta

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import *


_LOGGER = logging.getLogger(__name__)


class PwrStatCoordinator(DataUpdateCoordinator):
    """pwrstat-api coordinator
    """

    def __init__(self, hass, ups_name, ups_url, ups_poll_every):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=ups_name,
            update_interval=timedelta(seconds=ups_poll_every),
        )

        self._url = ups_url

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(10):
                response = await session.get(self._url)
                if response.status != 200:
                    raise UpdateFailed(f"Error fetching data from {self._url}: {response.status}")
                
                data = await response.json()
                _LOGGER.debug(f"data={data}")
                return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
