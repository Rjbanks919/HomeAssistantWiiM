"""Config flow for WiiM integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.wiim.pywiim import CannotConnectError, Wiim
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DATA_INFO, DATA_WIIM

_LOGGER = logging.getLogger(__name__)

# Setup only requires the IP address of the WiiM device
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
    }
)


async def validate_input(hass: HomeAssistant, host: str):
    """Validate the user input allows us to connect."""

    _LOGGER.info("About to set up a proper class bro")

    # Get a connection chugging
    wiim = Wiim(host, async_get_clientsession(hass))

    _LOGGER.info("Ok we have a class, time for the connection attempt")

    try:
        return await wiim.get_device_information()
    except CannotConnectError as error:
        _LOGGER.error("Yeah that shit failed")
        raise CannotConnect from error


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WiiM."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._host: str | None = None
        self._name: str | None = None
        self._uuid: str | None = None

    async def _set_uid_and_abort(self):
        await self.async_set_unique_id(self._uuid)
        self._abort_if_unique_id_configured(
            updates={
                CONF_HOST: self._host,
            }
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            info = None
            self._host = user_input[CONF_HOST]
            try:
                info = await validate_input(self.hass, self._host)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if info is not None:
                self._name = info.get("name", self._host)
                self._uuid = info.get("id")
                if self._uuid is not None:
                    await self._set_uid_and_abort()

            return self.async_create_entry(
                title=self._name,
                data={
                    CONF_NAME: self._name,
                    CONF_HOST: self._host,
                    CONF_ID: self._uuid,
                },
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
