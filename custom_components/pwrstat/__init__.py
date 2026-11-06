"""This component provides support for pwrstat-api, a REST API wrapping Cyberpower's pwrstat command."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.device_registry as dr
from homeassistant.util import slugify

from .const import (
    ATTR_UPS_NAME,
    ATTR_UPS_POLL_EVERY,
    ATTR_UPS_URL,
    COMPONENT_DOMAIN,
    COMPONENT_MANUFACTURER,
    COMPONENT_MODEL,
    DOMAIN,
)
from .coordinator import PwrStatCoordinator

__version__ = "0.3.0-alpha.1"

_LOGGER = logging.getLogger(__name__)

PWRSTAT_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]

type PwrStatConfigEntry = ConfigEntry[PwrStatCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: PwrStatConfigEntry) -> bool:
    """Set up pwrstat from a config entry."""
    _LOGGER.debug("Setting up entry: %s", entry.data)

    ups_name = entry.data[ATTR_UPS_NAME]
    ups_url = entry.options.get(ATTR_UPS_URL, entry.data[ATTR_UPS_URL])
    ups_poll_every = entry.options.get(ATTR_UPS_POLL_EVERY, entry.data[ATTR_UPS_POLL_EVERY])
    ups_id = slugify(f"{DOMAIN} {ups_name}")

    coordinator = PwrStatCoordinator(hass, ups_name, ups_url, ups_poll_every)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    # Keep hass.data populated for backwards compatibility
    hass.data.setdefault(DOMAIN, {})[ups_name] = coordinator

    # Create/update device in device registry with live device info
    _async_get_or_create_pwrstat_device_in_registry(hass, entry, coordinator, ups_id, ups_name)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PWRSTAT_PLATFORMS)

    _LOGGER.debug(
        "%s: polling %s at %s every %s seconds",
        ups_id,
        ups_name,
        ups_url,
        ups_poll_every,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PwrStatConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PWRSTAT_PLATFORMS):
        ups_name = entry.data[ATTR_UPS_NAME]
        if DOMAIN in hass.data:
            hass.data[DOMAIN].pop(ups_name, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: PwrStatConfigEntry) -> None:
    """Reload config entry after options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _async_get_or_create_pwrstat_device_in_registry(
    hass: HomeAssistant,
    entry: PwrStatConfigEntry,
    coordinator: PwrStatCoordinator,
    ups_id: str,
    ups_name: str,
) -> None:
    """Register or update device in registry."""
    data = coordinator.data or {}
    model = data.get("Model Name") or COMPONENT_MODEL
    sw_version = data.get("Firmware Number") or __version__

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, ups_id)},
        manufacturer=COMPONENT_MANUFACTURER,
        name=ups_name,
        model=model,
        sw_version=sw_version,
    )
