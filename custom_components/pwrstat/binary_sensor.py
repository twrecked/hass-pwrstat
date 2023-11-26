"""
This component provides support for pwrstat-api, a REST API wrapping
Cyberpower's pwrstat command.

"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
    DOMAIN as PLATFORM_DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import *


_LOGGER = logging.getLogger(__name__)


@dataclass
class PwrStatBinarySensorDescription(BinarySensorEntityDescription):
    suffix: str = "unknown"
    test: Callable[[Any], Any] | None = None


SENSORS = [
    PwrStatBinarySensorDescription(
        key="State",
        device_class=BinarySensorDeviceClass.POWER,
        suffix="Power",
        test=lambda v: v.split(" ")[0] == "Normal"
    ),
    PwrStatBinarySensorDescription(
        key="Battery Capacity",
        device_class=BinarySensorDeviceClass.BATTERY,
        suffix="Low Battery",
        test=lambda v: int(v.split(" ")[0]) < 35
    )
]


async def async_setup_entry(
        hass: HomeAssistantType,
        entry: ConfigEntry,
        async_add_entities: Callable[[list], None],
) -> None:
    _LOGGER.debug("setting up the entries...")

    ups_name = entry.data[ATTR_UPS_NAME]
    ups_id = slugify(f"{COMPONENT_DOMAIN} {ups_name}")
    coordinator = hass.data[COMPONENT_DOMAIN][ups_name]

    sensors = []
    for SENSOR in SENSORS:
        sensors.append(PwrStatBinarySensor(coordinator, ups_name, ups_id, SENSOR))

    async_add_entities(sensors)


class PwrStatBinarySensor(CoordinatorEntity, BinarySensorEntity):

    entity_description: PwrStatBinarySensorDescription

    def __init__(self, coordinator, ups_name, ups_id, description):
        super().__init__(coordinator, context=ups_name)

        self.entity_description = description
        self._attr_name = f"{ups_name} {self.entity_description.suffix}"
        self._attr_unique_id = slugify(f"{ups_id} {self.entity_description.suffix}")
        self._attr_device_info = DeviceInfo(
            identifiers={(COMPONENT_DOMAIN, ups_id)},
            manufacturer=COMPONENT_MANUFACTURER,
            model=COMPONENT_MODEL,
        )
        self.entity_id = f"{PLATFORM_DOMAIN}.{self._attr_unique_id}"

        _LOGGER.info(f"PwrStatBinarySensor: {self.name} created")
        self._update()

    def _update(self):
        # Nothing there...
        if not self.coordinator.data:
            return

        # Get value.
        self._attr_is_on = self.entity_description.test(self.coordinator.data[self.entity_description.key])
        _LOGGER.debug(f"{self._attr_name} --> {self._attr_is_on}")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update()
        self.async_write_ha_state()
