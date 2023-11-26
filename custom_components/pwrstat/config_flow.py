"""
This component provides support for pwrstat-api, a REST API wrapping
Cyberpower's pwrstat command.

"""

import logging
import voluptuous as vol
from typing import Any

from homeassistant import config_entries, exceptions
from homeassistant.data_entry_flow import FlowResult

from .const import *


_LOGGER = logging.getLogger(__name__)


class PwrStatConfigFlow(config_entries.ConfigFlow, domain=COMPONENT_DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:

        errors = {}

        if user_input is not None:
            return self.async_create_entry(title=user_input[ATTR_UPS_NAME], data={
                ATTR_UPS_NAME: user_input[ATTR_UPS_NAME],
                ATTR_UPS_URL: user_input[ATTR_UPS_URL],
                ATTR_UPS_POLL_EVERY: user_input[ATTR_UPS_POLL_EVERY],
            })

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


class UPSURLAlreadyUsed(exceptions.HomeAssistantError):
    """ Error indicating group name already used. """
