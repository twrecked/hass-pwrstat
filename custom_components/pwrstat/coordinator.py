"""
This component provides support for pwrstat-api, a REST API wrapping
Cyberpower's pwrstat command.

"""

import logging
import requests
from datetime import timedelta

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

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

        self._data = {}
        self._url = ups_url

    def update_data(self):
        _LOGGER.debug(f"statring update to {self._url}")
        request = requests.get(self._url)
        if request.status_code == 200:
            self._data = request.json()
        else:
            self._data = {}
        _LOGGER.debug(f"data={self._data}")

    async def _async_update_data(self):
        await self.hass.async_add_executor_job(
            self.update_data
        )
        return self._data
