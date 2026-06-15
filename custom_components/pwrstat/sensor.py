"""
This component provides support for pwrstat-api, a REST API wrapping
Cyberpower's pwrstat command.

"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    DOMAIN as PLATFORM_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTime,
)
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
class PwrStatSensorDescription(SensorEntityDescription):
    suffix: str = "unknown"
    convert: Callable[[Any], Any] | None = None
    extra_attributes: dict[str, Any] | None = None


SENSORS = [
    PwrStatSensorDescription(
        key="Load",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suffix="Load",
        convert=lambda v: v.split(" ")[0]
    ),
    PwrStatSensorDescription(
        key="Battery Capacity",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suffix="Battery Capacity",
        convert=lambda v: v.split(" ")[0]
    ),
    PwrStatSensorDescription(
        key="Output Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suffix="Output Voltage",
        convert=lambda v: v.split(" ")[0]
    ),
    PwrStatSensorDescription(
        key="Utility Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suffix="Utility Voltage",
        convert=lambda v: v.split(" ")[0]
    ),
    PwrStatSensorDescription(
        key="Remaining Runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        suffix="Remaining Runtime",
        convert=lambda v: int(v.split(" ")[0])
    ),
    PwrStatSensorDescription(
        key="State",
        device_class=SensorDeviceClass.ENUM,
        options=[
            "normal",
            "power failure"
        ],
        suffix="State",
        extra_attributes={
            "Power Supply by": "",
            "Firmware Number": "",
            "Model Name": "",
            "Rating Power": "",
            "Rating Voltage": "",
            "Last Power Event": "",
            "Test Result": ""
        },
        convert=lambda v: v.lower()
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
        sensors.append(PwrStatSensor(coordinator, ups_name, ups_id, SENSOR))

    async_add_entities(sensors)


class PwrStatSensor(CoordinatorEntity, SensorEntity):

    entity_description: PwrStatSensorDescription

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

        _LOGGER.info(f"PwrStatSensor: {self.name} created")

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        try:
            return self.entity_description.convert(self.coordinator.data[self.entity_description.key])
        except Exception:
            return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.coordinator.data is not None and self.entity_description.key in self.coordinator.data

    @property
    def extra_state_attributes(self):
        """Return extra_state_attributes."""
        if not self.entity_description.extra_attributes or not self.coordinator.data:
            return None

        attrs = {}
        for attribute in self.entity_description.extra_attributes.keys():
            attrs[attribute] = self.coordinator.data.get(attribute, "not available")
        return attrs
