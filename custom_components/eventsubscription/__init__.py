"""The eventsubscription integration."""

from __future__ import annotations
import logging

from hawhodid import WhoDid

from homeassistant.core import HomeAssistant, ServiceCall, Event
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import State
import asyncio

from .coordinator import EventSubscriptionCoordinator

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

from .const import DOMAIN, PERSONNOTIFY_DOMAIN

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

_LOGGER = logging.getLogger(__name__)

storage = None
coordinatorEntity = None


async def async_setup(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up eventsubscription from a config entry."""
    notify_entries = hass.config_entries.async_entries(domain="group")
    person_notify_entities = []

    for entry in notify_entries:
        if entry.source == PERSONNOTIFY_DOMAIN:
            person_notify_entities.append(entry)

    if len(person_notify_entities) == 0:
        _LOGGER.error(
            "Seems that ha-person-notify is not installed - ha-person-notify is a prerequisite"
        )
        return False

    WhoDid(hass=hass)

    global coordinatorEntity
    coordinatorEntity = EventSubscriptionCoordinator(hass=hass)

    if coordinatorEntity.data is None:
        coordinatorEntity.data = await coordinatorEntity._storage.async_load()

        if coordinatorEntity.data is None:
            coordinatorEntity.data = {}

    async def handle_specific(call: ServiceCall):
        event = call.data["targetEvent"].split(".")[1]
        personList = hass.states.async_entity_ids(domain_filter="person")
        personStateList = []

        message = ""

        if "customMessage" in call.data.keys():
            message = call.data["customMessage"]

        for person_id in personList:
            personStateList.append(hass.states.get(entity_id=person_id))

        for targetPerson in call.data["targetPerson"]:
            personName = targetPerson.split(".")[1]
            for personState in personStateList:
                if personName == personState.attributes["id"]:
                    _LOGGER.debug(
                        f"Subscribing {personState.attributes['user_id']} to {event}"
                    )
                    await coordinatorEntity.changeState(
                        eventdata={
                            "eventName": event,
                            "action": call.data["action"],
                            "userid": personState.attributes["user_id"],
                            "message": message,
                        },
                        sendMessage=not call.data["suppressMessage"],
                        customMessage=("customMessage" in call.data.keys()),
                    )

    async def handle_dynamic(call: ServiceCall):
        whodidInstance = WhoDid(hass=call.hass)

        userid = await whodidInstance.getUserId(context=call.context)

        if userid == None:
            return

        message = ""

        if "customMessage" in call.data.keys():
            message = call.data["customMessage"]

        event = call.data["targetEvent"].split(".")[1]
        _LOGGER.debug(f"Subscribing {userid} to {event}")
        await coordinatorEntity.changeState(
            eventdata={
                "eventName": event,
                "action": call.data["action"],
                "userid": userid,
                "message": message,
            },
            sendMessage=not call.data["suppressMessage"],
            customMessage=("customMessage" in call.data.keys()),
        )

    async def handle_reset(call: ServiceCall):
        event = call.data["targetEvent"].split(".")[1]
        _LOGGER.debug(f"Resetting {event}")
        await coordinatorEntity.changeState(
            eventdata={
                "eventName": event,
                "action": "reset",
                "userid": "",
                "message": "",
            }
        )

    async def handle_complete(call: ServiceCall):
        event = call.data["targetEvent"].split(".")[1]
        _LOGGER.debug(f"Completing {event}")

        message = ""

        if "customMessage" in call.data.keys():
            message = call.data["customMessage"]

        await coordinatorEntity.changeState(
            eventdata={
                "eventName": event,
                "action": "complete",
                "userid": "",
                "message": message,
            },
            customMessage=("customMessage" in call.data.keys()),
        )

    hass.services.async_register(DOMAIN, "user_specific", handle_specific)
    hass.services.async_register(DOMAIN, "user_dynamic", handle_dynamic)
    hass.services.async_register(DOMAIN, "reset", handle_reset)
    hass.services.async_register(DOMAIN, "complete", handle_complete)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up eventsubscription from a config entry."""

    entry.runtime_data = coordinatorEntity

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
