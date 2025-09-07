"""The eventsubscription integration."""

from __future__ import annotations
import logging

from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .coordinator import EventSubscriptionCoordinator

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

from .const import DOMAIN

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)

storage = None
coordinatorEntity = None


async def async_setup(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up RemoteNow from a config entry."""
    notify_entries = hass.config_entries.async_entries(domain="group")
    person_notify_entities = []

    for entry in notify_entries:
        if entry.source == "personnotify":
            person_notify_entities.append(entry)

    if len(person_notify_entities) == 0:
        _LOGGER.error(
            "Seems that ha-person-notify is not installed - ha-person-notify is a prerequisite"
        )
        return False

    global coordinatorEntity
    coordinatorEntity = EventSubscriptionCoordinator(hass=hass)

    if coordinatorEntity.data is None:
        coordinatorEntity.data = await coordinatorEntity._storage.async_load()

        if coordinatorEntity.data is None:
            coordinatorEntity.data = {}

    def handle_subscribe_specific(call):
        print(call)

    async def handle_subscribe_dynamic(call: ServiceCall):
        print(call.context.as_dict())
        print(call.data)

        event = call.data["targetEvent"].split(".")[1]
        _LOGGER.debug(f"Subscribing {call.context.user_id} to {event}")
        await coordinatorEntity.changeState(
            eventdata={
                "eventName": event,
                "action": "register",
                "userid": call.context.user_id,
                "deleteAfterCompletion": False,
                "message": "",
            }
        )

    hass.services.async_register(
        DOMAIN, "subscribe_specific", handle_subscribe_specific
    )
    hass.services.async_register(DOMAIN, "subscribe_dynamic", handle_subscribe_dynamic)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RemoteNow from a config entry."""

    entry.runtime_data = coordinatorEntity

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
