"""
This component provides support for pwrstat-api, a REST API wrapping
Cyberpower's pwrstat command.

"""

import logging
import voluptuous as vol
from typing import Any

from homeassistant import (
    config_entries,
    exceptions
)
from homeassistant.data_entry_flow import FlowResult

from .const import *


_LOGGER = logging.getLogger(__name__)


class PwrStatConfigFlow(config_entries.ConfigFlow, domain=COMPONENT_DOMAIN):

    VERSION = 1

    async def validate_input(self, user_input):
        for ups_name, values in self.hass.data.get(COMPONENT_DOMAIN, {}).items():
            _LOGGER.debug(f"checking {ups_name}")
            if ups_name == user_input[ATTR_UPS_NAME]:
                raise UPSNameAlreadyUsed

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:

        errors = {}
        try:
            if user_input is not None:
                await self.validate_input(user_input)
                return self.async_create_entry(title=user_input[ATTR_UPS_NAME], data={
                    ATTR_UPS_NAME: user_input[ATTR_UPS_NAME],
                    ATTR_UPS_URL: user_input[ATTR_UPS_URL],
                    ATTR_UPS_POLL_EVERY: user_input[ATTR_UPS_POLL_EVERY],
                })
        except UPSNameAlreadyUsed as _e:
            errors["base"] = "name_used"

        # Fill in defaults if we have nothing.
        if user_input is None:
            user_input = {
                ATTR_UPS_NAME: DEFAULT_UPS_NAME,
                ATTR_UPS_URL: DEFAULT_UPS_URL,
                ATTR_UPS_POLL_EVERY: DEFAULT_UPS_POLL_EVERY
            }

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({
                vol.Required(ATTR_UPS_NAME, default=user_input[ATTR_UPS_NAME]): str,
                vol.Required(ATTR_UPS_URL, default=user_input[ATTR_UPS_URL]): str,
                vol.Required(ATTR_UPS_POLL_EVERY, default=user_input[ATTR_UPS_POLL_EVERY]): int,
            }),
            errors=errors
        )


class UPSNameAlreadyUsed(exceptions.HomeAssistantError):
    """ Error indicating group name already used. """
