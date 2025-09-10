"""Config flow for the RemoteNow integration."""

from __future__ import annotations

import asyncio

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import *

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_EVENTNAME): str,
        vol.Required(ATTR_SUBSCRIBEMESSAGE): str,
        vol.Required(ATTR_COMPLETEMESSAGE): str,
        vol.Required(ATTR_UNSUBSCRIBEMESSAGE): str,
        vol.Required(ATTR_DELETEAFTERCOMPLETION): bool,
    }
)


class RemoteNowFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for eventsubscription."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[ATTR_EVENTNAME], data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
