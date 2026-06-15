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
from homeassistant.core import (
    HomeAssistant,
    callback,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import *


_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
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
        hass: HomeAssistant,
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

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None
        try:
            return self.entity_description.test(self.coordinator.data[self.entity_description.key])
        except Exception:
            return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.coordinator.data is not None and self.entity_description.key in self.coordinator.data
