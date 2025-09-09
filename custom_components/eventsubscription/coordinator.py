"""Example integration using DataUpdateCoordinator."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from homeassistant.helpers.storage import Store

from .const import DOMAIN, PERSONNOTIFY_DOMAIN

_LOGGER = logging.getLogger(__name__)


class EventSubscriptionCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
            always_update=True,
        )

        self._storage = Store(hass, version=1, key=DOMAIN)
        self.data = None

        _LOGGER.debug("EventSubscriptionCoordinator created")

    async def changeState(
        self, eventdata, sendMessage: bool = True, customMessage: bool = False
    ):
        _LOGGER.debug("EventSubscriptionCoordinator change setting")

        event_entries = self.hass.config_entries.async_entries(domain=DOMAIN)
        deleteAfterCompletion = False

        entrydata = None

        for event_entry in event_entries:
            if (
                event_entry.domain == DOMAIN
                and event_entry.data["eventname"] == eventdata["eventName"]
            ):
                entrydata = event_entry.data
                break

        if entrydata == None:
            _LOGGER.debug("Eventsubscribtion entry not found")
            return

        deleteAfterCompletion = entrydata["deleteaftercompletion"]

        message = ""

        if customMessage:
            message = eventdata["message"]
        else:
            if eventdata["action"] != "reset":
                message = entrydata[f"{eventdata['action']}message"]

        # prepare set
        setdata = set()

        if eventdata["eventName"] in self.data.keys():
            setdata = set(self.data[eventdata["eventName"]])

        if eventdata["action"] == "complete":
            _LOGGER.debug(
                f"EventSubscriptionCoordinator complete {eventdata['eventName']}"
            )
            if sendMessage:
                await self.sendMessage(userids=list(setdata), message=message)

            if deleteAfterCompletion:
                setdata.clear()

        if eventdata["action"] == "reset":
            _LOGGER.debug(
                f"EventSubscriptionCoordinator reset {eventdata['eventName']}"
            )
            setdata.clear()

        # update set
        if eventdata["action"] == "register":
            _LOGGER.debug(
                f"EventSubscriptionCoordinator register {eventdata['eventName']}"
            )
            setdata.add(eventdata["userid"])

            if sendMessage:
                await self.sendMessage(userids=[eventdata["userid"]], message=message)

        if eventdata["action"] == "unregister":
            _LOGGER.debug(
                f"EventSubscriptionCoordinator unregister {eventdata['eventName']}"
            )
            if sendMessage:
                await self.sendMessage(userids=[eventdata["userid"]], message=message)

            setdata.discard(eventdata["userid"])

        # update data
        self.data[eventdata["eventName"]] = list(setdata)

        await self._storage.async_save(self.data)

        self.async_update_listeners()

    async def _async_update_data(self):
        _LOGGER.debug("EventSubscriptionCoordinator updating")

        return self.data

    async def sendMessage(self, userids, message):
        """asd"""
        notify_entries = self.hass.config_entries.async_entries(domain="group")
        person_notify_entities = []

        for entry in notify_entries:
            if entry.source == PERSONNOTIFY_DOMAIN:
                person_notify_entities.append(entry)

        for userid in userids:
            for entry in person_notify_entities:
                if entry.data["user_id"] == userid:
                    _LOGGER.debug(f"Notifiy user with user_id {userid}")

                    await self.hass.services.async_call(
                        domain="notify",
                        service="send_message",
                        target={
                            "entity_id": f"{entry.options['group_type']}.{entry.options['name']}"
                        },
                        service_data={"title": "", "message": message},
                    )
