"""
This component provides support for pwrstat-api, a REST API wrapping
Cyberpower's pwrstat command.

"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.util import slugify
import homeassistant.helpers.device_registry as dr

from .const import *
from .coordinator import PwrStatCoordinator


__version__ = "0.1.0a1"

_LOGGER = logging.getLogger(__name__)

PWRSTAT_PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR
]


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry
) -> bool:
    _LOGGER.debug(f"async setup {entry.data}")

    if hass.data.get(COMPONENT_DOMAIN, None) is None:
        hass.data[COMPONENT_DOMAIN] = {}

    ups_name = entry.data[ATTR_UPS_NAME]
    ups_url = entry.data[ATTR_UPS_URL]
    ups_poll_every = entry.data[ATTR_UPS_POLL_EVERY]
    ups_id = slugify(f"{COMPONENT_DOMAIN} {ups_name}")

    coordinator = PwrStatCoordinator(hass, ups_name, ups_url, ups_poll_every)
    hass.data[COMPONENT_DOMAIN].update({
        ups_name: coordinator
    })

    await coordinator.async_config_entry_first_refresh()
    await _async_get_or_create_pwrstat_device_in_registry(hass, entry, ups_id, ups_name)
    await hass.config_entries.async_forward_entry_setups(entry, PWRSTAT_PLATFORMS)

    _LOGGER.debug(f"{ups_id}: would poll {ups_name} at {ups_url} every {ups_poll_every} seconds")
    return True


async def _async_get_or_create_pwrstat_device_in_registry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        ups_id,
        ups_name
) -> None:
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(COMPONENT_DOMAIN, ups_id)},
        manufacturer=COMPONENT_MANUFACTURER,
        name=ups_name,
        model=COMPONENT_MODEL,
        sw_version=__version__
    )
