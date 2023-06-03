"""The eventsubscription integration."""
from __future__ import annotations
import logging
import json
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, ATTR_NAME, ATTR_DEFAULT_NAME
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    ATTR_EVENTNAME,
    ATTR_REGISTERMESSAGE,
    ATTR_COMPLETEMESSAGE,
    ATTR_TARGETPERSON,
    ATTR_TARGETTEXT,
    ATTR_DELETEAFTERCOMPLETION,
    ATTR_FLUSHREGISTRATION,
)

_LOGGER = logging.getLogger(__name__)

state = {}


def setup(hass, config):
    _LOGGER.info(f"The {__name__} component is ready!")

    def handle_register(call):
        """Handle the service call."""
        eventname = call.data.get(ATTR_EVENTNAME)
        registermessage = call.data.get(ATTR_REGISTERMESSAGE)
        completemessage = call.data.get(ATTR_COMPLETEMESSAGE)
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
                "deleteaftercompletion": deleteaftercompletion,
            }

            hass.bus.fire(
                "eventsubscription_register",
                {
                    "eventname": eventname,
                    "message": registermessage,
                    "targetuser": user,
                },
            )

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

    hass.services.register(DOMAIN, "complete", handle_complete)
    hass.services.register(DOMAIN, "register", handle_register)

    # Return boolean to indicate that initialization was successful.
    return True
