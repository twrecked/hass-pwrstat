"""Support for Cyberpower pwrstat sensors."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging
import re
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util, slugify

from . import PwrStatConfigEntry, __version__
from .const import (
    ATTR_UPS_NAME,
    COMPONENT_MANUFACTURER,
    COMPONENT_MODEL,
    DOMAIN,
)
from .coordinator import PwrStatCoordinator

_LOGGER = logging.getLogger(__name__)


def _parse_first_int(value: Any) -> int | None:
    """Parse first integer from string."""
    if value is None:
        return None
    try:
        first_token = str(value).strip().split(" ")[0]
        return int(first_token)
    except (ValueError, IndexError):
        return None


def _parse_first_float(value: Any) -> float | None:
    """Parse first float from string."""
    if value is None:
        return None
    try:
        first_token = str(value).strip().split(" ")[0]
        return float(first_token)
    except (ValueError, IndexError):
        return None


def _parse_load_percent(value: Any) -> int | None:
    """Extract percentage from Load string like '86 Watt(23 %)'."""
    if value is None:
        return None
    match = re.search(r"\((\d+)\s*%\)", str(value))
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


@dataclass(frozen=True, kw_only=True)
class PwrStatSensorDescription(SensorEntityDescription):
    """Describes a PwrStat sensor entity."""

    suffix: str = "unknown"
    convert: Callable[[Any], Any] | None = None
    extra_attributes: dict[str, Any] | None = None


SENSORS: list[PwrStatSensorDescription] = [
    PwrStatSensorDescription(
        key="Load",
        name="Load",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        suffix="Load",
        convert=_parse_first_int,
    ),
    PwrStatSensorDescription(
        key="Load Percent",
        name="Load Percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        suffix="Load Percent",
        convert=_parse_load_percent,
    ),
    PwrStatSensorDescription(
        key="Battery Capacity",
        name="Battery Capacity",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        suffix="Battery Capacity",
        convert=_parse_first_int,
    ),
    PwrStatSensorDescription(
        key="Output Voltage",
        name="Output Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        suffix="Output Voltage",
        convert=_parse_first_float,
    ),
    PwrStatSensorDescription(
        key="Utility Voltage",
        name="Utility Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        suffix="Utility Voltage",
        convert=_parse_first_float,
    ),
    PwrStatSensorDescription(
        key="Remaining Runtime",
        name="Remaining Runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        suffix="Remaining Runtime",
        convert=_parse_first_int,
    ),
    PwrStatSensorDescription(
        key="State",
        name="State",
        device_class=SensorDeviceClass.ENUM,
        options=[
            "normal",
            "power failure",
        ],
        suffix="State",
        extra_attributes={
            "Power Supply by": "",
            "Firmware Number": "",
            "Model Name": "",
            "Rating Power": "",
            "Rating Voltage": "",
            "Last Power Event": "",
            "Test Result": "",
            "Line Interaction": "",
        },
        convert=lambda v: str(v).lower() if v is not None else None,
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
    """Set up pwrstat sensors based on a config entry."""
    coordinator = entry.runtime_data
    ups_name = entry.data[ATTR_UPS_NAME]
    ups_id = slugify(f"{DOMAIN} {ups_name}")

    entities: list[SensorEntity] = [
        PwrStatSensor(coordinator, ups_name, ups_id, description)
        for description in SENSORS
    ]

    # Add native continuous energy sensor (kWh)
    entities.append(PwrStatEnergySensor(coordinator, ups_name, ups_id))

    async_add_entities(entities)


class PwrStatSensor(CoordinatorEntity[PwrStatCoordinator], SensorEntity):
    """Representation of a PwrStat sensor."""

    entity_description: PwrStatSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PwrStatCoordinator,
        ups_name: str,
        ups_id: str,
        description: PwrStatSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, context=ups_name)

        self.entity_description = description
        self._ups_id = ups_id
        self._ups_name = ups_name
        self._attr_unique_id = slugify(f"{ups_id} {self.entity_description.suffix}")
        self.entity_id = f"sensor.{self._attr_unique_id}"
        self._attr_device_info = _build_device_info(coordinator, ups_id, ups_name)

        _LOGGER.debug("PwrStatSensor: created %s (%s)", self._attr_unique_id, description.name)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_device_info = _build_device_info(
            self.coordinator, self._ups_id, self._ups_name
        )
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        # For "Load Percent", we read from the "Load" key in coordinator data
        lookup_key = "Load" if self.entity_description.key == "Load Percent" else self.entity_description.key

        raw_val = self.coordinator.data.get(lookup_key)
        if raw_val is None:
            return None

        if self.entity_description.convert:
            try:
                return self.entity_description.convert(raw_val)
            except Exception:  # pylint: disable=broad-except
                return None
        return raw_val

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        lookup_key = "Load" if self.entity_description.key == "Load Percent" else self.entity_description.key
        return (
            super().available
            and self.coordinator.data is not None
            and lookup_key in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if not self.entity_description.extra_attributes or not self.coordinator.data:
            return None

        return {
            attribute: self.coordinator.data.get(attribute, "not available")
            for attribute in self.entity_description.extra_attributes
        }


class PwrStatEnergySensor(CoordinatorEntity[PwrStatCoordinator], RestoreEntity, SensorEntity):
    """Calculates continuous cumulative energy (kWh) from UPS Load (Watts)."""

    _attr_has_entity_name = True
    _attr_name = "Energy"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 3

    def __init__(
        self,
        coordinator: PwrStatCoordinator,
        ups_name: str,
        ups_id: str,
    ) -> None:
        """Initialize the energy sensor."""
        super().__init__(coordinator, context=ups_name)

        self._ups_id = ups_id
        self._ups_name = ups_name
        self._attr_unique_id = slugify(f"{ups_id} Energy")
        self.entity_id = f"sensor.{self._attr_unique_id}"
        self._attr_device_info = _build_device_info(coordinator, ups_id, ups_name)

        self._energy_accumulator: float = 0.0
        self._last_calc_time: datetime | None = None
        self._last_power: float | None = None

    async def async_added_to_hass(self) -> None:
        """Restore state on startup."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._energy_accumulator = float(last_state.state)
                self._attr_native_value = round(self._energy_accumulator, 4)
                _LOGGER.debug(
                    "%s: restored energy state: %.4f kWh",
                    self.entity_id,
                    self._energy_accumulator,
                )
            except (ValueError, TypeError):
                self._energy_accumulator = 0.0
        else:
            self._energy_accumulator = 0.0

        self._last_calc_time = dt_util.utcnow()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data and integrate power into energy."""
        self._attr_device_info = _build_device_info(
            self.coordinator, self._ups_id, self._ups_name
        )

        now = dt_util.utcnow()

        if self.coordinator.data and "Load" in self.coordinator.data:
            current_watts = _parse_first_float(self.coordinator.data["Load"])
            if current_watts is not None and self._last_calc_time is not None:
                elapsed_seconds = (now - self._last_calc_time).total_seconds()
                # Protect against negative time or huge jumps after prolonged downtime (>1 hour)
                if 0 < elapsed_seconds <= 3600:
                    power_watts = self._last_power if self._last_power is not None else current_watts
                    added_kwh = (power_watts * elapsed_seconds) / 3_600_000.0
                    self._energy_accumulator += max(0.0, added_kwh)
                    self._attr_native_value = round(self._energy_accumulator, 4)

                self._last_power = current_watts
            elif current_watts is not None:
                self._last_power = current_watts

        self._last_calc_time = now
        self.async_write_ha_state()

    @property
    def native_value(self) -> float:
        """Return the cumulative energy in kWh."""
        return round(self._energy_accumulator, 4)

    @property
    def available(self) -> bool:
        """Return True if coordinator is available."""
        return super().available and self.coordinator.data is not None and "Load" in self.coordinator.data
