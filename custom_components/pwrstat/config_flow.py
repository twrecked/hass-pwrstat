"""Config flow for pwrstat integration."""

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import slugify

from .const import (
    ATTR_UPS_NAME,
    ATTR_UPS_POLL_EVERY,
    ATTR_UPS_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_UPS_NAME,
    DEFAULT_UPS_POLL_EVERY,
    DEFAULT_UPS_URL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass, user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate that the pwrstat-api URL can be reached and returns valid data."""
    url = user_input[ATTR_UPS_URL]
    session = async_get_clientsession(hass)
    try:
        async with asyncio.timeout(DEFAULT_TIMEOUT):
            response = await session.get(url)
            if response.status != 200:
                raise CannotConnect(f"HTTP status {response.status}")
            data = await response.json()
            if not isinstance(data, dict):
                raise InvalidResponse("Response is not a valid JSON dictionary")
    except (TimeoutError, aiohttp.ClientError) as err:
        _LOGGER.error("Cannot connect to pwrstat-api at %s: %s", url, err)
        raise CannotConnect from err
    except (ValueError, TypeError) as err:
        _LOGGER.error("Invalid response from pwrstat-api at %s: %s", url, err)
        raise InvalidResponse from err

    return {"title": user_input[ATTR_UPS_NAME]}


class PwrStatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for pwrstat."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            ups_id = slugify(f"{DOMAIN} {user_input[ATTR_UPS_NAME]}")
            await self.async_set_unique_id(ups_id)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidResponse:
                errors["base"] = "invalid_response"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during configuration")
                errors["base"] = "unknown"

        if user_input is None:
            user_input = {
                ATTR_UPS_NAME: DEFAULT_UPS_NAME,
                ATTR_UPS_URL: DEFAULT_UPS_URL,
                ATTR_UPS_POLL_EVERY: DEFAULT_UPS_POLL_EVERY,
            }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        ATTR_UPS_NAME, default=user_input.get(ATTR_UPS_NAME, DEFAULT_UPS_NAME)
                    ): str,
                    vol.Required(
                        ATTR_UPS_URL, default=user_input.get(ATTR_UPS_URL, DEFAULT_UPS_URL)
                    ): str,
                    vol.Required(
                        ATTR_UPS_POLL_EVERY,
                        default=user_input.get(ATTR_UPS_POLL_EVERY, DEFAULT_UPS_POLL_EVERY),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return PwrStatOptionsFlowHandler(config_entry)


class PwrStatOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for pwrstat."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            test_input = {
                ATTR_UPS_NAME: self._config_entry.data[ATTR_UPS_NAME],
                ATTR_UPS_URL: user_input[ATTR_UPS_URL],
                ATTR_UPS_POLL_EVERY: user_input[ATTR_UPS_POLL_EVERY],
            }
            try:
                await validate_input(self.hass, test_input)
                return self.async_create_entry(title="", data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidResponse:
                errors["base"] = "invalid_response"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception updating options")
                errors["base"] = "unknown"

        current_url = self._config_entry.options.get(
            ATTR_UPS_URL, self._config_entry.data.get(ATTR_UPS_URL, DEFAULT_UPS_URL)
        )
        current_poll = self._config_entry.options.get(
            ATTR_UPS_POLL_EVERY,
            self._config_entry.data.get(ATTR_UPS_POLL_EVERY, DEFAULT_UPS_POLL_EVERY),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(ATTR_UPS_URL, default=current_url): str,
                    vol.Required(ATTR_UPS_POLL_EVERY, default=current_poll): vol.All(
                        vol.Coerce(int), vol.Range(min=5, max=3600)
                    ),
                }
            ),
            errors=errors,
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error indicating connection failure."""


class InvalidResponse(exceptions.HomeAssistantError):
    """Error indicating invalid response from API."""


class UPSNameAlreadyUsed(exceptions.HomeAssistantError):
    """Error indicating UPS name already used."""
