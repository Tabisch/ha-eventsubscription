from datetime import timedelta
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import *

_LOGGER = logging.getLogger(__name__)
# Time between updating data from GitHub
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            EventSubscriptionSensor(
                entry=entry, hass=hass, coordinator=entry.runtime_data
            )
        ],
        update_before_add=True,
    )


class EventSubscriptionSensor(SensorEntity, CoordinatorEntity):
    def __init__(
        self,
        entry: ConfigEntry,
        hass: HomeAssistant,
        coordinator: CoordinatorEntity,
    ) -> None:
        super().__init__(coordinator=coordinator)
        self._name = f"{entry.data[ATTR_EVENTNAME]}"
        self._attributename = entry.data[ATTR_EVENTNAME]

        self._available = True

        self._eventName = entry.data[ATTR_EVENTNAME]
        self._deleteAfterCompletion = entry.data[ATTR_DELETEAFTERCOMPLETION]

        self.attrs: Dict[str, Any] = {
            "last_update": "",
            "last_update_diff": "",
        }

        if self._eventName not in coordinator.data.keys():
            coordinator.data[self._eventName] = []

        self._state = len(coordinator.data[self._eventName])

        _LOGGER.debug(f"EventSubscriptionSensor - {self._name} created")

    @property
    def name(self) -> str:
        return self._name

    # Todo automatic names
    # @property
    # def displayname(self):
    #    return "text"

    @property
    def unique_id(self) -> str:
        return f"{self._name}"

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def available(self) -> str:
        return self._available

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._eventName)
            },
            "name": self._eventName,
            "manufacturer": DOMAIN,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug(
            f"EventSubscriptionSensor - {self._name} - {len(self.coordinator.data[self._name])}"
        )

        self._state = len(self.coordinator.data[self._name])

        self.async_write_ha_state()
