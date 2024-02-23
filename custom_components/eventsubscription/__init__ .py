"""The eventsubscription integration."""
from __future__ import annotations
import logging

import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    ATTR_EVENTNAME,
    ATTR_REGISTERMESSAGE,
    ATTR_COMPLETEMESSAGE,
    ATTR_TARGETPERSON,
    ATTR_TARGETTEXT,
    ATTR_DELETEAFTERCOMPLETION,
    ATTR_FLUSHREGISTRATION,
    ATTR_UNREGISTERMESSAGE,
)

_LOGGER = logging.getLogger(__name__)

state = {}
storage = None

@asyncio.coroutine
def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    _LOGGER.info(f"The {__name__} component is ready!")

    storage = Store(hass, version=1, key=DOMAIN)

    state = storage.async_load()

    def handle_register(call):
        """Handle the service call."""
        eventname = call.data.get(ATTR_EVENTNAME)
        registermessage = call.data.get(ATTR_REGISTERMESSAGE)
        completemessage = call.data.get(ATTR_COMPLETEMESSAGE)
        unregistermessage = call.data.get(ATTR_UNREGISTERMESSAGE)
        targetperson = call.data.get(ATTR_TARGETPERSON)
        targettext = call.data.get(ATTR_TARGETTEXT)

        deleteaftercompletion = call.data.get(ATTR_DELETEAFTERCOMPLETION)

        users = []

        if targetperson is not None:
            if type(targetperson) == list:
                for person in targetperson:
                    users.append(f"{person.replace('person.', '')}")
            else:
                users.append(f"{targetperson.replace('person.', '')}")

        if targettext is not None:
            if type(targettext) == list:
                for target in targettext:
                    users.append(f"{target}")
            else:
                users.append(f"{targettext}")

        for user in users:
            if eventname not in state.keys():
                state[eventname] = {}

            state[eventname][user] = {
                "registermessage": registermessage,
                "completemessage": completemessage,
                "unregistermessage": unregistermessage,
                "deleteaftercompletion": deleteaftercompletion,
            }

            if registermessage is not None:
                hass.bus.fire(
                    "eventsubscription_register",
                    {
                        "eventname": eventname,
                        "message": registermessage,
                        "targetuser": user,
                    },
                )

        storage.async_save(state)

    def handle_complete(call):
        """Handle the service call."""
        eventname = call.data.get(ATTR_EVENTNAME)
        flushregistration = call.data.get(ATTR_FLUSHREGISTRATION)

        if eventname not in state.keys():
            return

        users = list(state[eventname].keys())

        for user in users:
            hass.bus.fire(
                "eventsubscription_complete",
                {
                    "eventname": eventname,
                    "message": state[eventname][user]["completemessage"],
                    "targetuser": user,
                },
            )

            if state[eventname][user]["deleteaftercompletion"]:
                del state[eventname][user]

        if flushregistration:
            del state[eventname]

        storage.async_save(state)
        

    def handle_unregister(call):
        """Handle the service call."""
        eventname = call.data.get(ATTR_EVENTNAME)
        targetperson = call.data.get(ATTR_TARGETPERSON)
        targettext = call.data.get(ATTR_TARGETTEXT)

        users = []

        if targetperson is not None:
            if type(targetperson) == list:
                for person in targetperson:
                    users.append(f"{person.replace('person.', '')}")
            else:
                users.append(f"{targetperson.replace('person.', '')}")

        if targettext is not None:
            if type(targettext) == list:
                for target in targettext:
                    users.append(f"{target}")
            else:
                users.append(f"{targettext}")

        for user in users:
            if eventname not in state.keys():
                state[eventname] = {}

            registeredusers = list(state[eventname].keys())

            if user in registeredusers:
                hass.bus.fire(
                    "eventsubscription_unregister",
                    {
                        "eventname": eventname,
                        "message": state[eventname][user]["unregistermessage"],
                        "targetuser": user,
                    },
                )

                del state[eventname][user]

        storage.async_save(state)

    def handle_reset(call):
        """Reset all notifications."""
        state = {}

        hass.bus.fire(
            "eventsubscription_reset"
        )

        storage.async_save(state)

    hass.services.register(DOMAIN, "complete", handle_complete)
    hass.services.register(DOMAIN, "register", handle_register)
    hass.services.register(DOMAIN, "unregister", handle_unregister)
    hass.services.register(DOMAIN, "reset", handle_reset)

    return True