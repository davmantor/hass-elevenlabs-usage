"""Sensor platform for ElevenLabs Usage integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ElevenLabsUsageConfigEntry, ElevenLabsUsageCoordinator
from .const import DOMAIN, SENSOR_DEFINITIONS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ElevenLabsUsageConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ElevenLabs Usage sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        ElevenLabsUsageSensor(coordinator, entry, key, name, unit, icon)
        for key, name, unit, icon, _ in SENSOR_DEFINITIONS
    )


class ElevenLabsUsageSensor(CoordinatorEntity[ElevenLabsUsageCoordinator], SensorEntity):
    """A sensor for an ElevenLabs usage metric."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ElevenLabsUsageCoordinator,
        entry: ElevenLabsUsageConfigEntry,
        key: str,
        name: str,
        unit: str | None,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        if unit is not None:
            self._attr_state_class = SensorStateClass.MEASUREMENT

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ElevenLabs Usage",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        """Return True if the sensor value is available."""
        if self._key == "api_error":
            return True
        if not super().available:
            return False
        if self.coordinator.data is None:
            return False
        return self._key in self.coordinator.data

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self._key == "api_error":
            return 0 if self.coordinator.last_update_success else 1
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._key)
