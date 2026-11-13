"""Support for Cyberpower pwrstat binary sensors."""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import PwrStatConfigEntry, __version__
from .const import (
    ATTR_UPS_NAME,
    COMPONENT_MANUFACTURER,
    COMPONENT_MODEL,
    DOMAIN,
)
from .coordinator import PwrStatCoordinator

_LOGGER = logging.getLogger(__name__)


def _test_power_normal(value: Any) -> bool | None:
    """Return True if power state is Normal (utility power present)."""
    if value is None:
        return None
    return str(value).strip().lower().startswith("normal")


def _test_battery_low(value: Any) -> bool | None:
    """Return True if battery capacity is below 35%."""
    if value is None:
        return None
    try:
        pct = int(str(value).strip().split(" ")[0])
        return pct < 35
    except (ValueError, IndexError):
        return None


@dataclass(frozen=True, kw_only=True)
class PwrStatBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a PwrStat binary sensor entity."""

    suffix: str = "unknown"
    test: Callable[[Any], bool | None] | None = None


SENSORS: list[PwrStatBinarySensorDescription] = [
    PwrStatBinarySensorDescription(
        key="State",
        name="Utility Power",
        device_class=BinarySensorDeviceClass.POWER,
        suffix="Utility Power",
        test=_test_power_normal,
    ),
    PwrStatBinarySensorDescription(
        key="Battery Capacity",
        name="Low Battery",
        device_class=BinarySensorDeviceClass.BATTERY,
        suffix="Low Battery",
        test=_test_battery_low,
    ),
]


def _build_device_info(coordinator: PwrStatCoordinator, ups_id: str, ups_name: str) -> DeviceInfo:
    """Build DeviceInfo using coordinator data."""
    data = coordinator.data or {}
    return DeviceInfo(
        identifiers={(DOMAIN, ups_id)},
        manufacturer=COMPONENT_MANUFACTURER,
        model=data.get("Model Name") or COMPONENT_MODEL,
        sw_version=data.get("Firmware Number") or __version__,
        name=ups_name,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PwrStatConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up pwrstat binary sensors based on a config entry."""
    coordinator = entry.runtime_data
    ups_name = entry.data[ATTR_UPS_NAME]
    ups_id = slugify(f"{DOMAIN} {ups_name}")

    entities: list[BinarySensorEntity] = [
        PwrStatBinarySensor(coordinator, ups_name, ups_id, description)
        for description in SENSORS
    ]

    async_add_entities(entities)


class PwrStatBinarySensor(CoordinatorEntity[PwrStatCoordinator], BinarySensorEntity):
    """Representation of a PwrStat binary sensor."""

    entity_description: PwrStatBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PwrStatCoordinator,
        ups_name: str,
        ups_id: str,
        description: PwrStatBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, context=ups_name)

        self.entity_description = description
        self._ups_id = ups_id
        self._ups_name = ups_name
        self._attr_unique_id = slugify(f"{ups_id} {self.entity_description.suffix}")
        self.entity_id = f"binary_sensor.{self._attr_unique_id}"
        self._attr_device_info = _build_device_info(coordinator, ups_id, ups_name)

        _LOGGER.debug(
            "PwrStatBinarySensor: created %s (%s)",
            self._attr_unique_id,
            description.name,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_device_info = _build_device_info(
            self.coordinator, self._ups_id, self._ups_name
        )
        super()._handle_coordinator_update()

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data or self.entity_description.key not in self.coordinator.data:
            return None

        raw_val = self.coordinator.data.get(self.entity_description.key)
        if self.entity_description.test:
            try:
                return self.entity_description.test(raw_val)
            except Exception:  # pylint: disable=broad-except
                return None
        return bool(raw_val)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.entity_description.key in self.coordinator.data
        )
