"""Example integration using DataUpdateCoordinator."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from homeassistant.helpers.storage import Store

from .const import DOMAIN

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

    async def changeState(self, eventdata):
        _LOGGER.debug("EventSubscriptionCoordinator change setting")

        # prepare set
        setdata = set()

        if eventdata["eventName"] in self.data.keys():
            setdata = set(self.data[eventdata["eventName"]])

        if eventdata["action"] == "complete":
            """complete path"""
            _LOGGER.debug(
                f"EventSubscriptionCoordinator complete {eventdata['eventName']}"
            )
            await self.sendMessage(userids=list(setdata), message=eventdata["message"])

            if eventdata["deleteAfterCompletion"]:
                setdata.clear()

        if eventdata["action"] == "reset":
            """reset path"""
            _LOGGER.debug(
                f"EventSubscriptionCoordinator reset {eventdata['eventName']}"
            )
            setdata.clear()

        # update set
        if eventdata["action"] == "register":
            """register path"""
            _LOGGER.debug(
                f"EventSubscriptionCoordinator register {eventdata['eventName']}"
            )
            setdata.add(eventdata["userid"])

            await self.sendMessage(
                userids=[eventdata["userid"]], message=eventdata["message"]
            )

        if eventdata["action"] == "unregister":
            """unregister path"""
            _LOGGER.debug(
                f"EventSubscriptionCoordinator unregister {eventdata['eventName']}"
            )
            await self.sendMessage(
                userids=[eventdata["userid"]], message=eventdata["message"]
            )

            setdata.discard(eventdata["userid"])

        # update data
        self.data[eventdata["eventName"]] = list(setdata)

        await self._storage.async_save(self.data)

        self.async_update_listeners()

    async def _async_update_data(self):
        _LOGGER.debug("EventSubscriptionCoordinator updating")

        if self.data is None:
            self.data = await self._storage.async_load()
            _LOGGER.debug("EventSubscriptionCoordinator data loaded")

        return self.data

    async def sendMessage(self, userids, message):
        """asd"""
        notify_entries = self.hass.config_entries.async_entries(domain="group")
        person_notify_entities = []

        for entry in notify_entries:
            if entry.source == "ha-person-notify":
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
