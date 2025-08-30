import logging

from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import *

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            EventSubscriptionButton(
                entry=entry,
                action="register",
                coordinator=entry.runtime_data,
                message=entry.data["registermessage"],
            ),
            EventSubscriptionButton(
                entry=entry,
                action="unregister",
                coordinator=entry.runtime_data,
                message=entry.data["unregistermessage"],
            ),
            EventSubscriptionButton(
                entry=entry,
                action="complete",
                coordinator=entry.runtime_data,
                message=entry.data["completemessage"],
            ),
            EventSubscriptionButton(
                entry=entry,
                action="reset",
                coordinator=entry.runtime_data,
                message="",
            ),
        ],
        update_before_add=True,
    )


class EventSubscriptionButton(ButtonEntity, CoordinatorEntity):
    # Implement one of these methods.

    def __init__(
        self,
        entry: ConfigEntry,
        action: str,
        message: str,
        coordinator: CoordinatorEntity,
    ) -> None:
        super().__init__(coordinator=coordinator)
        self._name = f"{entry.data[ATTR_EVENTNAME]}_{action}"
        self._attributename = f"{entry.data[ATTR_EVENTNAME]}_{action}"
        self._entry_id = entry.entry_id

        self._available = True

        self._eventName = entry.data[ATTR_EVENTNAME]
        self._action = action
        self._actionMessage = message
        self._deleteAfterCompletion = entry.data[ATTR_DELETEAFTERCOMPLETION]

        self.attrs: Dict[str, Any] = {
            "last_update": "",
            "last_update_diff": "",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug(f"{self._eventName} {self._context.user_id}")

        await self.coordinator.changeState(
            eventdata={
                "eventName": self._eventName,
                "action": self._action,
                "userid": self._context.user_id,
                "deleteAfterCompletion": self._deleteAfterCompletion,
                "message": self._actionMessage,
            }
        )

        await self.coordinator.async_request_refresh()

    @property
    def unique_id(self) -> str:
        return self._name

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
